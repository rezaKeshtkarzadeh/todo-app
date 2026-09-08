"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAppDispatch } from "@/store/hooks";
import { createTask } from "@/store/slices/tasksSlice";

const taskSchema = z.object({
  title: z.string().min(1, { message: "tasks.titleRequired" }).max(200, { message: "tasks.titleTooLong" }),
});

type TaskFormData = z.infer<typeof taskSchema>;

export function TaskForm() {
  const t = useTranslations();
  const dispatch = useAppDispatch();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
  });

  const onSubmit = (data: TaskFormData) => {
    dispatch(createTask(data)).then(() => {
      reset();
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex gap-2">
      <div className="flex-1 space-y-1.5">
        <Label htmlFor="title" className="sr-only">
          {t("tasks.taskTitle")}
        </Label>
        <Input
          id="title"
          placeholder={t("tasks.taskTitle")}
          {...register("title")}
          disabled={isSubmitting}
        />
        {errors.title && (
          <p className="text-sm text-destructive" role="alert">
            {t(errors.title.message as string)}
          </p>
        )}
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t("common.loading") : t("tasks.addTask")}
      </Button>
    </form>
  );
}