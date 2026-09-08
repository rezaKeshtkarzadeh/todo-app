"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SettingsContent() {
  const t = useTranslations();

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">{t("settings.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("settings.theme")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            {t("settings.light")} / {t("settings.dark")} / {t("settings.system")} - Coming in Phase 24
          </p>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>{t("settings.language")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            {t("settings.light")} / {t("settings.dark")} - Coming in Phase 24
          </p>
        </CardContent>
      </Card>
    </div>
  );
}