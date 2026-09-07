import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

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
});

export const { setDevices, setRevoking, setStatus, setError } = securitySlice.actions;
export default securitySlice.reducer;