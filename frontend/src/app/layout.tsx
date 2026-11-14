import type { Metadata } from "next";
import { Open_Sans, Merriweather, Geist_Mono } from "next/font/google";
import "./globals.css";

const openSans = Open_Sans({
  variable: "--font-open-sans",
  subsets: ["latin"],
});

const merriweather = Merriweather({
  variable: "--font-merriweather",
  weight: ["400", "700"],
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Reforesta FINANCIACIÓN → Reforesta",
  description: "Asociación Reforesta · Centro de observabilidad y captación de convocatorias públicas y privadas para la reforestación y recuperación de bosques en España",
  icons: {
    icon: [
      { url: "/reforesta/cropped-favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/reforesta/cropped-favicon-192x192.png", sizes: "192x192", type: "image/png" },
    ],
    shortcut: "/reforesta/cropped-favicon-32x32.png",
    apple: "/reforesta/cropped-favicon-192x192.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="es"
      className={`${openSans.variable} ${merriweather.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
