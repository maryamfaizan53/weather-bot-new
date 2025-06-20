// utils/weatherUtils.ts
export const getWeatherIcon = (description: string) => {
  const desc = description.toLowerCase();
  if (desc.includes('clear') || desc.includes('sun')) return '☀️';
  if (desc.includes('cloud')) return '☁️';
  if (desc.includes('rain') || desc.includes('drizzle')) return '🌧️';
  if (desc.includes('snow')) return '❄️';
  if (desc.includes('thunder')) return '⛈️';
  if (desc.includes('mist') || desc.includes('fog')) return '🌫️';
  return '🌤️';
};

export const getWeatherGradient = (description: string) => {
  const desc = description.toLowerCase();
  if (desc.includes('clear') || desc.includes('sun')) return 'bg-sunny-gradient';
  if (desc.includes('cloud')) return 'bg-cloudy-gradient';
  if (desc.includes('rain') || desc.includes('drizzle')) return 'bg-rainy-gradient';
  if (desc.includes('snow')) return 'bg-gradient-to-br from-blue-100 to-blue-300';
  if (desc.includes('thunder')) return 'bg-gradient-to-br from-gray-800 to-gray-900';
  return 'bg-gradient-to-br from-blue-400 to-blue-600';
};

export const getAQILevel = (aqi: number) => {
  if (aqi === 1) return { level: 'Good', color: 'text-green-500', bgColor: 'bg-green-100' };
  if (aqi === 2) return { level: 'Fair', color: 'text-yellow-500', bgColor: 'bg-yellow-100' };
  if (aqi === 3) return { level: 'Moderate', color: 'text-orange-500', bgColor: 'bg-orange-100' };
  if (aqi === 4) return { level: 'Poor', color: 'text-red-500', bgColor: 'bg-red-100' };
  if (aqi === 5) return { level: 'Very Poor', color: 'text-purple-500', bgColor: 'bg-purple-100' };
  return { level: 'Unknown', color: 'text-gray-500', bgColor: 'bg-gray-100' };
};

export const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
};