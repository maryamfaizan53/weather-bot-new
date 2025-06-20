// components/ForecastCard.tsx
import React from 'react';
import { ForecastData } from '../../types/weather';
import { getWeatherIcon, formatDate } from '../../utils/weatherUtils';

interface ForecastCardProps {
  forecast: ForecastData;
}

export const ForecastCard: React.FC<ForecastCardProps> = ({ forecast }) => {
  if (forecast.error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
        <p>Error: {forecast.error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg animate-slide-up">
      <h3 className="text-xl font-bold text-gray-800 mb-4">3-Day Forecast</h3>
      
      <div className="space-y-4">
        {forecast.forecast.map((day, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{getWeatherIcon(day.weather[0].description)}</span>
              <div>
                <p className="font-semibold text-gray-800">{formatDate(day.dt)}</p>
                <p className="text-sm text-gray-600 capitalize">{day.weather[0].description}</p>
              </div>
            </div>
            
            <div className="text-right">
              <p className="text-lg font-bold text-gray-800">{Math.round(day.main.temp)}°C</p>
              <p className="text-sm text-gray-600">Feels {Math.round(day.main.feels_like)}°C</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
