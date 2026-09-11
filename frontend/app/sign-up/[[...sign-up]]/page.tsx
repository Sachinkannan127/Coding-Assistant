"use client";

import { SignUp } from "@clerk/nextjs";


export default function SignUpPage() {
  return (
    <main style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      background: "radial-gradient(ellipse at top, #1e1b4b 0%, #0f172a 60%, #020617 100%)",
      padding: "2rem"
    }}>
      <div style={{
        marginBottom: "2rem",
        textAlign: "center"
      }}>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          fontSize: "1.5rem",
          fontWeight: 700,
          color: "#f8fafc",
          marginBottom: "0.5rem"
        }}>
          <span>⚡</span> CodePilot AI
        </div>
        <p style={{ color: "#94a3b8", fontSize: "0.95rem" }}>
          Create an account to start reviewing and refactoring code
        </p>
      </div>

      <SignUp
        appearance={{
          elements: {
            card: {
              background: "rgba(30, 41, 59, 0.85)",
              backdropFilter: "blur(16px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
              borderRadius: "16px"
            },
            headerTitle: { color: "#f8fafc" },
            headerSubtitle: { color: "#94a3b8" },
            socialButtonsBlockButton: {
              backgroundColor: "rgba(15, 23, 42, 0.6)",
              borderColor: "rgba(255, 255, 255, 0.1)",
              color: "#f8fafc"
            },
            formButtonPrimary: {
              background: "linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)",
              fontSize: "0.95rem",
              fontWeight: "600"
            },
            footerActionLink: { color: "#818cf8" }
          }
        }}
      />
    </main>
  );
}
