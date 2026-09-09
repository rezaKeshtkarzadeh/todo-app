"use client";

import { useTranslations } from "next-intl";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchDevices } from "@/store/slices/securitySlice";
import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DeviceList } from "@/components/security/DeviceList";
import { RevokeAllDialog } from "@/components/security/RevokeAllDialog";
import { useAuthCleanup } from "@/lib/auth-cleanup";
import { useRouter } from "next/navigation";

export function SecurityContent() {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const router = useRouter();
  const cleanup = useAuthCleanup();

  useEffect(() => {
    dispatch(fetchDevices());
  }, [dispatch]);

  const handleGlobalLogout = () => {
    cleanup();
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">{t("security.title")}</h1>
        <RevokeAllDialog onSuccess={handleGlobalLogout} />
      </div>

      <DeviceList />
    </div>
  );
}