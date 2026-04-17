import { useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';
import { firebaseConfig, VAPID_KEY } from './firebase_config';

const useFCM = () => {
  useEffect(() => {
    const setupFCM = async () => {
      try {
        const app = initializeApp(firebaseConfig);
        const messaging = getMessaging(app);

        // Request permission
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
          const token = await getToken(messaging, { vapidKey: VAPID_KEY });
          if (token) {
            console.log('FCM Token:', token);
            // In a real app, send this to the backend:
            // await fetch('/api/notification/device-token', { method: 'POST', body: JSON.stringify({ token }) })
          }
        }

        // Handle foreground messages
        onMessage(messaging, (payload) => {
          console.log('Foreground message received:', payload);
          // You could trigger a Toast notification here
        });
      } catch (err) {
        console.error('FCM Setup failed', err);
      }
    };

    if ('serviceWorker' in navigator) {
      setupFCM();
    }
  }, []);
};

export default useFCM;
