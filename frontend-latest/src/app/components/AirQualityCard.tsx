// components/AirQualityCard.tsx
import React from 'react';
import { AirQualityData } from '../../types/weather';
import { getAQILevel } from '../../utils/weatherUtils';
import { Leaf } from 'lucide-react';

interface AirQualityCardProps {
  airQuality: AirQualityData;
}

export const AirQualityCard: React.FC<AirQualityCardProps> = ({ airQuality }) => {
  if (airQuality.error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
        <p>Error: {airQuality.error}</p>
      </div>
    );
  }

  const aqiInfo = getAQILevel(airQuality.aqi);

  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg animate-slide-up">
      <div className="flex items-center space-x-2 mb-4">
        <Leaf className="w-6 h-6 text-green-600" />
        <h3 className="text-xl font-bold text-gray-800">Air Quality</h3>
      </div>
      
      <div className={`${aqiInfo.bgColor} rounded-lg p-4 mb-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">AQI Level</p>
            <p className={`text-2xl font-bold ${aqiInfo.color}`}>{airQuality.aqi}</p>
          </div>
          <div className="text-right">
            <p className={`text-lg font-semibold ${aqiInfo.color}`}>{aqiInfo.level}</p>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-gray-50 p-3 rounded-lg">
          <p className="text-gray-600">PM2.5</p>
          <p className="font-semibold">{airQuality.components.pm2_5.toFixed(1)} μg/m³</p>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <p className="text-gray-600">PM10</p>
          <p className="font-semibold">{airQuality.components.pm10.toFixed(1)} μg/m³</p>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <p className="text-gray-600">O₃</p>
          <p className="font-semibold">{airQuality.components.o3.toFixed(1)} μg/m³</p>
        </div>
        <div className="bg-gray-50 p-3 rounded-lg">
          <p className="text-gray-600">NO₂</p>
          <p className="font-semibold">{airQuality.components.no2.toFixed(1)} μg/m³</p>
        </div>
      </div>
    </div>
  );
};
