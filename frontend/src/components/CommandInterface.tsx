import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Mic, Send, Volume2 } from 'lucide-react';
import { PorcupineWorker } from '@picovoice/porcupine-web';
import { MicVAD } from '@ricky0123/vad-web';

interface CommandInterfaceProps {
  translations: { placeholder: string; listening: string; };
  onCommand: (command: string) => void; // This will trigger text command handling in parent
  response: string; // Assistant's text response
  isLoading: boolean; // From parent for overall processing
}

type AssistantStatus = 'idle' | 'initializing' | 'listeningForWakeWord' | 'listeningForCommand' | 'processing' | 'error' | 'playingResponse';

export const CommandInterface: React.FC<CommandInterfaceProps> = ({
  translations,
  onCommand,
  response,
  isLoading,
}) => {
  const [command, setCommand] = useState('');
  const [assistantStatus, setAssistantStatus] = useState<AssistantStatus>('initializing');
  
  const porcupineWorkerRef = useRef<PorcupineWorker | null>(null);
  const vadRef = useRef<MicVAD | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioSourceRef = useRef<AudioBufferSourceNode | null>(null);

  useEffect(() => {
    // Initialize AudioContext
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    const initVoiceEngine = async () => {
      try {
        if (porcupineWorkerRef.current) {
          porcupineWorkerRef.current.release();
          porcupineWorkerRef.current = null;
        }

        porcupineWorkerRef.current = await PorcupineWorker.create(
          'KjFJIHycu/LCghU3SFVYv1XzoC/KSW6mDxQWBmc4K8I+ktk6hKL6Mw==', // <-- Place your Picovoice AccessKey here
          {
            publicPath: '/hey_assistant.ppn', // <-- Your model file name in the public folder
            sensitivity: 0.7,
          },
          (keywordDetection) => {
            console.log(`Wake word detected: ${keywordDetection.label}`);
            porcupineWorkerRef.current?.pause();
            startVAD();
          }
        );
        console.log("Porcupine initialized. Starting wake word listening.");
        startListeningForWakeWord();
      } catch (error) {
        console.error('Failed to initialize Porcupine:', error);
        setAssistantStatus('error');
      }
    };

    initVoiceEngine();

    return () => {
      porcupineWorkerRef.current?.release();
      vadRef.current?.destroy();
      audioSourceRef.current?.stop();
      audioContextRef.current?.close();
      console.log("Voice engines released.");
    };
  }, []);

  const startListeningForWakeWord = () => {
    setAssistantStatus('listeningForWakeWord');
    porcupineWorkerRef.current?.start();
  };
  
  const startVAD = async () => {
    setAssistantStatus('listeningForCommand');
    try {
      if (vadRef.current) {
        vadRef.current.destroy();
      }
      vadRef.current = await MicVAD.new({
        onSpeechEnd: async (audio) => {
          setAssistantStatus('processing');
          vadRef.current?.destroy();
          console.log("Speech ended, transcribing audio...");
          const audioBlob = new Blob([audio], { type: 'audio/wav' });
          await transcribeAudio(audioBlob);
        },
        onVADMisfire: () => {
          console.log("VAD misfire, restarting wake word listener.");
          startListeningForWakeWord();
        },
        stopOnAbsence: true,
      });
      vadRef.current.start();
    } catch (error) {
      console.error("VAD initialization failed:", error);
      setAssistantStatus('error');
      setTimeout(() => startListeningForWakeWord(), 2000);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'command.wav');
    formData.append('response_type', 'voice'); // Request voice response from backend

    try {
      const res = await fetch('http://localhost:8000/upload-audio/', {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      // If response is audio, play it directly
      if (res.headers.get('Content-Type')?.includes('audio')) {
        setAssistantStatus('playingResponse');
        const audioArrayBuffer = await res.arrayBuffer();
        await playAudio(audioArrayBuffer);
        // After audio plays, go back to listening for wake word
        startListeningForWakeWord();
      } else {
        // Otherwise, assume it's JSON with transcribed command and scheduled tasks
        const { command: transcribedText, scheduled_tasks } = await res.json();
        console.log("Transcribed text:", transcribedText);
        console.log("Scheduled tasks:", scheduled_tasks);

        if (transcribedText) {
          setCommand(transcribedText);
          onCommand(transcribedText); // Pass the transcribed text to the parent component's handler
        } else {
          onCommand(translations.placeholder);
        }
        startListeningForWakeWord(); // Listen for wake word after processing text response
      }
    } catch (error) {
      console.error('Transcription/TTS request failed:', error);
      onCommand(translations.placeholder);
      setAssistantStatus('error');
      setTimeout(() => startListeningForWakeWord(), 2000);
    }
  };

  const playAudio = async (audioArrayBuffer: ArrayBuffer) => {
    if (!audioContextRef.current) return;
    try {
      const audioBuffer = await audioContextRef.current.decodeAudioData(audioArrayBuffer);
      audioSourceRef.current = audioContextRef.current.createBufferSource();
      audioSourceRef.current.buffer = audioBuffer;
      audioSourceRef.current.connect(audioContextRef.current.destination);
      audioSourceRef.current.start(0);

      return new Promise<void>((resolve) => {
        audioSourceRef.current!.onended = () => {
          console.log("Audio playback ended.");
          resolve();
        };
      });
    } catch (error) {
      console.error("Error playing audio:", error);
    }
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim()) {
      onCommand(command);
      setCommand('');
    }
  };

  const getMicButton = () => {
    const statusMap = {
      idle: { text: "Initializing...", className: "bg-gray-400", disabled: true },
      initializing: { text: "Initializing voice engine...", className: "bg-gray-400 animate-pulse", disabled: true },
      listeningForWakeWord: { text: "Say 'Hey Assistant'", className: "bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 hover:scale-110", disabled: false },
      listeningForCommand: { text: translations.listening, className: "bg-red-500 hover:bg-red-600 animate-pulse", disabled: true },
      processing: { text: "Processing...", className: "bg-yellow-500 hover:bg-yellow-600 animate-pulse", disabled: true },
      playingResponse: { text: "Playing response...", className: "bg-green-500 animate-pulse", disabled: true },
      error: { text: "Error! Please refresh.", className: "bg-gray-700", disabled: true },
    };
    const currentStatus = statusMap[assistantStatus];

    return (
      <div className="text-center">
        <Button
            type="button"
            // Only allow manual re-start if idle/wake word listener failed
            onClick={assistantStatus === 'listeningForWakeWord' ? () => porcupineWorkerRef.current?.start() : undefined}
            disabled={currentStatus.disabled || isLoading} // Disable if overall assistant is busy
            className={`h-16 w-16 rounded-full transition-all duration-300 ${currentStatus.className}`}
        >
          <Mic className="w-6 h-6 text-white" />
        </Button>
        <p className="mt-4 text-sm text-gray-600 font-medium">{currentStatus.text}</p>
      </div>
    );
  };

  const handlePlayAssistantResponse = async () => {
    // This button will play the *text* response from the assistant, if any
    if (response) {
      setAssistantStatus('playingResponse');
      try {
        const ttsResponse = await fetch('http://localhost:8000/send-command/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: response, response_type: "voice" }), // Use response as command for TTS
        });

        if (!ttsResponse.ok) {
          throw new Error(`HTTP error! status: ${ttsResponse.status}`);
        }

        const audioArrayBuffer = await ttsResponse.arrayBuffer();
        await playAudio(audioArrayBuffer);
      } catch (error) {
        console.error("Error playing assistant response:", error);
      } finally {
        startListeningForWakeWord(); // Go back to listening after playing
      }
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6 bg-white/80 backdrop-blur-sm border-0 shadow-lg">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex gap-3">
            <Input
              value={command} onChange={(e) => setCommand(e.target.value)}
              placeholder={translations.placeholder}
              className="h-14 text-lg border-2 border-gray-200 focus:border-blue-400 rounded-xl bg-white/90"
              disabled={isLoading} // Disable input if overall assistant is busy
            />
            <Button type="submit" size="lg" className="h-14 px-6 bg-blue-600 hover:bg-blue-700 rounded-xl" disabled={isLoading}>
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