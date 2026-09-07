import type { Metadata, Viewport } from "next";
import "./globals.css";
import { StoreProvider } from "@/components/providers/StoreProvider";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { IntlProvider } from "@/components/providers/IntlProvider";
import { AppInit } from "@/components/providers/AppInit";


const locales = ["en", "fa"] as const;
type Locale = (typeof locales)[number];

async function getLocaleMessages(locale: Locale) {
  try {
    return (await import(`../../messages/${locale}.json`)).default;
  } catch {
    return (await import(`../../messages/en.json`)).default;
  }
}

export const metadata: Metadata = {
  title: "Todo App",
  description: "A secure todo application",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "black" },
  ],
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = "en" as Locale;

  const messages = await getLocaleMessages(locale);

  return (
    <html
      lang={locale}
      dir={(locale === "fa" ? "rtl" : "ltr") as "ltr" | "rtl"}
      className={`h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <StoreProvider>
          <ThemeProvider>
            <IntlProvider locale={locale} messages={messages}>
              <AppInit>{children}</AppInit>
            </IntlProvider>
          </ThemeProvider>
        </StoreProvider>
      </body>
    </html>
  );
}