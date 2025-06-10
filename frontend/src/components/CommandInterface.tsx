import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Mic, Send, Volume2 } from 'lucide-react';
import { MicVAD } from '@ricky0123/vad-web';
import { usePorcupine } from '@picovoice/porcupine-react'; // Import the hook

// Import the Porcupine model parameters from your porcupine_params.js file
import { porcupineModel } from './porcupine_params'; // Make sure the path is correct
import { HeyAssistantKeywordModel } from './hey_assistant'; // Make sure the path is correct

interface CommandInterfaceProps {
  translations: { placeholder: string; listening: string };
  onCommand: (command: string) => void;
  response: string;
  isLoading: boolean;
}

type AssistantStatus =
  | 'idle'
  | 'initializing'
  | 'listeningForCommand'
  | 'processing'
  | 'playingResponse'
  | 'error'
  | 'voiceDisabled';

export const CommandInterface: React.FC<CommandInterfaceProps> = ({
  translations,
  onCommand,
  response,
  isLoading,
}) => {
  const [command, setCommand] = useState('');
  const [assistantStatus, setAssistantStatus] = useState<AssistantStatus>('idle');
  const [volume, setVolume] = useState(0);
  const vadRef = useRef<MicVAD | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null); // Corrected initialization
  const animationFrameRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [showCircles, setShowCircles] = useState(false); // New state for showing circles

  // Porcupine setup
  const {
    keywordDetection,
    isLoaded,
    isListening,
    error,
    init: porcupineInit,
    start: porcupineStart,
    stop: porcupineStop,
    release: porcupineRelease,
  } = usePorcupine();

  useEffect(() => {
    const init = async () => {
      try {
        // Initialize VAD first to get the stream
        const vad = await MicVAD.new({
          onSpeechStart: () => setAssistantStatus('listeningForCommand'),
          onSpeechEnd: () => setAssistantStatus('idle'),
          startOnLoad: true, // Automatically start listening for speech
        });
        vadRef.current = vad;
        startVisualizer(vad.stream);
        streamRef.current = vad.stream;

        // Initialize Porcupine with your Access Key, keyword, and model
        await porcupineInit(
          'YOUR_ACCESS_KEY', // <-- Very important: Replace with your actual Picovoice Access Key!
          { base64: HeyAssistantKeywordModel, label: 'Hey Assistant' }, // Your keyword data (label should match your keyword)
          { base64: porcupineModel } // Your Porcupine model data
        );
        await porcupineStart(); // Start Porcupine after successful initialization

      } catch (error) {
        console.error("❌ Error initializing VAD or Porcupine:", error);
        setAssistantStatus('error');
      }
    };

    init();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      vadRef.current?.pause();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      porcupineRelease(); // Release Porcupine resources when component unmounts
    };
  }, []); // Empty dependency array means this effect runs once on mount

  // Effect to handle keyword detection
  useEffect(() => {
     if (keywordDetection !== null) {
       console.log('Keyword Detected:', keywordDetection.label);
       setShowCircles(true); // Show circles when keyword is detected
       // Hide circles after a short duration (e.g., 2 seconds)
       setTimeout(() => setShowCircles(false), 2000);
     }
   }, [keywordDetection]); // Rerun this effect when keywordDetection changes

  const startVisualizer = (stream: MediaStream) => {
    const ctx = new AudioContext();
    const src = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    src.connect(analyser);
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const loop = () => {
      analyser.getByteTimeDomainData(dataArray);
      const rms = Math.sqrt(dataArray.reduce((sum, val) => sum + (val - 128) ** 2, 0) / dataArray.length);
      setVolume(rms * 2); // Scale volume for effect
      animationFrameRef.current = requestAnimationFrame(loop);
    };
    loop();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim()) {
      onCommand(command);
      setCommand('');
    }
  };

  const handlePlayAssistantResponse = async () => {
    if (!response) return;
    setAssistantStatus('playingResponse');
    try {
      const res = await fetch('http://localhost:8000/send-command/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: response, response_type: 'voice' }),
      });
      const audioArrayBuffer = await res.arrayBuffer();
      const ctx = new AudioContext();
      const buffer = await ctx.decodeAudioData(audioArrayBuffer);
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      source.start();
      await new Promise<void>((resolve) => {
        source.onended = () => resolve();
      });
    } catch (error) {
      console.error('Error playing response:', error);
    } finally {
      setAssistantStatus('idle');
    }
  };

  const getMicButton = () => {
    return (
      <div className="relative w-28 h-28 flex items-center justify-center">
        <div className="absolute inset-0 flex items-center justify-center z-0">
          {/* Pass showCircles prop to conditionally render circles */}
          <VoiceVisualizer volume={volume} showCircles={showCircles} />
        </div>
        <Button
          type="button"
          disabled
          className="z-10 h-16 w-16 rounded-full bg-gray-500"
        >
          <Mic className="w-6 h-6 text-white" />
        </Button>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Card className="p-6 bg-white/80 backdrop-blur-sm border-0 shadow-lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-3">
            <Input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder={translations.placeholder}
              className="h-14 text-lg border-2 border-gray-200 focus:border-blue-400 rounded-xl bg-white/90"
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="lg"
              className="h-14 px-6 bg-blue-600 hover:bg-blue-700 rounded-xl"
              disabled={isLoading}
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
          <div className="flex justify-center pt-4">{getMicButton()}</div>
        </form>
      </Card>

      {response && (
        <Card className="p-6 bg-gradient-to-r from-green-50 to-blue-50 border-0 shadow-lg animate-fade-in">
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-800 mb-2">Assistant Response:</h3>
              <p className="text-gray-700 leading-relaxed">{response}</p>
            </div>
            <Button
              onClick={handlePlayAssistantResponse}
              variant="outline"
              size="sm"
              className="bg-white/80 hover:bg-white border-gray-300"
              disabled={assistantStatus === 'playingResponse'}
            >
              <Volume2 className="w-4 h-4" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};

// 🎨 Visualizer Component
const VoiceVisualizer: React.FC<{ volume: number; showCircles: boolean }> = ({ volume, showCircles }) => {
  const scales = [1.0, 1.5, 2.0].map((base) => base + volume / 40);

  return (
    <div className="relative flex items-center justify-center">
      {/* Conditionally render circles based on showCircles prop */}
      {showCircles &&
        scales.map((scale, i) => (
          <div
            key={i}
            className="absolute rounded-full border-2 border-blue-400 transition-all duration-100 ease-out"
            style={{
              width: `${scale * 40}px`,
              height: `${scale * 40}px`,
              opacity: 0.3 + i * 0.2,
            }}
          />
        ))}
    </div>
  );
};