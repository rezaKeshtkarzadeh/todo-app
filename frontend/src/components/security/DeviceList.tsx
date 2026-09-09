"use client";

import { useTranslations } from "next-intl";
import { Skeleton } from "@/components/ui/skeleton";
import { DeviceCard } from "./DeviceCard";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { fetchDevices } from "@/store/slices/securitySlice";
import { useEffect } from "react";

export function DeviceList() {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { devices, status, error } = useAppSelector((state) => state.security);

  useEffect(() => {
    dispatch(fetchDevices());
  }, [dispatch]);

  if (status === "loading") {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="text-center py-8 text-destructive">
        <p>{error || t("security.loadError")}</p>
      </div>
    );
  }

  if (devices.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">{t("security.noDevices")}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {devices.map((device) => (
        <DeviceCard key={device.id} device={device} />
      ))}
    </div>
  );
}