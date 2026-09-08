"use client";

import { useTranslations } from "next-intl";
import { Skeleton } from "@/components/ui/skeleton";
import { TaskItem } from "./TaskItem";
import type { Task } from "@/lib/api/tasks";

interface TaskListProps {
  tasks: Task[];
  status: "idle" | "loading" | "succeeded" | "error";
  error: string | null;
}

export function TaskList({ tasks, status, error }: TaskListProps) {
  const t = useTranslations();

  if (status === "loading") {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="text-center py-8 text-destructive">
        <p>{error || t("tasks.loadError")}</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">{t("tasks.noTasks")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <TaskItem key={task.id} task={task} />
      ))}
    </div>
  );
}