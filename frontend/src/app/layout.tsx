import type { Metadata } from "next";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { Toaster } from "sonner";
import "./globals.css";

export const metadata: Metadata = {
  title: "Atlas AI — Enterprise AI Workspace",
  description: "The organizational intelligence platform. Search, chat, and reason across your entire knowledge base.",
  keywords: ["AI", "enterprise", "knowledge base", "RAG", "search"],
  openGraph: {
    title: "Atlas AI",
    description: "Enterprise AI Workspace for Organizational Intelligence",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <QueryProvider>
            {children}
            <Toaster
              position="bottom-right"
              theme="dark"
              toastOptions={{
                style: { background: "hsl(224 71.4% 6%)", border: "1px solid hsl(215 27.9% 16.9%)", color: "white" },
              }}
            />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
