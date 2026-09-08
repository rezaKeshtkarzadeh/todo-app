"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { Globe } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setLocale } from "@/store/slices/settingsSlice";
import { setLocale as setLocaleLocal } from "@/lib/local-prefs";

export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const reduxLocale = useAppSelector((state) => state.settings.locale);

  const handleLocaleChange = (newLocale: "en" | "fa") => {
    setLocaleLocal(newLocale);
    dispatch(setLocale(newLocale));
    document.cookie = `NEXT_LOCALE=${newLocale}; path=/; max-age=31536000`;
    router.refresh();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Globe className="size-6 text-muted-foreground hover:text-foreground cursor-pointer p-1" aria-label="Change language" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleLocaleChange("en")} className="font-roboto">
          {reduxLocale === "en" && "✓ "}English
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleLocaleChange("fa")} className="font-vazir">
          {reduxLocale === "fa" && "✓ "}فارسی
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}