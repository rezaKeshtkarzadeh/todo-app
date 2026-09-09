"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { revokeAllSessions } from "@/store/slices/securitySlice";
import { ShieldAlert, Loader2 } from "lucide-react";

interface RevokeAllDialogProps {
  onSuccess?: () => void;
}

export function RevokeAllDialog({ onSuccess }: RevokeAllDialogProps) {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { revoking } = useAppSelector((state) => state.security);
  const isRevoking = revoking === "all";

  const handleRevokeAll = () => {
    dispatch(revokeAllSessions()).then((result) => {
      if (revokeAllSessions.fulfilled.match(result)) {
        onSuccess?.();
      }
    });
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger>
        <Button variant="destructive" className="gap-2" disabled={isRevoking}>
          <ShieldAlert className="h-4 w-4" />
          {t("security.globalLogout")}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("security.globalLogoutConfirm")}</AlertDialogTitle>
          <AlertDialogDescription>{t("security.globalLogoutDescription")}</AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex gap-2 justify-end">
          <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
          <AlertDialogAction onClick={handleRevokeAll} className="bg-destructive text-destructive-foreground hover:bg-destructive/90" disabled={isRevoking}>
            {isRevoking ? (
              <>
                <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                {t("common.loading")}
              </>
            ) : (
              t("security.globalLogout")
            )}
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}