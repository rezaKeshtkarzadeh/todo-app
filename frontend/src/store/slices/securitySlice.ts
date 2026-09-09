import { createSlice, type PayloadAction, createAsyncThunk } from "@reduxjs/toolkit";
import { securityApi } from "@/lib/api/security";
import { useAuthCleanup } from "@/lib/auth-cleanup";

interface Session {
  id: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string;
  is_current: boolean;
}

interface DeviceWithSessions {
  id: string;
  name: string | null;
  user_agent: string | null;
  created_at: string;
  last_seen_at: string | null;
  sessions: Session[];
}

interface SecurityState {
  devices: DeviceWithSessions[];
  status: "idle" | "loading" | "succeeded" | "error";
  error: string | null;
  revoking: string | null;
}

const initialState: SecurityState = {
  devices: [],
  status: "idle",
  error: null,
  revoking: null,
};

export const fetchDevices = createAsyncThunk(
  "security/fetchDevices",
  async (_, { rejectWithValue }) => {
    try {
      const response = await securityApi.listDevices();
      return response.data.devices;
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to fetch devices");
    }
  }
);

export const revokeSession = createAsyncThunk(
  "security/revokeSession",
  async (sessionId: string, { rejectWithValue }) => {
    try {
      await securityApi.revokeSession(sessionId);
      return sessionId;
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to revoke session");
    }
  }
);

export const revokeDeviceSessions = createAsyncThunk(
  "security/revokeDeviceSessions",
  async (deviceId: string, { rejectWithValue }) => {
    try {
      await securityApi.revokeDeviceSessions(deviceId);
      return deviceId;
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to revoke device sessions");
    }
  }
);

export const revokeAllSessions = createAsyncThunk(
  "security/revokeAllSessions",
  async (_, { rejectWithValue, dispatch }) => {
    try {
      await securityApi.revokeAllSessions();
      // Run cleanup routine - will be handled by the component
      return true;
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to revoke all sessions");
    }
  }
);

const securitySlice = createSlice({
  name: "security",
  initialState,
  reducers: {
    setDevices: (state, action: PayloadAction<DeviceWithSessions[]>) => {
      state.devices = action.payload;
      state.status = "succeeded";
      state.error = null;
    },
    setRevoking: (state, action: PayloadAction<string | null>) => {
      state.revoking = action.payload;
    },
    setStatus: (state, action: PayloadAction<SecurityState["status"]>) => {
      state.status = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.status = "error";
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDevices.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchDevices.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.devices = action.payload;
        state.error = null;
      })
      .addCase(fetchDevices.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
      })
      .addCase(revokeSession.pending, (state, action) => {
        state.revoking = action.meta.arg;
        state.error = null;
      })
      .addCase(revokeSession.fulfilled, (state, action) => {
        state.revoking = null;
        // Remove the revoked session from the device
        state.devices = state.devices.map((device) => ({
          ...device,
          sessions: device.sessions.filter((s) => s.id !== action.payload),
        })).filter((device) => device.sessions.length > 0);
        state.error = null;
      })
      .addCase(revokeSession.rejected, (state, action) => {
        state.revoking = null;
        state.error = action.payload as string;
      })
      .addCase(revokeDeviceSessions.pending, (state, action) => {
        state.revoking = action.meta.arg;
        state.error = null;
      })
      .addCase(revokeDeviceSessions.fulfilled, (state, action) => {
        state.revoking = null;
        // Remove the device entirely
        state.devices = state.devices.filter((d) => d.id !== action.payload);
        state.error = null;
      })
      .addCase(revokeDeviceSessions.rejected, (state, action) => {
        state.revoking = null;
        state.error = action.payload as string;
      })
      .addCase(revokeAllSessions.pending, (state) => {
        state.revoking = "all";
        state.error = null;
      })
      .addCase(revokeAllSessions.fulfilled, (state) => {
        state.revoking = null;
        state.devices = [];
        state.error = null;
      })
      .addCase(revokeAllSessions.rejected, (state, action) => {
        state.revoking = null;
        state.error = action.payload as string;
      });
  },
});

export const { setDevices, setRevoking, setStatus, setError } = securitySlice.actions;
export default securitySlice.reducer;