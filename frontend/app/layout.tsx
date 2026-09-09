import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodePilot AI - Code Review & Refactoring Engine",
  description: "Enterprise multi-agent AI system for deep code analysis, security auditing, and automated refactoring.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
