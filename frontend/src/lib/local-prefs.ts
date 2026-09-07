const THEME_KEY = "theme";
const LOCALE_KEY = "locale";

type Theme = "light" | "dark" | "system";
type Locale = "en" | "fa";

export function getTheme(): Theme {
  if (typeof window === "undefined") return "system";
  return (localStorage.getItem(THEME_KEY) as Theme) || "system";
}

export function setTheme(theme: Theme): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(THEME_KEY, theme);
  }
}

export function getLocale(): Locale {
  if (typeof window === "undefined") return "en";
  return (localStorage.getItem(LOCALE_KEY) as Locale) || "en";
}

export function setLocale(locale: Locale): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(LOCALE_KEY, locale);
  }
}

export function clearPreferences(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(THEME_KEY);
    localStorage.removeItem(LOCALE_KEY);
  }
}