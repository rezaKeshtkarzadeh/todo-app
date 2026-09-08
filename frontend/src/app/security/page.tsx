"use client";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { SecurityContent } from "./SecurityContent";

export default function SecurityPage() {
  return (
    <ProtectedRoute>
      <SecurityContent />
    </ProtectedRoute>
  );
}