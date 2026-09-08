"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations, useLocale } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { verifyOtp } from "@/store/slices/authSlice";

const otpSchema = z.object({
  code: z.string().length(4, { message: "auth.otpLength" }).regex(/^\d+$/, { message: "auth.otpDigits" }),
});

type OtpFormData = z.infer<typeof otpSchema>;

interface OtpFormProps {
  onBack?: () => void;
}

export function OtpForm({ onBack }: OtpFormProps) {
  const t = useTranslations();
  const locale = useLocale();
  const dispatch = useAppDispatch();
  const { phoneNumber, error } = useAppSelector((state) => state.auth);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<OtpFormData>({
    resolver: zodResolver(otpSchema),
  });

  const onSubmit = (data: OtpFormData) => {
    dispatch(verifyOtp({ phoneNumber: phoneNumber || "", code: data.code })).then((result) => {
      if (verifyOtp.rejected.match(result)) {
        const apiError = result.payload as any;
        if (apiError?.code === "AUTH_INVALID_OTP" || apiError?.code === "AUTH_OTP_EXPIRED") {
          setError("code", { type: "server", message: t(`auth.${apiError.code}`) });
        } else if (apiError?.code === "AUTH_OTP_MAX_ATTEMPTS") {
          setError("code", { type: "server", message: t(`auth.${apiError.code}`) });
        }
      }
    });
  };

  const isRtl = locale === "fa";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" dir={isRtl ? "rtl" : "ltr"}>
      {phoneNumber && (
        <p className="text-sm text-muted-foreground text-center">
          {t("auth.codeSentTo", { phone: phoneNumber })}
        </p>
      )}

      <div className="space-y-2">
        <Label htmlFor="code">{t("auth.otpCode")}</Label>
        <Input
          id="code"
          type="text"
          inputMode="numeric"
          maxLength={4}
          placeholder="****"
          autoComplete="one-time-code"
          {...register("code")}
          disabled={isSubmitting}
          className="text-center text-2xl tracking-widest"
        />
        {errors.code && (
          <p className="text-sm text-destructive text-center" role="alert">
            {t(errors.code.message as string)}
          </p>
        )}
      </div>

      {error && (error.code === "AUTH_OTP_MAX_ATTEMPTS" || error.code === "AUTH_INVALID_OTP" || error.code === "AUTH_OTP_EXPIRED") && (
        <p className="text-sm text-destructive text-center" role="alert">
          {t(`auth.${error.code}`)}
        </p>
      )}

      <div className="flex gap-2">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting ? t("common.loading") : t("auth.verify")}
        </Button>
        {onBack && (
          <Button type="button" variant="outline" onClick={onBack} className="flex-1">
            {t("common.cancel")}
          </Button>
        )}
      </div>
    </form>
  );
}