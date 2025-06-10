// src/components/DeviceStatusPanel.tsx

import React from 'react';
import { Card } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Lightbulb, Wind, Tv } from 'lucide-react';

interface DeviceStatusPanelProps {
  translations: {
    devices: string;
  };
  language: 'en' | 'fa';
  deviceStatuses: { [key: string]: string }; // Expected from backend
  fetchDeviceStatuses: () => void; // Function to refetch statuses from parent
}

// Map backend device names to friendly names and types for display
const DEVICE_METADATA: { [key: string]: { name: { en: string; fa: string }; type: 'lamp' | 'ac' | 'tv' | 'cooler' | 'other' } } = {
  'lamp_kitchen': { name: { en: 'Kitchen Lamp', fa: 'چراغ آشپزخانه' }, type: 'lamp' },
  'lamp_bathroom': { name: { en: 'Bathroom Lamp', fa: 'چراغ حمام' }, type: 'lamp' },
  'lamp_room1': { name: { en: 'Room 1 Lamp', fa: 'چراغ اتاق ۱' }, type: 'lamp' },
  'lamp_room2': { name: { en: 'Room 2 Lamp', fa: 'چراغ اتاق ۲' }, type: 'lamp' },
  'AC_room1': { name: { en: 'Room 1 AC', fa: 'کولر اتاق ۱' }, type: 'ac' },
  'AC_kitchen': { name: { en: 'Kitchen AC', fa: 'کولر آشپزخانه' }, type: 'ac' },
  'Cooler': { name: { en: 'Cooler', fa: 'کولر' }, type: 'cooler' }, // Assuming 'Cooler' is a distinct device
  'TV': { name: { en: 'Living Room TV', fa: 'تلویزیون پذیرایی' }, type: 'tv' }, // Assuming backend just returns 'TV'
};

export const DeviceStatusPanel: React.FC<DeviceStatusPanelProps> = ({ 
  translations, 
  language,
  deviceStatuses, // Receive from parent
  fetchDeviceStatuses // Receive from parent
}) => {

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'lamp':
        return <Lightbulb className="w-5 h-5" />;
      case 'ac':
      case 'cooler': 
        return <Wind className="w-5 h-5" />;
      case 'tv':
        return <Tv className="w-5 h-5" />;
      default:
        return <Lightbulb className="w-5 h-5" />;
    }
  };

  // Helper to get structured device list from backend statuses
  const getDisplayDevices = () => {
    // Filter out devices from backend_status that don't have metadata, or if metadata is empty
    return Object.entries(deviceStatuses).map(([backendName, status]) => {
      const metadata = DEVICE_METADATA[backendName];
      if (!metadata) {
        console.warn(`No metadata found for device: ${backendName}. Skipping.`);
        return null; // Skip unknown devices
      }
      return {
        id: backendName, // Use backend name as ID
        name: metadata.name,
        type: metadata.type,
        status: status === 'on', // Convert 'on'/'off' string to boolean
      };
    }).filter(Boolean); // Remove null entries
  };

  const displayDevices = getDisplayDevices();
  const activeDeviceCount = displayDevices.filter(d => d?.status).length; 

  // NOTE: This toggleDevice function will trigger a refetch of statuses from the backend.
  // For actual device control, you would need a dedicated API endpoint in your backend
  // that takes a device ID and an action (e.g., 'on'/'off') and then updates the DB.
  // The current backend only updates device status when a scheduled task runs.
  const toggleDevice = async (deviceId: string, currentStatus: boolean) => {
    console.warn(`Manual toggle for device '${deviceId}' triggered. This currently only re-fetches status. ` + 
                 `For actual control, implement a backend API endpoint (e.g., /control-device/${deviceId}/${currentStatus ? 'off' : 'on'})`);
    // Example of how you might call a *hypothetical* backend endpoint:
    // const action = currentStatus ? 'off' : 'on';
    // try {
    //   const response = await fetch(`http://localhost:8000/control-device/${deviceId}/${action}`, { method: 'POST' });
    //   if (!response.ok) throw new Error('Failed to toggle device');
    //   fetchDeviceStatuses(); // Refresh statuses after a successful toggle
    // } catch (error) {
    //   console.error("Error toggling device:", error);
    // }
    
    // For now, just trigger a refresh to reflect any potential changes if backend processes it
    fetchDeviceStatuses();
  };

  return (
    <Card className="p-6 bg-white/80 backdrop-blur-sm border-0 shadow-lg h-fit">
      <h2 className="text-xl font-semibold text-gray-800 mb-6 flex items-center gap-2">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        {translations.devices}
      </h2>
      
      <div className="space-y-4">
        {displayDevices.length > 0 ? (
          displayDevices.map((device) => (
            device && ( // Ensure device is not null
              <div 
                key={device.id}
                className="flex items-center justify-between p-4 rounded-lg bg-gray-50/80 hover:bg-gray-100/80 transition-all duration-200 group"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg transition-colors duration-200 ${
                    device.status 
                      ? 'bg-green-100 text-green-600' 
                      : 'bg-gray-200 text-gray-500'
                  }`}>
                    {getDeviceIcon(device.type)}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-800 group-hover:text-gray-900">
                      {device.name[language]}
                    </h3>
                    <p className={`text-sm ${
                      device.status ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {device.status ? (language === 'en' ? 'ON' : 'روشن') : (language === 'en' ? 'OFF' : 'خاموش')}
                    </p>
                  </div>
                </div>
                
                <Switch
                  checked={device.status}
                  onCheckedChange={() => toggleDevice(device.id, device.status)}
                  className="data-[state=checked]:bg-green-500"
                />
              </div>
            )
          ))
        ) : (
          <p className="text-center text-gray-500">No devices found or error fetching statuses.</p>
        )}
      </div>
      
      <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            {language === 'en' ? 'Active Devices' : 'دستگاه‌های فعال'}
          </span>
          <span className="font-semibold text-blue-600">
            {activeDeviceCount} / {displayDevices.length}
          </span>
        </div>
      </div>
    </Card>
  );
};