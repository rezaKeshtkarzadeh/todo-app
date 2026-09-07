import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

interface SettingsState {
  theme: "light" | "dark" | "system";
  locale: "en" | "fa";
}

const initialState: SettingsState = {
  theme: "system",
  locale: "en",
};

const settingsSlice = createSlice({
  name: "settings",
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<SettingsState["theme"]>) => {
      state.theme = action.payload;
    },
    setLocale: (state, action: PayloadAction<SettingsState["locale"]>) => {
      state.locale = action.payload;
    },
  },
});

export const { setTheme, setLocale } = settingsSlice.actions;
export default settingsSlice.reducer;