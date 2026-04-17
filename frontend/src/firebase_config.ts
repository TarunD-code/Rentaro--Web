// Firebase Cloud Messaging (FCM) Configuration
// NOTE: In production, these should be environment variables (import.meta.env.VITE_FCM_...)

export const firebaseConfig = {
  apiKey: "MOCK_API_KEY",
  authDomain: "rentora-fcm.firebaseapp.com",
  projectId: "rentora-fcm",
  storageBucket: "rentora-fcm.appspot.com",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef123456"
};

// VAPID Key used for web push registration
export const VAPID_KEY = "BDf_rT-UvXGkK-hM... (placeholder)";
