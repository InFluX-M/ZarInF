
import React from 'react';
import { Button } from '@/components/ui/button';
import { Globe } from 'lucide-react';

interface LanguageToggleProps {
  language: 'en' | 'fa';
  onLanguageChange: (language: 'en' | 'fa') => void;
}

export const LanguageToggle: React.FC<LanguageToggleProps> = ({ 
  language, 
  onLanguageChange 
}) => {
  return (
    <div className="flex items-center gap-2 bg-white/80 backdrop-blur-sm rounded-full p-1 shadow-lg border border-gray-200">
      <Button
        variant={language === 'en' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onLanguageChange('en')}
        className={`rounded-full px-4 transition-all duration-200 ${
          language === 'en' 
            ? 'bg-blue-600 hover:bg-blue-700 text-white' 
            : 'hover:bg-gray-100 text-gray-600'
        }`}
      >
        <Globe className="w-4 h-4 mr-1" />
        EN
      </Button>
      <Button
        variant={language === 'fa' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onLanguageChange('fa')}
        className={`rounded-full px-4 transition-all duration-200 ${
          language === 'fa' 
            ? 'bg-blue-600 hover:bg-blue-700 text-white' 
            : 'hover:bg-gray-100 text-gray-600'
        }`}
      >
        فا
      </Button>
    </div>
  );
};
