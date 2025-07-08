'use client'

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { useGlassTheme } from "@/hooks/useGlassTheme";
import React from "react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// AICODE-NOTE: Metadata moved to a server component if needed in the future
// export const metadata: Metadata = {
//   title: "AI Learning",
//   description: "The future of learning, personalized with AI.",
// };

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { theme } = useGlassTheme();

  React.useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme)
  }, [theme])

  return (
    <html lang="ru" suppressHydrationWarning>
      <body
        className={cn(
            "min-h-screen font-sans antialiased",
            geistSans.variable, 
            geistMono.variable
        )}
      >
        {children}
      </body>
    </html>
  );
}
