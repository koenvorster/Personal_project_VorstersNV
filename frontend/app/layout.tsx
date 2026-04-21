import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import ScrollToTop from "@/components/ui/ScrollToTop";
import AuthProvider from "@/components/AuthProvider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#0a0f1e",
};

export const metadata: Metadata = {
  metadataBase: new URL("https://koenvorsters.dev"),
  title: {
    default: "Koen Vorsters — Developer, Engineer & Innovator",
    template: "%s | Koen Vorsters",
  },
  description:
    "Portfolio van Koen Vorsters. Full-stack developer met expertise in AI, IoT en moderne webtechnologieën.",
  keywords: ["developer", "portfolio", "full-stack", "AI", "IoT", "Next.js", "FastAPI", "Koen Vorsters"],
  authors: [{ name: "Koen Vorsters" }],
  creator: "Koen Vorsters",
  openGraph: {
    type: "website",
    locale: "nl_BE",
    siteName: "Koen Vorsters",
    title: "Koen Vorsters — Developer, Engineer & Innovator",
    description:
      "Full-stack developer met expertise in AI, IoT en moderne webtechnologieën.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Koen Vorsters — Developer, Engineer & Innovator",
    description:
      "Full-stack developer met expertise in AI, IoT en moderne webtechnologieën.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="nl" className={`${inter.variable} h-full antialiased`} suppressHydrationWarning>
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100 overflow-x-hidden">
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
          <ScrollToTop />
        </AuthProvider>
      </body>
    </html>
  );
}
