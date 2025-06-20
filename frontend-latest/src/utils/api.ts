// utils/api.ts
import { WeatherData, ForecastData, AirQualityData } from '../types/weather';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export const weatherApi = {
  getCurrentWeather: async (location: string): Promise<WeatherData> => {
    const response = await fetch(`${API_BASE_URL}/weather/current`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ location }),
    });
    return response.json();
  },

  getForecast: async (location: string, days: number = 3): Promise<ForecastData> => {
    const response = await fetch(`${API_BASE_URL}/weather/forecast`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ location, days }),
    });
    return response.json();
  },

  getAirQuality: async (location: string): Promise<AirQualityData> => {
    const response = await fetch(`${API_BASE_URL}/weather/air-quality`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ location }),
    });
    return response.json();
  },

  updatePreferences: async (preferences: any) => {
    const response = await fetch(`${API_BASE_URL}/preferences`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ preferences }),
    });
    return response.json();
  },

  saveLocation: async (name: string, data: any) => {
    const response = await fetch(`${API_BASE_URL}/locations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, data }),
    });
    return response.json();
  },

  getAgentState: async () => {
    const response = await fetch(`${API_BASE_URL}/agent/state`);
    return response.json();
  },
};