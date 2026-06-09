import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Application Finder",
  description: "Electromagnetic Application-Space-Guided Generative Inverse Materials Design Platform"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const vercelAnalytics = process.env.NEXT_PUBLIC_VERCEL_ANALYTICS === "true";
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {children}
        {vercelAnalytics ? <Analytics /> : null}
      </body>
    </html>
  );
}
