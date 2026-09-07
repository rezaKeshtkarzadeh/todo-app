export interface User {
  id: string;
  phone_number: string;
  avatar_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  user_id: string;
  title: string;
  is_done: boolean;
  created_at: string;
  updated_at: string;
}

export interface Session {
  id: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string;
  is_current: boolean;
}

export interface DeviceWithSessions {
  id: string;
  name: string | null;
  user_agent: string | null;
  created_at: string;
  last_seen_at: string | null;
  sessions: Session[];
}

export interface SendOtpRequest {
  phone_number: string;
}

export interface SendOtpResponse {
  message: string;
  otp_debug?: string;
}

export interface VerifyOtpRequest {
  phone_number: string;
  code: string;
}

export interface VerifyOtpResponse {
  message: string;
}

export interface RefreshResponse {
  message: string;
}

export interface LogoutResponse {
  message: string;
}

export interface AvatarUploadResponse {
  avatar_path: string;
}

export interface PhoneChangeTokenResponse {
  phone_change_token: string;
}

export interface RequestCurrentPhoneOtpResponse {
  message: string;
  otp_debug?: string;
}

export interface VerifyCurrentPhoneOtpResponse {
  phone_change_token: string;
}

export interface RequestNewPhoneOtpRequest {
  phone_change_token: string;
  new_phone_number: string;
}

export interface RequestNewPhoneOtpResponse {
  message: string;
  otp_debug?: string;
}

export interface VerifyNewPhoneOtpRequest {
  phone_change_token: string;
  new_phone_number: string;
  code: string;
}

export interface VerifyNewPhoneOtpResponse {
  message: string;
}

export interface DeviceWithSessionsResponse {
  devices: DeviceWithSessions[];
}

export interface RevokeSessionRequest {
  session_id: string;
}

export interface RevokeDeviceSessionsRequest {
  device_id: string;
}

export interface RevokeAllSessionsResponse {
  message: string;
}