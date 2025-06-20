// components/WeatherCard.tsx
import React from 'react';
import { WeatherData } from '../../types/weather';
import { getWeatherIcon, getWeatherGradient } from '../../utils/weatherUtils';
import { Thermometer, Droplets, Wind, Eye } from 'lucide-react';

interface WeatherCardProps {
  weather: WeatherData;
  location: string;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather, location }) => {
  if (weather.error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
        <p>Error: {weather.error}</p>
      </div>
    );
  }

  return (
    <div className={`${getWeatherGradient(weather.description)} rounded-2xl p-6 text-black shadow-2xl animate-fade-in`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold">{location}</h2>
          <p className="text-lg capitalize opacity-90">{weather.description}</p>
        </div>
        <div className="text-6xl">
          {getWeatherIcon(weather.description)}
        </div>
      </div>
      
      <div className="text-5xl font-bold mb-6">
        {Math.round(weather.temperature)}°C
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-2">
          <Thermometer className="w-5 h-5" />
          <div>
            <p className="text-sm opacity-75">Feels like</p>
            <p className="font-semibold">{Math.round(weather.feels_like)}°C</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Droplets className="w-5 h-5" />
          <div>
            <p className="text-sm opacity-75">Humidity</p>
            <p className="font-semibold">{weather.humidity}%</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Wind className="w-5 h-5" />
          <div>
            <p className="text-sm opacity-75">Wind Speed</p>
            <p className="font-semibold">{weather.wind_speed} m/s</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Eye className="w-5 h-5" />
          <div>
            <p className="text-sm opacity-75">Visibility</p>
            <p className="font-semibold">Good</p>
          </div>
        </div>
      </div>
    </div>
  );
};