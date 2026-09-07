export const errorCodeToMessageKey: Record<string, string> = {
  AUTH_INVALID_OTP: "auth.invalidOtp",
  AUTH_OTP_EXPIRED: "auth.otpExpired",
  AUTH_OTP_RATE_LIMITED: "auth.rateLimited",
  AUTH_OTP_MAX_ATTEMPTS: "auth.maxAttempts",
  AUTH_UNAUTHENTICATED: "auth.unauthenticated",
  AUTH_SESSION_REVOKED: "auth.sessionRevoked",
  AUTH_REFRESH_FAILED: "auth.refreshFailed",
  AUTH_REFRESH_TOKEN_REUSED: "auth.refreshTokenReused",
  CSRF_TOKEN_MISSING: "auth.csrfMissing",
  CSRF_TOKEN_INVALID: "auth.csrfInvalid",
  DEVICE_ID_MISSING: "auth.deviceIdMissing",
  DEVICE_ID_INVALID: "auth.deviceIdInvalid",
  DEVICE_NOT_FOUND: "security.deviceNotFound",
  SESSION_NOT_FOUND: "security.sessionNotFound",
  PROFILE_PHONE_CHANGE_TOKEN_INVALID: "profile.phoneChangeTokenInvalid",
  PROFILE_PHONE_ALREADY_IN_USE: "profile.phoneAlreadyInUse",
  PROFILE_PHONE_SAME_AS_CURRENT: "profile.phoneSameAsCurrent",
  PROFILE_AVATAR_INVALID_TYPE: "profile.avatarInvalidType",
  PROFILE_AVATAR_TOO_LARGE: "profile.avatarTooLarge",
  TASK_NOT_FOUND: "tasks.notFound",
  TASK_TITLE_INVALID: "tasks.titleInvalid",
  VALIDATION_ERROR: "common.validationError",
  RATE_LIMITED: "common.rateLimited",
  NOT_FOUND: "common.notFound",
  INTERNAL_ERROR: "common.internalError",
  NETWORK_ERROR: "common.networkError",
  UNKNOWN_ERROR: "common.unknownError",
};

export function getErrorMessageKey(code: string): string {
  return errorCodeToMessageKey[code] || "common.unknownError";
}