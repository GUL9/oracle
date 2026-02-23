import { StatusBar } from 'expo-status-bar';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import Markdown from 'react-native-markdown-display';

import { WS_URL } from './src/config';

type ConnectionState = 'disconnected' | 'connecting' | 'connected';

type IncomingMessage =
  | { type: 'chunk'; data: string }
  | { type: string; data?: unknown };

const markdownStyles = StyleSheet.create({
  body: { color: '#e9e9ef', fontSize: 14, lineHeight: 20 },
  heading1: { color: '#fff' },
  heading2: { color: '#fff' },
  heading3: { color: '#fff' },
  strong: { color: '#fff' },
  em: { color: '#e9e9ef' },
  bullet_list: { marginVertical: 6 },
  ordered_list: { marginVertical: 6 },
  list_item: { marginVertical: 2 },
  link: { color: '#93c5fd' },
  code_inline: {
    color: '#e9e9ef',
    backgroundColor: '#0b0b0f',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  fence: {
    color: '#e9e9ef',
    backgroundColor: '#0b0b0f',
    borderRadius: 10,
    padding: 10,
  },
  blockquote: {
    borderLeftColor: '#2b2b3a',
    borderLeftWidth: 4,
    paddingLeft: 10,
    opacity: 0.95,
  },
  table: { borderWidth: 1, borderColor: '#2b2b3a' },
  tr: { borderBottomWidth: 1, borderBottomColor: '#2b2b3a' },
  th: { backgroundColor: '#0b0b0f' },
  td: { backgroundColor: '#12121a' },
});

export default function App() {
  const socketRef = useRef<WebSocket | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState<string | null>(null);

  const canSend = useMemo(() => {
    return prompt.trim().length > 0 && connectionState !== 'connecting';
  }, [prompt, connectionState]);

  const connect = async (): Promise<WebSocket> => {
    setError(null);

    const existingSocket = socketRef.current;
    if (existingSocket && existingSocket.readyState === WebSocket.OPEN) {
      setConnectionState('connected');
      return existingSocket;
    }

    if (existingSocket) {
      try {
        existingSocket.close();
      } catch {
        // ignore
      }
      socketRef.current = null;
    }

    setConnectionState('connecting');

    return await new Promise<WebSocket>((resolve, reject) => {
      const socket = new WebSocket(WS_URL);
      socketRef.current = socket;

      let settled = false;
      let timeoutId: ReturnType<typeof setTimeout> | null = null;

      socket.onopen = () => {
        if (settled) return;
        settled = true;
        if (timeoutId) clearTimeout(timeoutId);
        setConnectionState('connected');
        resolve(socket);
      };

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(String(event.data)) as IncomingMessage;
          if (parsed?.type === 'chunk' && typeof parsed.data === 'string') {
            setResponse((prev) => prev + parsed.data);
          }
        } catch (e) {
          setError(`Failed to parse message: ${String(e)}`);
        }
      };

      socket.onerror = () => {
        setError('WebSocket error. Check server URL and network.');
      };

      socket.onclose = () => {
        if (timeoutId) clearTimeout(timeoutId);
        setConnectionState('disconnected');
      };

      timeoutId = setTimeout(() => {
        if (settled) return;
        settled = true;
        try {
          socket.close();
        } catch {
          // ignore
        }
        reject(new Error('Connection timed out'));
      }, 8000);
    });
  };

  const disconnect = () => {
    const socket = socketRef.current;
    socketRef.current = null;

    if (!socket) return;
    try {
      socket.close();
    } catch {
      // ignore
    }
  };

  const sendPrompt = async () => {
    const content = prompt.trim();
    if (!content) return;

    setError(null);
    setResponse('');

    try {
      const socket = await connect();
      socket.send(JSON.stringify({ content }));
    } catch (e) {
      setConnectionState('disconnected');
      setError(`Failed to connect/send: ${String(e)}`);
    }
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <Text style={styles.title}>Oracle (Mobile)</Text>

        <View style={styles.row}>
          <Text style={styles.label}>Server</Text>
          <Text numberOfLines={1} style={styles.value}>
            {WS_URL}
          </Text>
        </View>

        <View style={styles.row}>
          <Text style={styles.label}>Status</Text>
          <View style={styles.statusPill}>
            {connectionState === 'connecting' ? (
              <ActivityIndicator size="small" />
            ) : (
              <Text style={styles.statusText}>{connectionState}</Text>
            )}
          </View>
        </View>

        <TextInput
          value={prompt}
          onChangeText={setPrompt}
          placeholder="Ask something…"
          placeholderTextColor="#999"
          style={styles.input}
          multiline
        />

        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.button, !canSend ? styles.buttonDisabled : null]}
            disabled={!canSend}
            onPress={sendPrompt}
          >
            <Text style={styles.buttonText}>Send</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.button, styles.buttonSecondary]} onPress={() => setResponse('')}>
            <Text style={styles.buttonTextSecondary}>Clear</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.button, styles.buttonSecondary]} onPress={disconnect}>
            <Text style={styles.buttonTextSecondary}>Disconnect</Text>
          </TouchableOpacity>
        </View>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <View style={styles.responseHeader}>
          <Text style={styles.responseTitle}>Response</Text>
        </View>

        <ScrollView style={styles.responseBox} contentContainerStyle={styles.responseContent}>
          {response ? (
            <Markdown
              style={markdownStyles}
              onLinkPress={(url) => {
                Linking.openURL(url).catch(() => {
                  setError(`Failed to open link: ${url}`);
                });
                return false;
              }}
            >
              {response}
            </Markdown>
          ) : (
            <Text style={styles.responseText}>—</Text>
          )}
        </ScrollView>
      </View>
      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#0b0b0f' },
  container: { flex: 1, padding: 16, gap: 12 },
  title: { color: '#fff', fontSize: 22, fontWeight: '700' },
  row: { flexDirection: 'row', gap: 10, alignItems: 'center' },
  label: { color: '#b7b7c2', width: 56 },
  value: { color: '#fff', flex: 1 },
  statusPill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: '#1a1a24',
  },
  statusText: { color: '#fff', textTransform: 'capitalize' },
  input: {
    minHeight: 84,
    borderRadius: 12,
    padding: 12,
    backgroundColor: '#12121a',
    color: '#fff',
    borderWidth: 1,
    borderColor: '#222233',
  },
  buttonRow: { flexDirection: 'row', gap: 10, flexWrap: 'wrap' },
  button: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: '#4f46e5',
  },
  buttonDisabled: { opacity: 0.55 },
  buttonSecondary: { backgroundColor: '#1a1a24' },
  buttonText: { color: '#fff', fontWeight: '700' },
  buttonTextSecondary: { color: '#fff', fontWeight: '600' },
  error: { color: '#ff6b6b' },
  responseHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  responseTitle: { color: '#fff', fontSize: 16, fontWeight: '700' },
  responseBox: {
    flex: 1,
    borderRadius: 12,
    backgroundColor: '#12121a',
    borderWidth: 1,
    borderColor: '#222233',
  },
  responseContent: { padding: 12 },
  responseText: { color: '#e9e9ef', lineHeight: 20 },
});
