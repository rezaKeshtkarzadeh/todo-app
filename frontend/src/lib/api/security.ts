import { apiClient } from "../api-client";
import type { DeviceWithSessionsResponse, DeviceWithSessions } from "../types";

export const securityApi = {
  listDevices: () => apiClient.get<DeviceWithSessionsResponse>("/security/devices"),

  revokeSession: (sessionId: string) => apiClient.delete(`/security/sessions/${sessionId}`),

  revokeDeviceSessions: (deviceId: string) => apiClient.delete(`/security/devices/${deviceId}/sessions`),

  revokeAllSessions: () => apiClient.delete("/security/sessions"),
};