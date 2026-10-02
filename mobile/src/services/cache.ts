import AsyncStorage from '@react-native-async-storage/async-storage';

const LISTINGS_CACHE_KEY = '@rentaro_listings';

export const saveListingsToCache = async (listings: any[]) => {
  try {
    const jsonValue = JSON.stringify(listings);
    await AsyncStorage.setItem(LISTINGS_CACHE_KEY, jsonValue);
  } catch (e) {
    console.error('Failed to save listings to cache:', e);
  }
};

export const getListingsFromCache = async () => {
  try {
    const jsonValue = await AsyncStorage.getItem(LISTINGS_CACHE_KEY);
    return jsonValue != null ? JSON.parse(jsonValue) : [];
  } catch (e) {
    console.error('Failed to retrieve listings from cache:', e);
    return [];
  }
};
