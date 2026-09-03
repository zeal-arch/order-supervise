import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/ui/Navbar";

export const metadata: Metadata = {
  title: "Order Supervisor | Sagepilot AI Agent Platform",
  description: "Autonomous long-running order lifecycle supervisor powered by Temporal workflows",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-black text-white antialiased min-h-screen flex flex-col font-sans">
        <Navbar />
        <main className="flex-1 max-w-[1360px] w-full mx-auto px-6 sm:px-10 lg:px-14 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
