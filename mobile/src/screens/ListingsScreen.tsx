import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  FlatList, 
  ActivityIndicator, 
  StyleSheet, 
  RefreshControl, 
  Platform 
} from 'react-native';
import { apiClient } from '../services/api';
import { getListingsFromCache, saveListingsToCache } from '../services/cache';

const ListingsScreen = () => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchListings = async () => {
    try {
      const response = await apiClient.get('/property/');
      const data = response.data;
      setListings(data);
      await saveListingsToCache(data);
      setError(null);
    } catch (err) {
      console.warn('Network fetch failed, loading from cache...', err);
      const cachedData = await getListingsFromCache();
      setListings(cachedData);
      setError('Showing cached results (Offline)');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchListings();
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#0A3D62" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error && <Text style={styles.errorText}>{error}</Text>}
      <FlatList
        data={listings}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.price}>{item.currency} {item.price}</Text>
            <Text style={styles.address}>{item.address}</Text>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text>No listings found.</Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: '#FFF',
    margin: 10,
    padding: 15,
    borderRadius: 8,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
    }),
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0A3D62',
  },
  price: {
    fontSize: 16,
    color: '#27AE60',
    marginTop: 5,
  },
  address: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  errorText: {
    backgroundColor: '#FFEBEE',
    color: '#B71C1C',
    textAlign: 'center',
    padding: 10,
    fontSize: 12,
  }
});

export default ListingsScreen;
