// types/weather.ts
export interface WeatherData {
  temperature: number;
  feels_like: number;
  humidity: number;
  description: string;
  wind_speed: number;
  error?: string;
}

export interface ForecastData {
  forecast: Array<{
    dt: number;
    main: {
      temp: number;
      feels_like: number;
      humidity: number;
    };
    weather: Array<{
      main: string;
      description: string;
      icon: string;
    }>;
    wind: {
      speed: number;
    };
  }>;
  city: string;
  error?: string;
}

export interface AirQualityData {
  aqi: number;
  components: {
    co: number;
    no: number;
    no2: number;
    o3: number;
    so2: number;
    pm2_5: number;
    pm10: number;
    nh3: number;
  };
  error?: string;
}

export interface SavedLocation {
  name: string;
  data: any;
}