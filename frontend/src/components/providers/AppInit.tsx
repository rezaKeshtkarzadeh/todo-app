"use client";

import { useEffect } from "react";
import { apiClient } from "@/lib/api-client";

export function AppInit({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    apiClient.get("/auth/csrf-token").catch(() => {
      // Ignore CSRF initialization errors during app startup
      // The endpoint may fail if backend is not reachable, but we don't want to block the UI
    });
  }, []);

  return <>{children}</>;
}