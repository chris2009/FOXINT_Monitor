import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OSINT Monitor",
  description: "Monitoreo de páginas públicas de redes sociales",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
