import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JARVIS // Cognitive Multi-Agent OS",
  description: "Chief Systems Architect: Ansh Tiwari — Autonomous Multi-Agent Swarm, Voice Telephony & Powerups",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-jarvis-bg text-jarvis-text min-h-screen selection:bg-jarvis-cyan selection:text-black">
        {children}
      </body>
    </html>
  );
}

