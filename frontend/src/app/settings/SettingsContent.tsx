"use client";

import { useTranslations } from "next-intl";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setTheme, setLocale } from "@/store/slices/settingsSlice";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Separator } from "@/components/ui/separator";
import { hydrateSettings } from "@/store/slices/settingsSlice";
import { useEffect } from "react";

export function SettingsContent() {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { theme, locale, hydrated } = useAppSelector((state) => state.settings);

  useEffect(() => {
    if (!hydrated) {
      dispatch(hydrateSettings());
    }
  }, [dispatch, hydrated]);

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">{t("settings.title")}</h1>

      <Card>
        <CardHeader>
          <CardTitle>{t("settings.theme")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioGroup value={theme} onValueChange={(value) => dispatch(setTheme(value as "light" | "dark" | "system"))}>
            <div className="flex items-center space-x-4">
              <RadioGroupItem value="light" className="translate-y-0.5" id="theme-light" />
              <Label htmlFor="theme-light">{t("settings.light")}</Label>
            </div>
            <div className="flex items-center space-x-4">
              <RadioGroupItem value="dark" className="translate-y-0.5" id="theme-dark" />
              <Label htmlFor="theme-dark">{t("settings.dark")}</Label>
            </div>
            <div className="flex items-center space-x-4">
              <RadioGroupItem value="system" className="translate-y-0.5" id="theme-system" />
              <Label htmlFor="theme-system">{t("settings.system")}</Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>{t("settings.language")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <RadioGroup value={locale} onValueChange={(value) => dispatch(setLocale(value as "en" | "fa"))}>
            <div className="flex items-center space-x-4">
              <RadioGroupItem value="en" className="translate-y-0.5" id="locale-en" />
              <Label htmlFor="locale-en" className="font-roboto">{t("settings.english")}</Label>
            </div>
            <div className="flex items-center space-x-4">
              <RadioGroupItem value="fa" className="translate-y-0.5" id="locale-fa" />
              <Label htmlFor="locale-fa" className="font-vazir">{t("settings.persian")}</Label>
            </div>
          </RadioGroup>
        </CardContent>
      </Card>
    </div>
  );
}