"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { 
  requestCurrentPhoneOtp, 
  verifyCurrentPhoneOtp, 
  requestNewPhoneOtp, 
  verifyNewPhoneOtp,
  resetPhoneChange 
} from "@/store/slices/profileSlice";
import { ArrowRight, ArrowLeft, CheckCircle, Loader2 } from "lucide-react";

type PhoneChangeStep = "requestCurrent" | "verifyCurrent" | "requestNew" | "verifyNew";

const phoneSchema = z.object({
  phone_number: z.string().min(10, { message: "auth.phoneTooShort" }).max(15, { message: "auth.phoneTooLong" }),
});

const otpSchema = z.object({
  code: z.string().length(4, { message: "auth.otpLength" }).regex(/^\d+$/, { message: "auth.otpDigits" }),
});

type PhoneFormData = z.infer<typeof phoneSchema>;
type OtpFormData = z.infer<typeof otpSchema>;

export function PhoneChangeWizard() {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { phoneChangeStep, status, error, phoneChangeToken, phoneChangeNewNumber } = useAppSelector((state) => state.profile);

  const [currentStep, setCurrentStep] = useState<PhoneChangeStep>("requestCurrent");

  // Sync with Redux state
  useEffect(() => {
    switch (phoneChangeStep) {
      case "currentRequested":
        setCurrentStep("verifyCurrent");
        break;
      case "currentVerified":
        setCurrentStep("requestNew");
        break;
      case "newRequested":
        setCurrentStep("verifyNew");
        break;
      case "idle":
      default:
        setCurrentStep("requestCurrent");
        break;
    }
  }, [phoneChangeStep]);

  // Handle token invalid - reset to step 1
  useEffect(() => {
    if (error === "PROFILE_PHONE_CHANGE_TOKEN_INVALID") {
      setCurrentStep("requestCurrent");
    }
  }, [error]);

  const phoneForm = useForm<PhoneFormData>({
    resolver: zodResolver(phoneSchema),
    defaultValues: { phone_number: "" },
  });

  const otpForm = useForm<OtpFormData>({
    resolver: zodResolver(otpSchema),
    defaultValues: { code: "" },
  });

  const handleNext = () => {
    switch (currentStep) {
      case "requestCurrent":
        setCurrentStep("verifyCurrent");
        break;
      case "verifyCurrent":
        setCurrentStep("requestNew");
        break;
      case "requestNew":
        setCurrentStep("verifyNew");
        break;
    }
  };

  const handleBack = () => {
    switch (currentStep) {
      case "verifyCurrent":
        setCurrentStep("requestCurrent");
        break;
      case "requestNew":
        setCurrentStep("verifyCurrent");
        break;
      case "verifyNew":
        setCurrentStep("requestNew");
        break;
    }
  };

  const handleCancel = () => {
    dispatch(resetPhoneChange());
    setCurrentStep("requestCurrent");
    phoneForm.reset();
    otpForm.reset();
  };

  const onPhoneSubmit = (data: PhoneFormData) => {
    dispatch(requestCurrentPhoneOtp());
  };

  const onOtpSubmit = (data: OtpFormData) => {
    if (currentStep === "verifyCurrent") {
      dispatch(verifyCurrentPhoneOtp(data.code)).then((result) => {
        if (verifyCurrentPhoneOtp.fulfilled.match(result)) {
          setCurrentStep("requestNew");
          otpForm.reset();
        }
      });
    } else if (currentStep === "verifyNew") {
      dispatch(verifyNewPhoneOtp(data.code)).then((result) => {
        if (verifyNewPhoneOtp.fulfilled.match(result)) {
          setCurrentStep("requestCurrent");
          otpForm.reset();
        }
      });
    }
  };

  const onNewPhoneSubmit = (data: PhoneFormData) => {
    dispatch(requestNewPhoneOtp(data.phone_number)).then((result) => {
      if (requestNewPhoneOtp.fulfilled.match(result)) {
        setCurrentStep("verifyNew");
        phoneForm.reset();
      }
    });
  };

  const getStepNumber = (step: PhoneChangeStep): number => {
    switch (step) {
      case "requestCurrent": return 1;
      case "verifyCurrent": return 2;
      case "requestNew": return 3;
      case "verifyNew": return 4;
    }
  };

  const isStepActive = (step: PhoneChangeStep): boolean => getStepNumber(step) <= getStepNumber(currentStep);
  const isStepCompleted = (step: PhoneChangeStep): boolean => getStepNumber(step) < getStepNumber(currentStep);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-2xl">📱</span>
          {t("profile.changePhoneWizard")}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Step indicator */}
        <div className="flex items-center justify-between">
          {[
            { step: "requestCurrent", label: t("profile.step1Label") },
            { step: "verifyCurrent", label: t("profile.step2Label") },
            { step: "requestNew", label: t("profile.step3Label") },
            { step: "verifyNew", label: t("profile.step4Label") },
          ].map(({ step, label }, index) => (
            <div key={step} className="flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                isStepCompleted(step as PhoneChangeStep)
                  ? "bg-primary text-primary-foreground"
                  : isStepActive(step as PhoneChangeStep)
                  ? "bg-primary/20 text-primary"
                  : "bg-muted text-muted-foreground"
              }`}>
                {isStepCompleted(step as PhoneChangeStep) ? <CheckCircle className="h-4 w-4" /> : getStepNumber(step as PhoneChangeStep)}
              </div>
              <div className={`w-24 h-0.5 mx-2 transition-colors ${index < 3 && isStepActive((["requestCurrent", "verifyCurrent", "requestNew", "verifyNew"][index + 1]) as PhoneChangeStep) ? "bg-primary" : "bg-muted"}`} />
              <span className={`text-sm font-medium ${isStepActive(step as PhoneChangeStep) ? "text-foreground" : "text-muted-foreground"}`}>
                {label}
              </span>
            </div>
          ))}
        </div>

        <Separator />

        {error && (
          <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-lg" role="alert">
            {t(`profile.${error}`) || t("common.error")}
            {error === "PROFILE_PHONE_CHANGE_TOKEN_INVALID" && (
              <p className="mt-1 text-xs">{t("profile.tokenExpired")}</p>
            )}
          </div>
        )}

        {/* Step 1: Request current phone OTP */}
        {(currentStep === "requestCurrent") && (
          <div className="space-y-4">
            <p className="text-muted-foreground text-center">
              {t("profile.step1Description")}
            </p>
            <form onSubmit={phoneForm.handleSubmit(onPhoneSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="phone_number">{t("auth.phoneNumber")}</Label>
                <Input
                  id="phone_number"
                  type="tel"
                  placeholder="09123456789"
                  {...phoneForm.register("phone_number")}
                  disabled={status === "loading"}
                />
                {phoneForm.formState.errors.phone_number && (
                  <p className="text-sm text-destructive" role="alert">
                    {t(phoneForm.formState.errors.phone_number.message as string)}
                  </p>
                )}
              </div>
              <Button type="submit" disabled={status === "loading"} className="w-full">
                {status === "loading" && currentStep === "requestCurrent" ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    {t("common.loading")}
                  </>
                ) : (
                  t("profile.requestCurrentOtp")
                )}
              </Button>
            </form>
            {phoneChangeToken && process.env.NODE_ENV === "development" && (
              <p className="text-xs text-muted-foreground text-center font-mono">
                {t("common.otpDebug", { code: phoneChangeToken })}
              </p>
            )}
          </div>
        )}

        {/* Step 2: Verify current phone OTP */}
        {(currentStep === "verifyCurrent") && (
          <div className="space-y-4">
            <p className="text-muted-foreground text-center">
              {t("profile.step2Description")}
            </p>
            <form onSubmit={otpForm.handleSubmit(onOtpSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="code">{t("auth.otpCode")}</Label>
                <Input
                  id="code"
                  type="text"
                  inputMode="numeric"
                  maxLength={4}
                  placeholder="****"
                  autoComplete="one-time-code"
                  {...otpForm.register("code")}
                  disabled={status === "loading"}
                  className="text-center text-2xl tracking-widest"
                />
                {otpForm.formState.errors.code && (
                  <p className="text-sm text-destructive text-center" role="alert">
                    {t(otpForm.formState.errors.code.message as string)}
                  </p>
                )}
              </div>
              {error && (error === "AUTH_INVALID_OTP" || error === "AUTH_OTP_EXPIRED" || error === "AUTH_OTP_MAX_ATTEMPTS") && (
                <p className="text-sm text-destructive text-center" role="alert">
                  {t(`auth.${error}`)}
                </p>
              )}
              <div className="flex gap-2">
                <Button type="submit" disabled={status === "loading"} className="flex-1">
                  {status === "loading" && currentStep === "verifyCurrent" ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      {t("common.loading")}
                    </>
                  ) : (
                    t("auth.verify")
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={handleBack} className="flex-1">
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  {t("common.back")}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Step 3: Request new phone OTP */}
        {(currentStep === "requestNew") && (
          <div className="space-y-4">
            <p className="text-muted-foreground text-center">
              {t("profile.step3Description")}
            </p>
            <form onSubmit={phoneForm.handleSubmit(onNewPhoneSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="new_phone_number">{t("profile.newPhoneNumber")}</Label>
                <Input
                  id="new_phone_number"
                  type="tel"
                  placeholder="09123456789"
                  {...phoneForm.register("phone_number")}
                  disabled={status === "loading"}
                />
                {phoneForm.formState.errors.phone_number && (
                  <p className="text-sm text-destructive" role="alert">
                    {t(phoneForm.formState.errors.phone_number.message as string)}
                  </p>
                )}
              </div>
              {error && error === "PROFILE_PHONE_ALREADY_IN_USE" && (
                <p className="text-sm text-destructive text-center" role="alert">
                  {t(`profile.${error}`)}
                </p>
              )}
              {error && error === "PROFILE_PHONE_SAME_AS_CURRENT" && (
                <p className="text-sm text-destructive text-center" role="alert">
                  {t(`profile.${error}`)}
                </p>
              )}
              <div className="flex gap-2">
                <Button type="submit" disabled={status === "loading"} className="flex-1">
                  {status === "loading" && currentStep === "requestNew" ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      {t("common.loading")}
                    </>
                  ) : (
                    t("profile.requestNewOtp")
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={handleBack} className="flex-1">
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  {t("common.back")}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Step 4: Verify new phone OTP */}
        {(currentStep === "verifyNew") && (
          <div className="space-y-4">
            <p className="text-muted-foreground text-center">
              {t("profile.step4Description", { phone: phoneChangeNewNumber || "" })}
            </p>
            <form onSubmit={otpForm.handleSubmit(onOtpSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="code">{t("auth.otpCode")}</Label>
                <Input
                  id="code"
                  type="text"
                  inputMode="numeric"
                  maxLength={4}
                  placeholder="****"
                  autoComplete="one-time-code"
                  {...otpForm.register("code")}
                  disabled={status === "loading"}
                  className="text-center text-2xl tracking-widest"
                />
                {otpForm.formState.errors.code && (
                  <p className="text-sm text-destructive text-center" role="alert">
                    {t(otpForm.formState.errors.code.message as string)}
                  </p>
                )}
              </div>
              {error && (error === "AUTH_INVALID_OTP" || error === "AUTH_OTP_EXPIRED" || error === "AUTH_OTP_MAX_ATTEMPTS") && (
                <p className="text-sm text-destructive text-center" role="alert">
                  {t(`auth.${error}`)}
                </p>
              )}
              <div className="flex gap-2">
                <Button type="submit" disabled={status === "loading"} className="flex-1">
                  {status === "loading" && currentStep === "verifyNew" ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      {t("common.loading")}
                    </>
                  ) : (
                    t("auth.verify")
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={handleBack} className="flex-1">
                  <ArrowLeft className="h-4 w-4 mr-1" />
                  {t("common.back")}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Cancel button */}
        <AlertDialog>
          <AlertDialogTrigger>
            <Button variant="ghost" className="w-full" onClick={handleCancel}>
              {t("common.cancel")}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{t("profile.cancelWizard")}</AlertDialogTitle>
              <AlertDialogDescription>
                {t("profile.cancelWizardDescription")}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <div className="flex gap-2 justify-end">
              <AlertDialogCancel>{t("common.cancel")}</AlertDialogCancel>
              <AlertDialogAction onClick={handleCancel} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                {t("common.confirm")}
              </AlertDialogAction>
            </div>
          </AlertDialogContent>
        </AlertDialog>
      </CardContent>
    </Card>
  );
}