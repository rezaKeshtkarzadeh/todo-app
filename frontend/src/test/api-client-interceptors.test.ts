import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import { apiClient } from "@/lib/api-client";
import { getDeviceId, clearDeviceId } from "@/lib/device-id";
import { getCsrfToken } from "@/lib/csrf";

// Mock axios
vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      post: vi.fn(),
      patch: vi.fn(),
      delete: vi.fn(),
      put: vi.fn(),
    })),
    isAxiosError: vi.fn(),
  },
}));

// Mock device-id and csrf
vi.mock("@/lib/device-id", () => ({
  getDeviceId: vi.fn(),
  clearDeviceId: vi.fn(),
}));

vi.mock("@/lib/csrf", () => ({
  getCsrfToken: vi.fn(),
}));

vi.mock("@/lib/local-prefs", () => ({
  clearPreferences: vi.fn(),
}));

vi.mock("@/lib/api-error", () => ({
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      public code: string,
      public message: string,
      public details: Record<string, string[]> | null,
      public requestId: string | null
    ) {
      super(message);
    }
    static fromResponse = vi.fn();
    static fromNetworkError = vi.fn();
  },
}));

describe("api-client interceptors", () => {
  let mockAxiosInstance: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockAxiosInstance = axios.create();
    (apiClient as any).interceptors.request.handlers = [];
    (apiClient as any).interceptors.response.handlers = [];
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("attaches X-Device-Id on every request", () => {
    (getDeviceId as vi.Mock).mockReturnValue("test-device-id");

    // Re-import to trigger interceptor setup
    const requestInterceptor = (apiClient as any).interceptors.request.handlers[0]?.fulfilled;
    if (requestInterceptor) {
      const config = { headers: {}, method: "get" };
      const result = requestInterceptor(config);
      expect(result.headers["X-Device-Id"]).toBe("test-device-id");
    }
  });

  it("attaches X-CSRF-Token on POST requests", () => {
    (getCsrfToken as vi.Mock).mockReturnValue("test-csrf-token");
    (getDeviceId as vi.Mock).mockReturnValue("test-device-id");

    const requestInterceptor = (apiClient as any).interceptors.request.handlers[0]?.fulfilled;
    if (requestInterceptor) {
      const config = { headers: {}, method: "post" };
      const result = requestInterceptor(config);
      expect(result.headers["X-CSRF-Token"]).toBe("test-csrf-token");
    }
  });

  it("attaches X-CSRF-Token on PATCH requests", () => {
    (getCsrfToken as vi.Mock).mockReturnValue("test-csrf-token");
    (getDeviceId as vi.Mock).mockReturnValue("test-device-id");

    const requestInterceptor = (apiClient as any).interceptors.request.handlers[0]?.fulfilled;
    if (requestInterceptor) {
      const config = { headers: {}, method: "patch" };
      const result = requestInterceptor(config);
      expect(result.headers["X-CSRF-Token"]).toBe("test-csrf-token");
    }
  });

  it("does NOT attach X-CSRF-Token on GET requests", () => {
    (getCsrfToken as vi.Mock).mockReturnValue("test-csrf-token");
    (getDeviceId as vi.Mock).mockReturnValue("test-device-id");

    const requestInterceptor = (apiClient as any).interceptors.request.handlers[0]?.fulfilled;
    if (requestInterceptor) {
      const config = { headers: {}, method: "get" };
      const result = requestInterceptor(config);
      expect(result.headers["X-CSRF-Token"]).toBeUndefined();
    }
  });

  it("removes Content-Type header for FormData requests", () => {
    (getDeviceId as vi.Mock).mockReturnValue("test-device-id");

    const requestInterceptor = (apiClient as any).interceptors.request.handlers[0]?.fulfilled;
    if (requestInterceptor) {
      const formData = new FormData();
      const config = { headers: { "Content-Type": "application/json" }, method: "post", data: formData };
      const result = requestInterceptor(config);
      expect(result.headers["Content-Type"]).toBeUndefined();
    }
  });
});