"use client";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { ProfileContent } from "./ProfileContent";

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}