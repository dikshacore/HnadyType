import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Your handwriting, typed",
  description: "Turn typed text into your own handwriting.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
