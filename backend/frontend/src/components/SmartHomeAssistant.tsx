// src/components/SmartHomeAssistant.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { HeroSection } from './HeroSection';
import { CommandInterface } from './CommandInterface';
import { DeviceStatusPanel } from './DeviceStatusPanel';
import { LanguageToggle } from './LanguageToggle';

export const SmartHomeAssistant = () => {
  const [language, setLanguage] = useState<'en' | 'fa'>('en');
  const [assistantResponse, setAssistantResponse] = useState('');
  const [deviceStatuses, setDeviceStatuses] = useState<{ [key: string]: string }>({}); // State to hold device statuses from backend
  const [isLoading, setIsLoading] = useState(false); // New state for loading indicator

  const translations = {
    en: {
      title: "Smart Home Assistant",
      subtitle: "Control your smart home with voice or text commands",
      placeholder: "Type your command or use the wake word...",
      listening: "Listening...",
      devices: "Device Status"
    },
    fa: {
      title: "دستیار خانه هوشمند",
      subtitle: "خانه هوشمند خود را با دستورات صوتی یا متنی کنترل کنید",
      placeholder: "دستور خود را تایپ یا کلمه کلیدی را استفاده کنید...",
      listening: "در حال گوش دادن...",
      devices: "وضعیت دستگاه‌ها"
    }
  };

  // Function to fetch device statuses from the backend
  const fetchDeviceStatuses = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/device-statuses/');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setDeviceStatuses(data);
      console.log("Fetched device statuses:", data);
    } catch (error) {
      console.error("Failed to fetch device statuses:", error);
      // setAssistantResponse(language === 'en' ? 'Error fetching device statuses.' : 'خطا در دریافت وضعیت دستگاه‌ها.');
    }
  }, []); // No need for language in useCallback dependencies if it's not directly used in the fetch URL/body

  // Fetch statuses on component mount and periodically
  useEffect(() => {
    fetchDeviceStatuses();
    const interval = setInterval(fetchDeviceStatuses, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [fetchDeviceStatuses]);

  const handleCommand = async (command: string) => {
    if (!command.trim()) return;

    setIsLoading(true);
    setAssistantResponse(language === 'en' ? 'Processing command...' : 'در حال پردازش دستور...');

    try {
      // Corrected endpoint for text commands
      const response = await fetch('http://localhost:8000/send-command/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command, response_type: "text" }), // Request text response for display
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Text command response:", data);
      
      const scheduledCount = data.scheduled_tasks ? data.scheduled_tasks.length : 0;
      let message = data.command || (language === 'en' ? 'Command processed.' : 'دستور پردازش شد.'); // Use 'command' from backend

      if (scheduledCount > 0) {
        // You might want to format 'scheduled' data into a more readable string here
        // For simplicity, just append count for now
        message += language === 'en' ? ` ${scheduledCount} task(s) scheduled.` : ` ${scheduledCount} وظیفه برنامه‌ریزی شد.`;
      }
      
      setAssistantResponse(message);
      
      // After a command, refresh device statuses to reflect potential changes
      fetchDeviceStatuses();

    } catch (error) {
      console.error("Failed to send command:", error);
      setAssistantResponse(language === 'en' ? 'Error connecting to assistant.' : 'خطا در اتصال به دستیار.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="flex justify-end mb-6">
          <LanguageToggle language={language} onLanguageChange={setLanguage} />
        </div>

        <HeroSection translations={translations[language]} />

        <div className="grid lg:grid-cols-3 gap-8 mt-12">
          <div className="lg:col-span-2">
            <CommandInterface 
              translations={translations[language]}
              onCommand={handleCommand} // This is for text commands derived from voice
              response={assistantResponse}
              isLoading={isLoading} // Pass loading state to CommandInterface
            />
          </div>

          <div className="lg:col-span-1">
            <DeviceStatusPanel 
              translations={translations[language]}
              language={language}
              deviceStatuses={deviceStatuses} // Pass device statuses to the panel
              fetchDeviceStatuses={fetchDeviceStatuses} // Pass fetch function for potential toggles
            />
          </div>
        </div>
      </div>
    </div>
  );
};