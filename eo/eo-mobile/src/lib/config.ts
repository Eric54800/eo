import Constants from "expo-constants";

const extra = Constants.expoConfig?.extra ?? {};

export const PUBLIC_API_BASE_URL =
  String(extra.publicApiBaseUrl ?? "http://127.0.0.1:8000/api/public").replace(/\/$/, "");
