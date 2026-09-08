"use client";

import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { TasksContent } from "./TasksContent";

export default function TasksPage() {
  return (
    <ProtectedRoute>
      <TasksContent />
    </ProtectedRoute>
  );
}