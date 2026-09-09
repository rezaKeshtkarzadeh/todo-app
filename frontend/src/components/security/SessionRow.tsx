"use client";

import { useTranslations } from "next-intl";
import { format } from "date-fns";
import { faIR } from "date-fns/locale";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { revokeSession } from "@/store/slices/securitySlice";
import { Clock, X } from "lucide-react";

interface SessionRowProps {
  session: {
    id: string;
    created_at: string;
    last_used_at: string | null;
    expires_at: string;
    is_current: boolean;
  };
  deviceId: string;
}

export function SessionRow({ session, deviceId }: SessionRowProps) {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { revoking } = useAppSelector((state) => state.security);
  const isRevoking = revoking === session.id;

  const formatDate = (dateStr: string) => {
    const locale = document.documentElement.lang === "fa" ? faIR : undefined;
    return format(new Date(dateStr), "PPpp", { locale });
  };

  const handleRevoke = () => {
    dispatch(revokeSession(session.id));
  };

  return (
    <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border border-border/50">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <div className="text-sm">
            <p className="font-medium">{t("security.created")} {formatDate(session.created_at)}</p>
            {session.last_used_at && (
              <p className="text-xs text-muted-foreground">{t("security.lastActivity")} {formatDate(session.last_used_at)}</p>
            )}
            <p className="text-xs text-muted-foreground">{t("security.expires")} {formatDate(session.expires_at)}</p>
          </div>
        </div>
        {session.is_current && (
          <Badge variant="secondary" className="ml-2">{t("security.currentSession")}</Badge>
        )}
      </div>
      <div className="flex items-center gap-2 ml-4">
        {session.is_current ? (
          <Badge variant="outline">{t("security.currentSession")}</Badge>
        ) : (
          <AlertDialog>
            <AlertDialogTrigger>
              <Button
                variant="destructive"
                size="sm"
                disabled={isRevoking}
                onClick={handleRevoke}
              >
                {isRevoking ? (
                  <>
                    <svg className="mr-1 h-3 w-3 animate-spin" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /><animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" /></svg>
                    {t("common.loading")}
                  </>
                ) : (
                  t("security.revokeSession")
                )}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t("security.revokeSessionConfirm")}</AlertDialogTitle>
                <AlertDialogDescription>{t("security.revokeSessionDescription")}</AlertDialogDescription>
              </AlertDialogHeader>
              <div className="flex gap-2 justify-end">
                <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
                <AlertDialogAction onClick={handleRevoke} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                  {t("security.revokeSession")}
                </AlertDialogAction>
              </div>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>
    </div>
  );
}