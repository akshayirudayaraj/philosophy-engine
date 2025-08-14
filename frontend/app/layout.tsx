import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "philosophy rag engine",
  description: "rag for clear, academic philosophical essays",
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
