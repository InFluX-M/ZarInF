// src/components/CommandInterface.tsx

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Mic, Send, Volume2 } from 'lucide-react';
import { PorcupineWorker } from '@picovoice/porcupine-web'; // Keep import
import { MicVAD } from '@ricky0123/vad-web'; // Keep import

interface CommandInterfaceProps {
  translations: { placeholder: string; listening: string; };
  onCommand: (command: string) => void;
  response: string;
  isLoading: boolean;
}

type AssistantStatus = 'idle' | 'initializing' | 'listeningForWakeWord' | 'listeningForCommand' | 'processing' | 'error' | 'playingResponse' | 'voiceDisabled'; // Keep type

export const CommandInterface: React.FC<CommandInterfaceProps> = ({
  translations,
  onCommand,
  response,
  isLoading,
}) => {
  const [command, setCommand] = useState('');
  const [assistantStatus, setAssistantStatus] = useState<AssistantStatus>('voiceDisabled'); // Set initial status to voiceDisabled
  
  const porcupineWorkerRef = useRef<PorcupineWorker | null>(null); // Keep ref
  const vadRef = useRef<MicVAD | null>(null); // Keep ref
  const audioContextRef = useRef<AudioContext | null>(null); // Keep ref
  const audioSourceRef = useRef<AudioBufferSourceNode | null>(null); // Keep ref

  useEffect(() => {
    // Voice command functionality is currently disabled for future implementation.
    // Initialize AudioContext if it doesn't exist, though it won't be used for input for now.
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    console.log("Voice command initialization skipped. Voice input is currently disabled.");
    // No voice engine initialization here. The status remains 'voiceDisabled'.
    
    return () => {
      // Clean up if audio context was created, though not directly used for voice input anymore
      audioSourceRef.current?.stop();
      audioContextRef.current?.close();
      console.log("Audio resources cleaned up.");
    };
  }, []); // Keep useEffect structure, but with simplified logic

  const startListeningForWakeWord = () => {
    console.log("Wake word listening is currently disabled.");
    // setAssistantStatus('listeningForWakeWord'); // Placeholder, won't actually listen
  };
  
  const startVAD = async () => {
    console.log("VAD (Voice Activity Detection) is currently disabled.");
    // setAssistantStatus('listeningForCommand'); // Placeholder, won't actually listen
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    console.log("Audio transcription is currently disabled. Received audio blob:", audioBlob);
    setAssistantStatus('voiceDisabled'); // Go back to disabled state
    onCommand(translations.placeholder); // Still trigger onCommand with placeholder
  };

  const playAudio = async (audioArrayBuffer: ArrayBuffer) => { // Keep this function
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

  const getMicButton = () => { // Keep the function structure but simplify its logic
    const statusMap = {
      idle: { text: "Voice Disabled", className: "bg-gray-400", disabled: true },
      initializing: { text: "Voice Disabled", className: "bg-gray-400 animate-pulse", disabled: true },
      listeningForWakeWord: { text: "Voice Disabled", className: "bg-gray-400", disabled: true },
      listeningForCommand: { text: "Voice Disabled", className: "bg-gray-400", disabled: true },
      processing: { text: "Voice Disabled", className: "bg-gray-400", disabled: true },
      playingResponse: { text: "Playing response...", className: "bg-green-500 animate-pulse", disabled: true },
      error: { text: "Error! Voice Disabled.", className: "bg-gray-700", disabled: true },
      voiceDisabled: { text: "Voice Commands Disabled", className: "bg-gray-400", disabled: true }, // New status
    };
    const currentStatus = statusMap[assistantStatus];

    return (
      <div className="text-center">
        <Button
            type="button"
            onClick={() => console.log("Voice command button clicked, but functionality is disabled.")} // Placeholder click handler
            disabled={currentStatus.disabled || isLoading}
            className={`h-16 w-16 rounded-full transition-all duration-300 ${currentStatus.className}`}
        >
          <Mic className="w-6 h-6 text-white" />
        </Button>
        <p className="mt-4 text-sm text-gray-600 font-medium">{currentStatus.text}</p>
      </div>
    );
  };

  const handlePlayAssistantResponse = async () => { // Keep this function for playing text response
    if (response) {
      setAssistantStatus('playingResponse');
      try {
        const ttsResponse = await fetch('http://localhost:8000/send-command/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: response, response_type: "voice" }),
        });

        if (!ttsResponse.ok) {
          throw new Error(`HTTP error! status: ${ttsResponse.status}`);
        }

        const audioArrayBuffer = await ttsResponse.arrayBuffer();
        await playAudio(audioArrayBuffer);
      } catch (error) {
        console.error("Error playing assistant response:", error);
      } finally {
        setAssistantStatus('voiceDisabled'); // Go back to disabled after playing
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
              disabled={isLoading}
            />
            <Button type="submit" size="lg" className="h-14 px-6 bg-blue-600 hover:bg-blue-700 rounded-xl" disabled={isLoading}>
              <Send className="w-5 h-5" />
            </Button>
          </div>
          <div className="flex justify-center pt-4">{getMicButton()}</div> {/* Keep the button's structure */}
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