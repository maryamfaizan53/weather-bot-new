// app/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { WeatherCard } from './components/WeatherCard';
import { ForecastCard } from './components/ForecastCard';
import { AirQualityCard } from './components/AirQualityCard';
import { SearchBar } from './components/SearchBar';
import { weatherApi } from '../utils/api';
import { WeatherData, ForecastData, AirQualityData } from '../types/weather';
import { Cloud, Sun, CloudRain } from 'lucide-react';

export default function Home() {
  const [currentWeather, setCurrentWeather] = useState<WeatherData | null>(null);
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [airQuality, setAirQuality] = useState<AirQualityData | null>(null);
  const [currentLocation, setCurrentLocation] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchWeatherData = async (location: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const [weatherData, forecastData, airQualityData] = await Promise.all([
        weatherApi.getCurrentWeather(location),
        weatherApi.getForecast(location, 3),
        weatherApi.getAirQuality(location)
      ]);

      setCurrentWeather(weatherData);
      setForecast(forecastData);
      setAirQuality(airQualityData);
      setCurrentLocation(location);
    } catch (err) {
      setError('Failed to fetch weather data. Please try again.');
      console.error('Error fetching weather data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load default location on mount
    fetchWeatherData('London');
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-center space-x-3">
            <div className="flex items-center space-x-2">
              <Sun className="w-8 h-8 text-yellow-500" />
              <Cloud className="w-8 h-8 text-blue-500 -ml-2" />
              <CloudRain className="w-8 h-8 text-blue-600 -ml-2" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">WeatherWise</h1>
          </div>
          <p className="text-center text-gray-600 mt-2">Your intelligent weather companion</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <SearchBar onSearch={fetchWeatherData} loading={loading} />

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
            <p>{error}</p>
          </div>
        )}

        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500"></div>
          </div>
        )}

        {!loading && currentWeather && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Weather Card */}
            <div className="lg:col-span-2">
              <WeatherCard weather={currentWeather} location={currentLocation} />
            </div>

            {/* Side Cards */}
            <div className="space-y-6">
              {forecast && <ForecastCard forecast={forecast} />}
              {airQuality && <AirQualityCard airQuality={airQuality} />}
            </div>
          </div>
        )}

        {/* Additional Features */}
        {!loading && currentWeather && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-6 shadow-lg text-center">
              <div className="text-3xl mb-2">🌅</div>
              <h3 className="font-semibold text-gray-800">Sunrise</h3>
              <p className="text-gray-600">6:30 AM</p>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-lg text-center">
              <div className="text-3xl mb-2">🌇</div>
              <h3 className="font-semibold text-gray-800">Sunset</h3>
              <p className="text-gray-600">7:45 PM</p>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-lg text-center">
              <div className="text-3xl mb-2">🌙</div>
              <h3 className="font-semibold text-gray-800">Moon Phase</h3>
              <p className="text-gray-600">Waxing Crescent</p>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-lg text-center">
              <div className="text-3xl mb-2">📊</div>
              <h3 className="font-semibold text-gray-800">UV Index</h3>
              <p className="text-gray-600">Moderate</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>&copy; 2024 WeatherWise. Your intelligent weather companion.</p>
          <p className="text-gray-400 mt-2">Powered by OpenWeatherMap API</p>
        </div>
      </footer>
    </div>
  );
}