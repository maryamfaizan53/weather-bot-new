//  components/SearchBar.tsx
import React, { useState } from 'react';
import { Search, MapPin } from 'lucide-react';

interface SearchBarProps {
  onSearch: (location: string) => void;
  loading: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, loading }) => {
  const [location, setLocation] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (location.trim()) {
      onSearch(location.trim());
    }
  };

  const handleCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          onSearch(`${latitude},${longitude}`);
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please search manually.');
        }
      );
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mb-8">
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Search for a city..."
              className="w-full pl-12 pr-4 py-4 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-l-2xl"
              disabled={loading}
            />
          </div>
          
          <button
            type="button"
            onClick={handleCurrentLocation}
            className="px-4 py-4 text-gray-500 hover:text-blue-500 hover:bg-gray-50 transition-colors"
            disabled={loading}
          >
            <MapPin className="w-5 h-5" />
          </button>
          
          <button
            type="submit"
            disabled={loading || !location.trim()}
            className="px-8 py-4 bg-blue-500 text-white font-semibold hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors rounded-r-2xl"
          >
            {loading ? 'Loading...' : 'Search'}
          </button>
        </div>
      </form>
    </div>
  );
};