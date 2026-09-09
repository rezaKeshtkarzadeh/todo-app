"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { format } from "date-fns";
import { faIR } from "date-fns/locale";
import { ChevronDown, Monitor, Smartphone, Tablet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { revokeDeviceSessions } from "@/store/slices/securitySlice";
import { SessionRow } from "./SessionRow";

interface DeviceCardProps {
  device: {
    id: string;
    name: string | null;
    user_agent: string | null;
    created_at: string;
    last_seen_at: string | null;
    sessions: Array<{
      id: string;
      created_at: string;
      last_used_at: string | null;
      expires_at: string;
      is_current: boolean;
    }>;
  };
}

export function DeviceCard({ device }: DeviceCardProps) {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { revoking } = useAppSelector((state) => state.security);
  const isRevoking = revoking === device.id;
  const [isOpen, setIsOpen] = useState(true);

  const formatDate = (dateStr: string) => {
    const locale = document.documentElement.lang === "fa" ? faIR : undefined;
    return format(new Date(dateStr), "PPpp", { locale });
  };

  const getDeviceIcon = (userAgent: string | null) => {
    if (!userAgent) return <Monitor className="h-5 w-5" />;
    const ua = userAgent.toLowerCase();
    if (ua.includes("mobile") || ua.includes("android") || ua.includes("iphone")) return <Smartphone className="h-5 w-5" />;
    if (ua.includes("tablet") || ua.includes("ipad")) return <Tablet className="h-5 w-5" />;
    return <Monitor className="h-5 w-5" />;
  };

  const handleRevokeAll = () => {
    dispatch(revokeDeviceSessions(device.id));
  };

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between py-3 px-4 cursor-pointer" onClick={() => setIsOpen(!isOpen)}>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-muted">{getDeviceIcon(device.user_agent)}</div>
          <div>
            <h3 className="font-medium">{device.name || t("security.unnamedDevice")}</h3>
            <p className="text-sm text-muted-foreground">{formatDate(device.created_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{device.sessions.length} {t("security.sessions")}</Badge>
          <ChevronDown className={`h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
        </div>
      </CardHeader>
      {isOpen && (
        <CardContent className="pt-0">
          <div className="space-y-2 pb-4 border-b border-border/50">
            {device.sessions.map((session) => (
              <SessionRow key={session.id} session={session} deviceId={device.id} />
            ))}
          </div>
          {device.sessions.length > 1 && (
            <div className="pt-4 flex justify-end">
              <AlertDialog>
                <AlertDialogTrigger >
                  <Button variant="outline" size="sm" disabled={isRevoking} onClick={handleRevokeAll}>
                    {isRevoking ? (
                      <>
                        <svg className="mr-1 h-3 w-3 animate-spin" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" /></svg>
                        {t("common.loading")}
                      </>
                    ) : (
                      t("security.revokeAllDeviceSessions")
                    )}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{t("security.revokeAllDeviceSessionsConfirm")}</AlertDialogTitle>
                    <AlertDialogDescription>{t("security.revokeAllDeviceSessionsDescription")}</AlertDialogDescription>
                  </AlertDialogHeader>
                  <div className="flex gap-2 justify-end">
                    <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
                    <AlertDialogAction onClick={handleRevokeAll} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                      {t("security.revokeAllDeviceSessions")}
                    </AlertDialogAction>
                  </div>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}