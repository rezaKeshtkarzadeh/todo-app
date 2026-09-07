import { apiClient } from "../api-client";
import type { SendOtpRequest, SendOtpResponse, VerifyOtpRequest, VerifyOtpResponse, RefreshResponse, LogoutResponse } from "../types";

export const authApi = {
  sendOtp: (data: SendOtpRequest) => apiClient.post<SendOtpResponse>("/auth/send-otp", data),
  verifyOtp: (data: VerifyOtpRequest) => apiClient.post<VerifyOtpResponse>("/auth/verify-otp", data),
  refresh: () => apiClient.post<RefreshResponse>("/auth/refresh"),
  logout: () => apiClient.post<LogoutResponse>("/auth/logout"),
  getCsrfToken: () => apiClient.get("/auth/csrf-token"),
};