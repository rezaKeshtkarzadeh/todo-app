"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations, useLocale } from "next-intl";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sendOtp, decrementCooldown } from "@/store/slices/authSlice";

const phoneSchema = z.object({
  phone_number: z.string().min(10, { message: "auth.phoneTooShort" }).max(15, { message: "auth.phoneTooLong" }),
});

interface PhoneFormProps {
  onOtpSent: () => void;
}

type PhoneFormData = z.infer<typeof phoneSchema>;

export function PhoneForm({ onOtpSent }: PhoneFormProps) {
  const t = useTranslations();
  const locale = useLocale();
  const dispatch = useAppDispatch();
  const { sendOtpCooldown, otpDebug } = useAppSelector((state) => state.auth);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PhoneFormData>({
    resolver: zodResolver(phoneSchema),
  });

  useEffect(() => {
    const interval = setInterval(() => {
      dispatch(decrementCooldown());
    }, 1000);
    return () => clearInterval(interval);
  }, [dispatch]);

  const onSubmit = async (data: PhoneFormData) => {
    const result = await dispatch(sendOtp(data.phone_number));

    if (sendOtp.fulfilled.match(result)) {
      onOtpSent();
    }
  };

  const isRtl = locale === "fa";

  const submitLabel = isSubmitting
    ? t("common.loading")
    : sendOtpCooldown > 0
      ? t("auth.resendIn", { seconds: sendOtpCooldown })
      : t("auth.sendCode");

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-6"
      dir={isRtl ? "rtl" : "ltr"}
    >
      <div className="space-y-2">
        <Label htmlFor="phone_number">{t("auth.phoneNumber")}</Label>
        <Input
          id="phone_number"
          type="tel"
          placeholder={isRtl ? "۰۹۱۲۳۴۵۶۷۸۹" : "09123456789"}
          {...register("phone_number")}
          disabled={sendOtpCooldown > 0 || isSubmitting}
          className={isRtl ? "text-right" : ""}
        />
        {errors.phone_number && (
          <p className="text-sm text-destructive" role="alert">
            {t(errors.phone_number.message as string)}
          </p>
        )}
      </div>

      <Button type="submit" disabled={sendOtpCooldown > 0 || isSubmitting} className="w-full">
        {submitLabel}
      </Button>

      {process.env.NODE_ENV === "development" && otpDebug && (
        <p className="text-xs text-muted-foreground text-center font-mono">
          {t("common.otpDebug", { code: otpDebug })}
        </p>
      )}
    </form>
  );
}