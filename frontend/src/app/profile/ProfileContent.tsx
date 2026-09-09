"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AvatarUploader } from "@/components/profile/AvatarUploader";
import { PhoneChangeWizard } from "@/components/profile/PhoneChangeWizard";
import { Separator } from "@/components/ui/separator";

export function ProfileContent() {
  const t = useTranslations();

  return (
    <div className="container mx-auto py-8 px-4 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">{t("profile.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("profile.avatar")}</CardTitle>
        </CardHeader>
        <CardContent>
          <AvatarUploader />
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>{t("profile.phoneNumber")}</CardTitle>
        </CardHeader>
        <CardContent>
          <PhoneChangeWizard />
        </CardContent>
      </Card>
    </div>
  );
}