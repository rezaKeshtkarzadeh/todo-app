"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ProfileContent() {
  const t = useTranslations();

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">{t("profile.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("profile.avatar")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            {t("profile.changeAvatar")} - Coming in Phase 25
          </p>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>{t("profile.phoneNumber")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            {t("profile.changePhone")} - Coming in Phase 26
          </p>
        </CardContent>
      </Card>
    </div>
  );
}