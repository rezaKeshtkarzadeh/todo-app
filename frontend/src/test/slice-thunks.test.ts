import { describe, it, expect, vi, beforeEach } from "vitest";
import { configureStore } from "@reduxjs/toolkit";

// Mock lib/image first with factory functions
vi.mock("@/lib/image", () => ({
  validateImageFile: vi.fn(() => ({ valid: true })),
  compressImage: vi.fn(() => Promise.resolve(new File(["test"], "test.jpg", { type: "image/jpeg" }))),
  createImagePreview: vi.fn(() => Promise.resolve("data:image/jpeg;base64,test")),
}));

vi.mock("@/lib/api/tasks", () => ({
  tasksApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
  },
}));

vi.mock("@/lib/api/auth", () => ({
  authApi: {
    sendOtp: vi.fn(),
    verifyOtp: vi.fn(),
  },
}));

vi.mock("@/lib/api/security", () => ({
  securityApi: {
    listDevices: vi.fn(),
    revokeSession: vi.fn(),
  },
}));

vi.mock("@/lib/api/profile", () => ({
  profileApi: {
    uploadAvatar: vi.fn(),
  },
}));

// Import after mocks
import tasksReducer, { fetchTasks, createTask, updateTask, deleteTask } from "@/store/slices/tasksSlice";
import authReducer, { sendOtp, verifyOtp, checkAuth } from "@/store/slices/authSlice";
import securityReducer, { fetchDevices, revokeSession } from "@/store/slices/securitySlice";
import profileReducer, { uploadAvatar } from "@/store/slices/profileSlice";

import { tasksApi } from "@/lib/api/tasks";
import { authApi } from "@/lib/api/auth";
import { securityApi } from "@/lib/api/security";
import { profileApi } from "@/lib/api/profile";

describe("slice thunks state transitions", () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    vi.clearAllMocks();
    store = configureStore({
      reducer: {
        tasks: tasksReducer,
        auth: authReducer,
        security: securityReducer,
        profile: profileReducer,
      },
    });
  });

  describe("tasksSlice", () => {
    it("fetchTasks goes through idle -> loading -> succeeded", async () => {
      const mockTasks = [{ id: "1", title: "Test", is_done: false, created_at: "", updated_at: "" }];
      (tasksApi.list as vi.Mock).mockResolvedValue({ data: mockTasks });

      const initialState = store.getState().tasks;
      expect(initialState.status).toBe("idle");

      const promise = store.dispatch(fetchTasks());
      expect(store.getState().tasks.status).toBe("loading");

      await promise;
      const finalState = store.getState().tasks;
      expect(finalState.status).toBe("succeeded");
      expect(finalState.items).toEqual(mockTasks);
    });

    it("fetchTasks goes to error on failure", async () => {
      (tasksApi.list as vi.Mock).mockRejectedValue(new Error("Failed"));

      await store.dispatch(fetchTasks());
      const finalState = store.getState().tasks;
      expect(finalState.status).toBe("error");
      expect(finalState.error).toBeTruthy();
    });

    it("updateTask optimistic update rolls back on error", async () => {
      const mockTask = { id: "1", title: "Original", is_done: false, created_at: "", updated_at: "" };
      (tasksApi.list as vi.Mock).mockResolvedValue({ data: [mockTask] });
      await store.dispatch(fetchTasks());

      (tasksApi.update as vi.Mock).mockRejectedValue(new Error("Server error"));

      const promise = store.dispatch(updateTask({ id: "1", data: { is_done: true }, previousTask: mockTask }));
      expect(store.getState().tasks.items[0].is_done).toBe(true);

      await promise;
      const finalState = store.getState().tasks;
      expect(finalState.items[0].is_done).toBe(false); // rolled back
      expect(finalState.status).toBe("error");
    });

    it("deleteTask optimistic delete rolls back on error", async () => {
      const mockTask = { id: "1", title: "Test", is_done: false, created_at: "", updated_at: "" };
      (tasksApi.list as vi.Mock).mockResolvedValue({ data: [mockTask] });
      await store.dispatch(fetchTasks());

      (tasksApi.remove as vi.Mock).mockRejectedValue(new Error("Server error"));

      const promise = store.dispatch(deleteTask({ id: "1", previousTask: mockTask }));
      expect(store.getState().tasks.items).toHaveLength(0);

      await promise;
      const finalState = store.getState().tasks;
      expect(finalState.items).toHaveLength(1); // rolled back
      expect(finalState.status).toBe("error");
    });
  });

  describe("authSlice", () => {
    it("sendOtp goes through idle -> loading -> idle", async () => {
      (authApi.sendOtp as vi.Mock).mockResolvedValue({ data: { phoneNumber: "123", cooldown: 30 } });

      const promise = store.dispatch(sendOtp("1234567890"));
      expect(store.getState().auth.status).toBe("loading");

      await promise;
      expect(store.getState().auth.status).toBe("idle");
    });

    it("verifyOtp goes through idle -> loading -> idle", async () => {
      (authApi.verifyOtp as vi.Mock).mockResolvedValue({});

      const promise = store.dispatch(verifyOtp({ phoneNumber: "1234567890", code: "1234" }));
      expect(store.getState().auth.status).toBe("loading");

      await promise;
      expect(store.getState().auth.status).toBe("idle");
      expect(store.getState().auth.isAuthenticated).toBe(true);
    });
  });

  describe("securitySlice", () => {
    it("fetchDevices goes through idle -> loading -> succeeded", async () => {
      const mockDevices = [{ id: "1", name: "Device", sessions: [] }];
      (securityApi.listDevices as vi.Mock).mockResolvedValue({ data: { devices: mockDevices } });

      const promise = store.dispatch(fetchDevices());
      expect(store.getState().security.status).toBe("loading");

      await promise;
      expect(store.getState().security.status).toBe("succeeded");
    });
  });

  describe("profileSlice", () => {
    it("uploadAvatar goes through idle -> loading -> succeeded", async () => {
      (profileApi.uploadAvatar as vi.Mock).mockResolvedValue({ data: { avatar_path: "path/to/avatar" } });

      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      const promise = store.dispatch(uploadAvatar(file));
      expect(store.getState().profile.status).toBe("loading");

      await promise;
      expect(store.getState().profile.status).toBe("succeeded");
    });
  });
});