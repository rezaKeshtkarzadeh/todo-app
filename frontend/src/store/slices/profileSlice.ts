import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

interface ProfileState {
  avatarUrl: string | null;
  phoneChangeStep: "idle" | "currentRequested" | "currentVerified" | "newRequested";
  status: "idle" | "loading" | "error";
  error: string | null;
}

const initialState: ProfileState = {
  avatarUrl: null,
  phoneChangeStep: "idle",
  status: "idle",
  error: null,
};

const profileSlice = createSlice({
  name: "profile",
  initialState,
  reducers: {
    setAvatarUrl: (state, action: PayloadAction<string | null>) => {
      state.avatarUrl = action.payload;
    },
    setPhoneChangeStep: (state, action: PayloadAction<ProfileState["phoneChangeStep"]>) => {
      state.phoneChangeStep = action.payload;
    },
    setStatus: (state, action: PayloadAction<ProfileState["status"]>) => {
      state.status = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
      state.status = "error";
    },
  },
});

export const { setAvatarUrl, setPhoneChangeStep, setStatus, setError } = profileSlice.actions;
export default profileSlice.reducer;