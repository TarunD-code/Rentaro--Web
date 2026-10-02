import axios from 'axios';

// Gateway URL
const API_URL = 'http://10.0.2.2:8000'; // Standard Android Emulator Loopback

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
});

apiClient.interceptors.request.use(
  async (config) => {
    // In a real app, retrieve token from secure storage
    // const token = await getToken();
    // if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);
