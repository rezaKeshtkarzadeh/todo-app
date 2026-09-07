import axios, { type AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig, type AxiosResponse } from "axios";
import { ApiError } from "./api-error";
import { getCsrfToken } from "./csrf";
import { getDeviceId } from "./device-id";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

let refreshPromise: Promise<void> | null = null;
let isRefreshing = false;

function clearAuthState(): void {
  if (typeof window !== "undefined") {
    const { clearPreferences } = require("./local-prefs");
    clearPreferences();
  }
}

function createMockResponse(axiosResponse: AxiosResponse): Response {
  return {
    status: axiosResponse.status,
    statusText: axiosResponse.statusText,
    ok: axiosResponse.status >= 200 && axiosResponse.status < 300,
    headers: new Headers(axiosResponse.headers as Record<string, string>),
    url: axiosResponse.config.url ? new URL(axiosResponse.config.url, API_URL).toString() : "",
    redirected: false,
    type: "basic",
    clone: () => createMockResponse(axiosResponse),
    body: null,
    bodyUsed: false,
    arrayBuffer: async () => new ArrayBuffer(0),
    blob: async () => new Blob(),
    formData: async () => new FormData(),
    json: async () => axiosResponse.data,
    text: async () => JSON.stringify(axiosResponse.data),
  } as Response;
}

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const deviceId = getDeviceId();
    if (deviceId) {
      config.headers["X-Device-Id"] = deviceId;
    }

    const isMutation = ["post", "put", "patch", "delete"].includes(config.method?.toLowerCase() || "");
    if (isMutation) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        config.headers["X-CSRF-Token"] = csrfToken;
      }
    }

    if (config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    }

    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      const errorData = error.response.data as { error?: { code: string } };
      const isSessionRevoked = errorData?.error?.code === "AUTH_SESSION_REVOKED";

      if (isSessionRevoked) {
        clearAuthState();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(ApiError.fromResponse(createMockResponse(error.response), error.response.data));
      }

      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = (async () => {
          try {
            await apiClient.post("/auth/refresh");
          } finally {
            isRefreshing = false;
            refreshPromise = null;
          }
        })();
      }

      try {
        await refreshPromise;
      } catch (refreshError) {
        clearAuthState();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        throw refreshError;
      }

      originalRequest._retry = true;
      return apiClient(originalRequest);
    }

    if (error.response) {
      return Promise.reject(ApiError.fromResponse(createMockResponse(error.response), error.response.data));
    }

    return Promise.reject(ApiError.fromNetworkError(error));
  }
);

export default apiClient;