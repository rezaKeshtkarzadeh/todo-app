import { createSlice, type PayloadAction, createAsyncThunk } from "@reduxjs/toolkit";
import { getTheme, getLocale, setTheme as setThemeLocal, setLocale as setLocaleLocal } from "@/lib/local-prefs";

interface SettingsState {
  theme: "light" | "dark" | "system";
  locale: "en" | "fa";
  hydrated: boolean;
}

const initialState: SettingsState = {
  theme: "system",
  locale: "en",
  hydrated: false,
};

export const hydrateSettings = createAsyncThunk(
  "settings/hydrate",
  async () => {
    const theme = getTheme();
    const locale = getLocale();
    return { theme, locale };
  }
);

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<SettingsState["theme"]>) => {
      state.theme = action.payload;
      setThemeLocal(action.payload);
    },
    setLocale: (state, action: PayloadAction<SettingsState["locale"]>) => {
      state.locale = action.payload;
      setLocaleLocal(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder.addCase(hydrateSettings.fulfilled, (state, action) => {
      state.theme = action.payload.theme;
      state.locale = action.payload.locale;
      state.hydrated = true;
    });
  },
});

export const { setTheme, setLocale } = settingsSlice.actions;
export default settingsSlice.reducer;