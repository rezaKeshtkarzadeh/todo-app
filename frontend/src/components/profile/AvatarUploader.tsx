"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { uploadAvatar } from "@/store/slices/profileSlice";
import { validateImageFile } from "@/lib/image";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogCancel, AlertDialogAction } from "@/components/ui/alert-dialog";
import { Camera, X, Loader2 } from "lucide-react";

export function AvatarUploader() {
  const t = useTranslations();
  const dispatch = useAppDispatch();
  const { avatarUrl, status, error, uploadProgress } = useAppSelector((state) => state.profile);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setFileError(null);

    const validation = validateImageFile(file);
    if (!validation.valid) {
      setFileError(validation.error || "Invalid file");
      event.target.value = "";
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewUrl(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validation = validateImageFile(file);
    if (!validation.valid) {
      setFileError(validation.error || "Invalid file");
      event.target.value = "";
      return;
    }

    setFileError(null);
    dispatch(uploadAvatar(file)).then((result) => {
      if (uploadAvatar.fulfilled.match(result)) {
        setPreviewUrl(null);
      }
    });
    event.target.value = "";
  };

  const handleRemove = () => {
    setPreviewUrl(null);
    // Note: backend doesn't have a delete avatar endpoint, so we just clear local preview
    // The actual avatar on server remains until a new one is uploaded
  };

  const displayUrl = previewUrl || avatarUrl;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-6">
        <Avatar className="h-24 w-24">
          <AvatarImage
            src={displayUrl ? `/uploads/${displayUrl}` : undefined}
            alt={t("profile.avatar")}
            className="object-cover"
          />
          <AvatarFallback className="text-2xl">
            <Camera className="h-6 w-6" />
          </AvatarFallback>
        </Avatar>

        <div className="flex flex-col gap-2">
          <Label>{t("profile.avatar")}</Label>
          {displayUrl ? (
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleRemove}>
                <X className="h-3 w-3 mr-1" />
                {t("profile.removeAvatar")}
              </Button>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("profile.noAvatar")}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label className="cursor-pointer">
          <span className="text-sm font-medium">{t("profile.changeAvatar")}</span>
          <Input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleUpload}
            className="sr-only"
            id="avatar-upload"
            disabled={status === "loading"}
          />
        </Label>

        {fileError && (
          <p className="text-sm text-destructive" role="alert">
            {t(fileError)}
          </p>
        )}

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {t(`profile.${error}`) || t("common.error")}
          </p>
        )}

        {status === "loading" && (
          <div className="space-y-2">
            <Progress value={uploadProgress} className="h-2" />
            <p className="text-sm text-muted-foreground text-center">
              {t("profile.uploading", { progress: uploadProgress })}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}