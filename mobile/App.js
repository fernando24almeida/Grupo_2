import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, FlatList, ActivityIndicator } from 'react-native';
import axios from 'axios';

const API_URL = 'http://YOUR_BACKEND_IP:8000/clinical/episodes';

export default function App() {
  const [episodes, setEpisodes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEpisodes();
  }, []);

  const fetchEpisodes = async () => {
    try {
      const response = await axios.get(API_URL);
      setEpisodes(response.data);
      setLoading(false);
    } catch (error) {
      console.error(error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#0000ff" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Consulta de Episódios</Text>
      <FlatList
        data={episodes}
        keyExtractor={(item) => item.cod_epis}
        renderItem={({ item }) => (
          <View style={styles.item}>
            <Text style={styles.itemTitle}>Cod: {item.cod_epis}</Text>
            <Text>Entrada: {new Date(item.data_h_entr).toLocaleString()}</Text>
            <Text>Utente ID: {item.id_utente}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 50,
    backgroundColor: '#fff',
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#007bff'
  },
  item: {
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  itemTitle: {
    fontWeight: 'bold',
    fontSize: 16,
  }
});
