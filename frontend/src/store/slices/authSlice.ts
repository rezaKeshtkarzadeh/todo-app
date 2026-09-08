import {
  createSlice,
  type PayloadAction,
  createAsyncThunk,
} from "@reduxjs/toolkit";
import type { ApiError } from "@/lib/api-error";
import { authApi } from "@/lib/api/auth";
import { tasksApi } from "@/lib/api/tasks";

interface AuthState {
  isAuthenticated: boolean;
  phoneNumber: string | null;
  currentSessionId: string | null;
  status: "idle" | "loading" | "error";
  error: ApiError | null;
  sendOtpCooldown: number;
  otpDebug?: string;
}

const initialState: AuthState = {
  isAuthenticated: false,
  phoneNumber: null,
  currentSessionId: null,
  status: "idle",
  error: null,
  sendOtpCooldown: 0,
  otpDebug: undefined,
};

export const sendOtp = createAsyncThunk(
  "auth/sendOtp",
  async (phoneNumber: string, { rejectWithValue }) => {
    try {
      const response = await authApi.sendOtp({ phone_number: phoneNumber });
      return { phoneNumber, cooldown: 30, otpDebug: response.data.otp_debug };
    } catch (err) {
      const apiError = err as ApiError;
      return rejectWithValue(apiError);
    }
  },
);

export const verifyOtp = createAsyncThunk(
  "auth/verifyOtp",
  async (
    { phoneNumber, code }: { phoneNumber: string; code: string },
    { rejectWithValue },
  ) => {
    try {
      await authApi.verifyOtp({ phone_number: phoneNumber, code });
      return { phoneNumber };
    } catch (err) {
      const apiError = err as ApiError;
      return rejectWithValue(apiError);
    }
  },
);

export const logout = createAsyncThunk(
  "auth/logout",
  async (_, { rejectWithValue }) => {
    try {
      await authApi.logout();
    } catch (err) {
      const apiError = err as ApiError;
      return rejectWithValue(apiError);
    }
  },
);

export const checkAuth = createAsyncThunk(
  "auth/checkAuth",
  async (_, { rejectWithValue }) => {
    try {
      await tasksApi.list();
      return { authenticated: true };
    } catch (err) {
      const apiError = err as ApiError;
      if (apiError.status === 401 || apiError.code === "AUTH_UNAUTHENTICATED") {
        return { authenticated: false };
      }
      return rejectWithValue(apiError);
    }
  },
);

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setAuthenticated: (
      state,
      action: PayloadAction<{ phoneNumber: string; sessionId: string }>,
    ) => {
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
      state.otpDebug = undefined;
    },
    setStatus: (state, action: PayloadAction<AuthState["status"]>) => {
      state.status = action.payload;
    },
    setError: (state, action: PayloadAction<ApiError | null>) => {
      state.error = action.payload;
      state.status = "error";
    },
    setSendOtpCooldown: (state, action: PayloadAction<number>) => {
      state.sendOtpCooldown = action.payload;
    },
    decrementCooldown: (state) => {
      if (state.sendOtpCooldown > 0) {
        state.sendOtpCooldown -= 1;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendOtp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(sendOtp.fulfilled, (state, action) => {
        state.status = "idle";
        state.phoneNumber = action.payload.phoneNumber;
        state.sendOtpCooldown = action.payload.cooldown;
        state.otpDebug = action.payload.otpDebug;
      })
      .addCase(sendOtp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as ApiError;
      })
      .addCase(verifyOtp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(verifyOtp.fulfilled, (state, action) => {
        state.status = "idle";
        state.isAuthenticated = true;
        state.phoneNumber = action.payload.phoneNumber;
        state.otpDebug = undefined;
      })
      .addCase(verifyOtp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as ApiError;
      })
      .addCase(logout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.phoneNumber = null;
        state.currentSessionId = null;
        state.status = "idle";
        state.error = null;
        state.otpDebug = undefined;
      })
      .addCase(checkAuth.fulfilled, (state, action) => {
        state.isAuthenticated = action.payload.authenticated;
        state.status = "idle";
      })
      .addCase(checkAuth.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as ApiError;
      });
  },
});

export const {
  setAuthenticated,
  setUnauthenticated,
  setStatus,
  setError,
  setSendOtpCooldown,
  decrementCooldown,
} = authSlice.actions;
export default authSlice.reducer;
