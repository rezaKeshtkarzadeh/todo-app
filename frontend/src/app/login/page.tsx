"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { PhoneForm } from "@/components/auth/PhoneForm";
import { OtpForm } from "@/components/auth/OtpForm";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

export default function LoginPage() {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const router = useRouter();

  const { isAuthenticated, status, error } = useAppSelector(
    (state) => state.auth
  );

  const [step, setStep] = useState<"phone" | "otp">("phone");

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/tasks");
      router.refresh();
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (error?.code === "AUTH_OTP_MAX_ATTEMPTS") {
      setStep("phone");
    }
  }, [error]);

  const handleBack = () => {
    setStep("phone");
  };

  const handleOtpSent = () => {
    setStep("otp");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">
            {t("common.appName")}
          </CardTitle>

          <p className="text-muted-foreground mt-2">
            {t("auth.signInToContinue")}
          </p>
        </CardHeader>

        <CardContent className="space-y-6">
          {status === "error" &&
            error &&
            error.code !== "AUTH_OTP_MAX_ATTEMPTS" &&
            error.code !== "AUTH_INVALID_OTP" &&
            error.code !== "AUTH_OTP_EXPIRED" && (
              <div
                className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-lg"
                role="alert"
              >
                <AlertCircle className="h-4 w-4 shrink-0" />

                <span>
                  {t(`auth.${error.code}`) || t("common.error")}
                </span>
              </div>
            )}

          {step === "phone" ? (
            <PhoneForm onOtpSent={handleOtpSent} />
          ) : (
            <OtpForm onBack={handleBack} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}