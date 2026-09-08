"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function TasksContent() {
  const t = useTranslations();

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{t("tasks.title")}</h1>
        <p className="text-muted-foreground mt-1">{t("tasks.addTask")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("tasks.noTasks")}</CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <p className="text-muted-foreground">{t("tasks.noTasks")}</p>
        </CardContent>
      </Card>
    </div>
  );
}