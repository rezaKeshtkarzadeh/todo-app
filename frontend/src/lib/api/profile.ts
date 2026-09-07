import { apiClient } from "../api-client";
import type {
  AvatarUploadResponse,
  PhoneChangeTokenResponse,
  RequestCurrentPhoneOtpResponse,
  VerifyCurrentPhoneOtpResponse,
  RequestNewPhoneOtpRequest,
  RequestNewPhoneOtpResponse,
  VerifyNewPhoneOtpRequest,
  VerifyNewPhoneOtpResponse,
} from "../types";

export const profileApi = {
  uploadAvatar: (formData: FormData) =>
    apiClient.post<AvatarUploadResponse>("/profile/avatar", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  requestCurrentPhoneOtp: () =>
    apiClient.post<RequestCurrentPhoneOtpResponse>("/profile/phone/request-current"),

  verifyCurrentPhoneOtp: (code: string) =>
    apiClient.post<VerifyCurrentPhoneOtpResponse>("/profile/phone/verify-current", { code }),

  requestNewPhoneOtp: (data: RequestNewPhoneOtpRequest) =>
    apiClient.post<RequestNewPhoneOtpResponse>("/profile/phone/request-new", data),

  verifyNewPhoneOtp: (data: VerifyNewPhoneOtpRequest) =>
    apiClient.post<VerifyNewPhoneOtpResponse>("/profile/phone/verify-new", data),
};