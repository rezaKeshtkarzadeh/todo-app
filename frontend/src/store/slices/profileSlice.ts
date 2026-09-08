import { createSlice, type PayloadAction, createAsyncThunk } from "@reduxjs/toolkit";
import { profileApi } from "@/lib/api/profile";
import { validateImageFile, compressImage, createImagePreview } from "@/lib/image";

interface ProfileState {
  avatarUrl: string | null;
  phoneChangeStep: "idle" | "currentRequested" | "currentVerified" | "newRequested";
  status: "idle" | "loading" | "succeeded" | "error";
  error: string | null;
  uploadProgress: number;
}

const initialState: ProfileState = {
  avatarUrl: null,
  phoneChangeStep: "idle",
  status: "idle",
  error: null,
  uploadProgress: 0,
};

export const uploadAvatar = createAsyncThunk(
  "profile/uploadAvatar",
  async (file: File, { rejectWithValue }) => {
    try {
      // Client-side validation
      const validation = validateImageFile(file);
      if (!validation.valid) {
        return rejectWithValue(validation.error);
      }

      // Compress image
      const compressedFile = await compressImage(file);

      // Create preview
      const previewUrl = await createImagePreview(compressedFile);

      // Upload
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
      });
  },
});

export const { setAvatarUrl, setPhoneChangeStep, setStatus, setError, setUploadProgress, clearUploadProgress } = profileSlice.actions;
export default profileSlice.reducer;