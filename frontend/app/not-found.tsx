import Link from "next/link";

export default function NotFound() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", textAlign: "center", padding: "2rem" }}>
      <h2 style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "1rem" }}>404 - Page Not Found</h2>
      <p style={{ marginBottom: "1.5rem", color: "var(--text-secondary)" }}>Could not find requested resource</p>
      <Link href="/" className="btn-launch-primary">
        Return Home
      </Link>
    </div>
  );
}
