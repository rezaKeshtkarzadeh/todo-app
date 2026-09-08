"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function SecurityContent() {
  const t = useTranslations();

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">{t("security.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("security.devices")} & {t("security.sessions")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            {t("security.revokeSession")}, {t("security.revokeAllSessions")}, {t("security.globalLogout")} - Coming in Phase 27
          </p>
        </CardContent>
      </Card>
    </div>
  );
}