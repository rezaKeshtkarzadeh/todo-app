import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { ApiError } from "@/lib/api-error";

interface AuthState {
  isAuthenticated: boolean;
  phoneNumber: string | null;
  currentSessionId: string | null;
  status: "idle" | "loading" | "error";
  error: ApiError | null;
}

const initialState: AuthState = {
  isAuthenticated: false,
  phoneNumber: null,
  currentSessionId: null,
  status: "idle",
  error: null,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setAuthenticated: (state, action: PayloadAction<{ phoneNumber: string; sessionId: string }>) => {
      state.isAuthenticated = true;
      state.phoneNumber = action.payload.phoneNumber;
      state.currentSessionId = action.payload.sessionId;
      state.status = "idle";
      state.error = null;
    },
    setUnauthenticated: (state) => {
      state.isAuthenticated = false;
      state.phoneNumber = null;
      state.currentSessionId = null;
      state.status = "idle";
      state.error = null;
    },
    setStatus: (state, action: PayloadAction<AuthState["status"]>) => {
      state.status = action.payload;
    },
    setError: (state, action: PayloadAction<ApiError | null>) => {
      state.error = action.payload;
      state.status = "error";
    },
  },
});

export const { setAuthenticated, setUnauthenticated, setStatus, setError } = authSlice.actions;
export default authSlice.reducer;