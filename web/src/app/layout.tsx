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

      <body className="bg-[#05070B] text-[#E8E6DE] min-h-screen antialiased selection:bg-[#C8973B]/30 selection:text-white">
        {children}
      </body>
    </html>
  );
}
