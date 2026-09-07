"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { Globe } from "lucide-react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();

  const handleLocaleChange = (newLocale: string) => {
    document.cookie = `NEXT_LOCALE=${newLocale}; path=/; max-age=31536000`;
    router.refresh();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Globe className="size-6 text-muted-foreground hover:text-foreground cursor-pointer p-1" aria-label="Change language" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleLocaleChange("en")} className={"font-roboto"}>
          {locale === "en" && "✓ "}English
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleLocaleChange("fa")} className={"font-vazir"}>
          {locale === "fa" && "✓ "}فارسی
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}