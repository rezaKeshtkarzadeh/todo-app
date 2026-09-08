"use client";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { SettingsContent } from "./SettingsContent";

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}