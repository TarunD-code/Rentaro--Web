const API_URL = import.meta.env.VITE_API_URL;

export interface MediaItem {
  id: string;
  type: 'image' | 'video';
  url: string;
  thumbnailUrl?: string;
  mime?: string;
  size?: number;
}

export interface PropertyDetail {
  id: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  address: {
    city: string;
    state: string;
    country: string;
    geo?: { lat: number; lng: number };
  };
  amenities: string[];
  media: MediaItem[];
  host: {
    id: string;
    name: string;
    verified: boolean;
    responseTime: string;
  };
  createdAt: string;
  updatedAt: string;
}

export const fetchFeatured = async (limit: number = 6): Promise<any[]> => {
  const response = await fetch(`${API_URL}/property/?featured=true&limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch featured listings');
  return response.json();
};

export const getPropertyById = async (id: string): Promise<PropertyDetail> => {
  const response = await fetch(`${API_URL}/property/${id}`);
  if (!response.ok) throw new Error('Property not found');
  return response.json();
};

export const fetchSuggestions = async (q: string): Promise<string[]> => {
  if (!q) return [];
  const response = await fetch(`${API_URL}/property/search/suggestions?q=${q}`);
  if (!response.ok) return [];
  return response.json();
};
