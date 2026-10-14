import Constants from 'expo-constants';

/**
 * API base URL.
 *
 * Priority order:
 *  1. EXPO_PUBLIC_API_URL environment variable (set in .env.local or eas.json)
 *  2. LAN IP derived from the Expo debugger host (works on physical devices
 *     when the phone and laptop are on the same Wi-Fi network)
 *  3. Localhost fallback (works in the laptop browser and iOS Simulator)
 *
 * For a physical device, set EXPO_PUBLIC_API_URL to your machine's LAN IP:
 *   EXPO_PUBLIC_API_URL=http://192.168.x.x:8000
 */
function resolveApiUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_URL;
  if (envUrl) return envUrl.replace(/\/$/, '');

  // On native, Constants.expoConfig?.hostUri is the LAN IP:port of the Metro
  // bundler, which is the same machine running the FastAPI backend.
  const hostUri = Constants.expoConfig?.hostUri;
  if (hostUri) {
    const host = hostUri.split(':')[0];
    if (host && host !== 'localhost') {
      return `http://${host}:8000`;
    }
  }

  return 'http://localhost:8000';
}

export const API_BASE_URL = resolveApiUrl();
export const API_V1 = `${API_BASE_URL}/api/v1`;
