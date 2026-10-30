import type { Metadata } from "next";
import "./globals.css";
import { AppLayout } from "@/components/layout/app-layout";
import { ThemeProvider } from "@/lib/theme";

export const metadata: Metadata = {
  title: "FlashFacts — Current Affairs Intelligence Platform",
  description: "Real-time current affairs extraction, domain classification, and temporal event analytics dashboard.",
  keywords: ["Current Affairs", "News Intelligence", "UPSC", "TNPSC", "FastAPI", "Next.js"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased min-h-screen">
        <ThemeProvider>
          <AppLayout>{children}</AppLayout>
        </ThemeProvider>
      </body>
    </html>
  );
}
