import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Codex Portfolio",
  description: "Track cryptocurrency portfolio transactions and current value.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
