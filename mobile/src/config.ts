import { Platform } from 'react-native';

const DEFAULT_WS_URL =
  Platform.OS === 'android' ? 'ws://10.0.2.2:8000/chat' : 'ws://localhost:8000/chat';

const env = (globalThis as any)?.process?.env as Record<string, string | undefined> | undefined;

export const WS_URL = env?.EXPO_PUBLIC_WS_URL ?? DEFAULT_WS_URL;
