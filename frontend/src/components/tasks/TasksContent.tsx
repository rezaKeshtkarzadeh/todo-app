"use client";

import { useTranslations } from "next-intl";
import { useAppSelector, useAppDispatch } from "@/store/hooks";
import { fetchTasks } from "@/store/slices/tasksSlice";
import { useEffect } from "react";
import { TaskForm } from "@/components/tasks/TaskForm";
import { TaskList } from "@/components/tasks/TaskList";
import { Separator } from "@base-ui/react";

export function TasksContent() {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { items, status, error } = useAppSelector((state) => state.tasks);

  useEffect(() => {
    dispatch(fetchTasks());
  }, [dispatch]);

  return (
    <div className="container mx-auto py-8 px-4 space-y-2">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{t("tasks.title")}</h1>
      </div>

      <TaskForm />

      <Separator className={"w-full border rounded-full mb-4"} />

      <TaskList tasks={items} status={status} error={error} />
    </div>
  );
}