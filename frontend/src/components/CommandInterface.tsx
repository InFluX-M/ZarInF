import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Mic, Send, Volume2, Square } from 'lucide-react';

interface CommandInterfaceProps {
  translations: { placeholder: string; listening: string; };
  onCommand: (command: string) => void;
  response: string;
  isLoading: boolean;
}

type VoiceStatus = 'idle' | 'recording' | 'processing' | 'playingResponse' | 'error';

export const CommandInterface: React.FC<CommandInterfaceProps> = ({
  translations,
  onCommand,
  response,
  isLoading,
}) => {
  const [command, setCommand] = useState('');
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus>('idle');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const audioSourceRef = useRef<AudioBufferSourceNode | null>(null);

  useEffect(() => {
    // Initialize AudioContext
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    return () => {
      // Cleanup on unmount
      mediaRecorderRef.current?.stream.getTracks().forEach(track => track.stop());
      if (recordingTimeoutRef.current) {
        clearTimeout(recordingTimeoutRef.current);
      }
      audioSourceRef.current?.stop();
      audioContextRef.current?.close();
      console.log("Audio resources released.");
    };
  }, []);

  const transcribeAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'command.wav');
    formData.append('response_type', 'voice'); // Request voice response from backend

    try {
      setVoiceStatus('processing');
      const res = await fetch('http://localhost:8000/upload-audio/', {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      // If response is audio, play it directly
      if (res.headers.get('Content-Type')?.includes('audio')) {
        setVoiceStatus('playingResponse');
        const audioArrayBuffer = await res.arrayBuffer();
        await playAudio(audioArrayBuffer);
        setVoiceStatus('idle'); // Go back to idle after audio plays
      } else {
        // Otherwise, assume it's JSON with transcribed command
        const { command: transcribedText } = await res.json();
        console.log("Transcribed text:", transcribedText);

        if (transcribedText) {
          setCommand(transcribedText);
          onCommand(transcribedText); // Pass the transcribed text to the parent component
        }
        setVoiceStatus('idle'); // Go back to idle after processing
      }
    } catch (error) {
      console.error('Transcription request failed:', error);
      setVoiceStatus('error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
    if (recordingTimeoutRef.current) {
      clearTimeout(recordingTimeoutRef.current);
      recordingTimeoutRef.current = null;
    }
  };

  const handleMicClick = async () => {
    if (voiceStatus === 'recording') {
      stopRecording();
      return;
    }

    if (voiceStatus !== 'idle' && voiceStatus !== 'error') return;

    setVoiceStatus('recording');
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop()); // Stop the microphone access
      };

      mediaRecorderRef.current.start();

      // Set a 10-second timeout to automatically stop recording
      recordingTimeoutRef.current = setTimeout(() => {
        console.log("Recording timed out after 10 seconds.");
        stopRecording();
      }, 10000);

    } catch (error) {
      console.error("Microphone access denied or error:", error);
      setVoiceStatus('error');
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
      setVoiceStatus('idle'); // Reset status on playback error
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
      idle: { text: "Click to Speak", className: "bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 hover:scale-110", icon: <Mic className="w-6 h-6 text-white" />, disabled: false },
      recording: { text: "Recording... (Click to Stop)", className: "bg-red-500 hover:bg-red-600 animate-pulse", icon: <Square className="w-6 h-6 text-white" />, disabled: false },
      processing: { text: "Processing...", className: "bg-yellow-500 hover:bg-yellow-600 animate-pulse", icon: <Mic className="w-6 h-6 text-white" />, disabled: true },
      playingResponse: { text: "Playing response...", className: "bg-green-500 animate-pulse", icon: <Volume2 className="w-6 h-6 text-white" />, disabled: true },
      error: { text: "Error! Click to retry.", className: "bg-gray-700", icon: <Mic className="w-6 h-6 text-white" />, disabled: false },
    };
    const currentStatus = statusMap[voiceStatus];

    return (
      <div className="text-center">
        <Button
            type="button"
            onClick={handleMicClick}
            disabled={currentStatus.disabled || isLoading}
            className={`h-16 w-16 rounded-full transition-all duration-300 ${currentStatus.className}`}
        >
          {currentStatus.icon}
        </Button>
        <p className="mt-4 text-sm text-gray-600 font-medium">{currentStatus.text}</p>
      </div>
    );
  };

  const handlePlayAssistantResponse = async () => {
    if (response && voiceStatus !== 'playingResponse') {
      setVoiceStatus('playingResponse');
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
        setVoiceStatus('idle');
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
              disabled={isLoading || voiceStatus === 'processing'}
            />
            <Button type="submit" size="lg" className="h-14 px-6 bg-blue-600 hover:bg-blue-700 rounded-xl" disabled={isLoading || voiceStatus === 'processing'}>
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
              disabled={voiceStatus === 'playingResponse' || voiceStatus === 'recording'}
            >
              <Volume2 className="w-4 h-4" />
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};