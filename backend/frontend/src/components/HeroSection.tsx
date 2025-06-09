
import React from 'react';

interface HeroSectionProps {
  translations: {
    title: string;
    subtitle: string;
  };
}

export const HeroSection: React.FC<HeroSectionProps> = ({ translations }) => {
  return (
    <div className="text-center mb-12">
      <div className="relative">
        <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-6 animate-fade-in">
          {translations.title}
        </h1>
        <div className="absolute -top-2 -left-2 w-4 h-4 bg-blue-500 rounded-full animate-pulse opacity-60"></div>
        <div className="absolute -bottom-2 -right-2 w-3 h-3 bg-purple-500 rounded-full animate-pulse opacity-60 delay-1000"></div>
      </div>
      <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed animate-fade-in">
        {translations.subtitle}
      </p>
    </div>
  );
};
