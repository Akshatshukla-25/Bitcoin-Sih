import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NTRO INTERNAL • Bitcoin Forensic Monitor | SIH26146",
  description: "Air-Gapped AI Engine for Bitcoin Transaction Traffic Monitoring & Laundering Detection",
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
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,600;0,8..60,700;1,8..60,600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#05070B] text-[#E8E6DE] min-h-screen antialiased selection:bg-[#C8973B]/30 selection:text-white">
        {children}
      </body>
    </html>
  );
}
