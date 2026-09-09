import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Code Review & Refactoring Platform",
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
        <nav className="navbar">
          <div className="logo">
            <span>⚡</span> CodePilot AI
          </div>
          <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
            <span className="badge badge-indigo">Phase 1 Foundation</span>
            <span className="badge badge-success">
              <span className="status-dot"></span> API Connected
            </span>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
