"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setTheme } from "@/store/slices/settingsSlice";

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme: setThemeNext } = useTheme();
  const dispatch = useAppDispatch();
  const reduxTheme = useAppSelector((state) => state.settings.theme);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleThemeChange = (newTheme: "light" | "dark" | "system") => {
    setThemeNext(newTheme);
    dispatch(setTheme(newTheme));
  };

  if (!mounted) {
    return <Button variant="ghost" size="icon" disabled><Sun className="h-4 w-4" /></Button>;
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => handleThemeChange(theme === "dark" ? "light" : "dark")}
      aria-label="Toggle theme"
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}