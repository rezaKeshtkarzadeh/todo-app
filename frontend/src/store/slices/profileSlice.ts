import { createSlice, type PayloadAction, createAsyncThunk } from "@reduxjs/toolkit";
import { profileApi } from "@/lib/api/profile";
import { validateImageFile, compressImage, createImagePreview } from "@/lib/image";

interface ProfileState {
  avatarUrl: string | null;
  phoneChangeStep: "idle" | "currentRequested" | "currentVerified" | "newRequested";
  status: "idle" | "loading" | "succeeded" | "error";
  error: string | null;
  uploadProgress: number;
  phoneChangeToken: string | null;
  phoneChangeNewNumber: string | null;
}

const initialState: ProfileState = {
  avatarUrl: null,
  phoneChangeStep: "idle",
  status: "idle",
  error: null,
  uploadProgress: 0,
  phoneChangeToken: null,
  phoneChangeNewNumber: null,
};

export const uploadAvatar = createAsyncThunk(
  "profile/uploadAvatar",
  async (file: File, { rejectWithValue }) => {
    try {
      const validation = validateImageFile(file);
      if (!validation.valid) {
        return rejectWithValue(validation.error);
      }

      const compressedFile = await compressImage(file);
      const previewUrl = await createImagePreview(compressedFile);

      const formData = new FormData();
      formData.append("avatar", compressedFile);

      const response = await profileApi.uploadAvatar(formData);

      return { avatarUrl: response.data.avatar_path, previewUrl };
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to upload avatar");
    }
  }
);

export const requestCurrentPhoneOtp = createAsyncThunk(
  "profile/requestCurrentPhoneOtp",
  async (_, { rejectWithValue }) => {
    try {
      const response = await profileApi.requestCurrentPhoneOtp();
      return { otpDebug: response.data.otp_debug };
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to request OTP");
    }
  }
);

export const verifyCurrentPhoneOtp = createAsyncThunk(
  "profile/verifyCurrentPhoneOtp",
  async (code: string, { rejectWithValue }) => {
    try {
      const response = await profileApi.verifyCurrentPhoneOtp(code);
      return { phoneChangeToken: response.data.phone_change_token };
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to verify OTP");
    }
  }
);

export const requestNewPhoneOtp = createAsyncThunk(
  "profile/requestNewPhoneOtp",
  async (newPhoneNumber: string, { rejectWithValue, getState }) => {
    try {
      const state = getState() as { profile: ProfileState };
      const phoneChangeToken = state.profile.phoneChangeToken;
      if (!phoneChangeToken) {
        return rejectWithValue("PROFILE_PHONE_CHANGE_TOKEN_INVALID");
      }
      const response = await profileApi.requestNewPhoneOtp({ phone_change_token: phoneChangeToken, new_phone_number: newPhoneNumber });
      return { newPhoneNumber, otpDebug: response.data.otp_debug };
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to request OTP for new number");
    }
  }
);

export const verifyNewPhoneOtp = createAsyncThunk(
  "profile/verifyNewPhoneOtp",
  async (code: string, { rejectWithValue, getState }) => {
    try {
      const state = getState() as { profile: ProfileState };
      const phoneChangeToken = state.profile.phoneChangeToken;
      const newPhoneNumber = state.profile.phoneChangeNewNumber;
      if (!phoneChangeToken || !newPhoneNumber) {
        return rejectWithValue("PROFILE_PHONE_CHANGE_TOKEN_INVALID");
      }
      await profileApi.verifyNewPhoneOtp({ phone_change_token: phoneChangeToken, new_phone_number: newPhoneNumber, code });
      return { newPhoneNumber };
    } catch (err) {
      const apiError = err as { code?: string; message?: string };
      return rejectWithValue(apiError.code || apiError.message || "Failed to verify new OTP");
    }
  }
);

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
    setUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
    clearUploadProgress: (state) => {
      state.uploadProgress = 0;
    },
    setPhoneChangeToken: (state, action: PayloadAction<string | null>) => {
      state.phoneChangeToken = action.payload;
    },
    setPhoneChangeNewNumber: (state, action: PayloadAction<string | null>) => {
      state.phoneChangeNewNumber = action.payload;
    },
    resetPhoneChange: (state) => {
      state.phoneChangeStep = "idle";
      state.phoneChangeToken = null;
      state.phoneChangeNewNumber = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadAvatar.pending, (state) => {
        state.status = "loading";
        state.error = null;
        state.uploadProgress = 0;
      })
      .addCase(uploadAvatar.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.avatarUrl = action.payload.avatarUrl;
        state.error = null;
        state.uploadProgress = 100;
      })
      .addCase(uploadAvatar.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
        state.uploadProgress = 0;
      })
      .addCase(requestCurrentPhoneOtp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(requestCurrentPhoneOtp.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.phoneChangeStep = "currentRequested";
        state.error = null;
        // phoneChangeToken is set by verifyCurrentPhoneOtp, not here
      })
      .addCase(requestCurrentPhoneOtp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
      })
      .addCase(verifyCurrentPhoneOtp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(verifyCurrentPhoneOtp.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.phoneChangeStep = "currentVerified";
        state.phoneChangeToken = action.payload.phoneChangeToken;
        state.error = null;
      })
      .addCase(verifyCurrentPhoneOtp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
      })
      .addCase(requestNewPhoneOtp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(requestNewPhoneOtp.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.phoneChangeStep = "newRequested";
        state.phoneChangeNewNumber = action.payload.newPhoneNumber;
        state.error = null;
      })
      .addCase(requestNewPhoneOtp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
      })
      .addCase(verifyNewPhoneOtp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(verifyNewPhoneOtp.fulfilled, (state) => {
        state.status = "succeeded";
        state.phoneChangeStep = "idle";
        state.phoneChangeToken = null;
        state.phoneChangeNewNumber = null;
        state.error = null;
      })
      .addCase(verifyNewPhoneOtp.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload as string;
        if ((action.payload as string) === "PROFILE_PHONE_CHANGE_TOKEN_INVALID") {
          state.phoneChangeStep = "idle";
          state.phoneChangeToken = null;
          state.phoneChangeNewNumber = null;
        }
      });
  },
});

export const { setAvatarUrl, setPhoneChangeStep, setStatus, setError, setUploadProgress, clearUploadProgress, setPhoneChangeToken, setPhoneChangeNewNumber, resetPhoneChange } = profileSlice.actions;
export default profileSlice.reducer;