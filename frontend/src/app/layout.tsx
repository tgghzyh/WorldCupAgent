import type { Metadata } from "next";
import "@/styles/globals.css";
import { Providers } from "@/components/Providers";

export const metadata: Metadata = {
  title: "World Cup 2026 AI Prediction | Explainable Tournament Analysis",
  description:
    "AI-powered World Cup predictions with explainable reasoning. Track champion probability, match analysis, and Monte Carlo simulations.",
  keywords: [
    "World Cup",
    "AI Prediction",
    "Tournament Analysis",
    "Monte Carlo",
    "Explainable AI",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-bg text-text">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
