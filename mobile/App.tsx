import React, { useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StatusBar, useColorScheme } from 'react-native';
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ListingsScreen from './src/screens/ListingsScreen';
import { apiClient } from './src/services/api';
import { Platform } from 'react-native';

// --- MOCK SCREENS ---
const DashboardScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text style={{ fontSize: 24, fontWeight: 'bold' }}>Rentaro Dashboard</Text>
  </View>
);

const ProfileScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text style={{ fontSize: 24, fontWeight: 'bold' }}>My Profile</Text>
  </View>
);

const Tab = createBottomTabNavigator();

const App = () => {
  const isDarkMode = useColorScheme() === 'dark';

  useEffect(() => {
    // 1. Request Permission & Get Notification Token
    const setupNotifications = async () => {
      try {
        const authStatus = await messaging().requestPermission();
        const enabled = 
          authStatus === messaging.AuthorizationStatus.AUTHORIZED || 
          authStatus === messaging.AuthorizationStatus.PROVISIONAL;

        if (enabled) {
          const token = await messaging().getToken();
          console.log('FCM Token:', token);
          
          // Register token with backend notification service
          await apiClient.post('/notifications/register', {
            device_token: token,
            platform: Platform.OS
          });
          
          await AsyncStorage.setItem('fcm_token', token);
        }
      } catch (error) {
        console.log('Notification registration failed:', error);
      }
    };

    setupNotifications();

    // 2. Listen for foreground messages
    const unsubscribe = messaging().onMessage(async remoteMessage => {
      console.log('Foreground Message received:', remoteMessage);
      // Logic to show local notification or custom UI alert
    });

    return unsubscribe;
  }, []);

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />
        <Tab.Navigator screenOptions={{ headerShown: true }}>
          <Tab.Screen name="Dashboard" component={DashboardScreen} />
          <Tab.Screen name="Listings" component={ListingsScreen} />
          <Tab.Screen name="Profile" component={ProfileScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

export default App;
