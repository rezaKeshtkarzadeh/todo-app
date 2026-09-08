"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Pencil, Trash2 } from "lucide-react";
import { useAppDispatch } from "@/store/hooks";
import { updateTask, deleteTask } from "@/store/slices/tasksSlice";
import type { Task } from "@/lib/api/tasks";

interface TaskItemProps {
  task: Task;
}

export function TaskItem({ task }: TaskItemProps) {
  const t = useTranslations();
  const dispatch = useAppDispatch();

  const handleToggle = () => {
    const previousTask = { ...task };
    dispatch(updateTask({ id: task.id, data: { is_done: !task.is_done }, previousTask }));
  };

  const handleDelete = () => {
    dispatch(deleteTask({ id: task.id, previousTask: task }));
  };

  const handleEdit = (newTitle: string) => {
    if (newTitle.trim() && newTitle !== task.title) {
      const previousTask = { ...task };
      dispatch(updateTask({ id: task.id, data: { title: newTitle.trim() }, previousTask }));
    }
  };

  const [editTitle, setEditTitle] = useState(task.title);
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="flex items-center gap-3 p-4 bg-card rounded-lg border border-border">
      <Checkbox
        checked={task.is_done}
        onCheckedChange={handleToggle}
        aria-label={task.is_done ? t("tasks.markIncomplete") : t("tasks.markComplete")}
      />
      <span className={`flex-1 text-left ${task.is_done ? "line-through text-muted-foreground" : ""}`}>
        {task.title}
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => {
            setEditTitle(task.title);
            setIsEditing(true);
          }}
          aria-label={t("tasks.edit")}
        >
          <Pencil className="h-4 w-4" />
        </Button>
        <AlertDialog>
          <AlertDialogTrigger>
            <Button variant="ghost" size="icon" aria-label={t("tasks.delete")}>
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{t("tasks.confirmDelete")}</AlertDialogTitle>
              <AlertDialogDescription>
                {t("tasks.deleteDescription", { title: task.title })}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <div className="flex gap-2 justify-end">
              <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
              <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                {t("common.delete")}
              </AlertDialogAction>
            </div>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      <Dialog open={isEditing} onOpenChange={setIsEditing}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("tasks.editTask")}</DialogTitle>
            <DialogDescription>{t("tasks.editDescription")}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder={t("tasks.taskTitle")}
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                {t("common.cancel")}
              </Button>
              <Button onClick={() => { handleEdit(editTitle); setIsEditing(false); }}>
                {t("common.save")}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}