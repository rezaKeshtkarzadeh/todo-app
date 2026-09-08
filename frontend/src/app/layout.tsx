import type { Metadata, Viewport } from "next";
import { headers } from "next/headers";
import localFont from "next/font/local"
import "./globals.css";
import { StoreProvider } from "@/components/providers/StoreProvider";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { IntlProvider } from "@/components/providers/IntlProvider";
import { AppInit } from "@/components/providers/AppInit";
import { AppNav } from "@/components/layout/AppNav";

const locales = ["en", "fa"] as const;
type Locale = (typeof locales)[number];

const roboto = localFont({
  src: "../../public/fonts/roboto.woff2",
  variable: "--font-roboto",
  display: "swap",
})

const vazir = localFont({
  src: "../../public/fonts/vazir.woff2",
  variable: "--font-vazir",
  display: "swap",
})

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
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const headersList = await headers();
  const locale = (headersList.get("x-next-intl-locale") as Locale) || "en";

  const messages = await getLocaleMessages(locale);

  return (
    <html
      lang={locale}
      dir={(locale === "fa" ? "rtl" : "ltr") as "ltr" | "rtl"}
      className={`${roboto.variable} ${vazir.variable} h-full antialiased ${locale === "fa" ? "font-vazir" : "font-roboto"}`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <StoreProvider>
          <ThemeProvider>
            <IntlProvider locale={locale} messages={messages}>
              <AppInit>
                <AppNav />
                <main className="flex-1 pt-12">{children}</main>
              </AppInit>
            </IntlProvider>
          </ThemeProvider>
        </StoreProvider>
      </body>
    </html>
  );
}