"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { label: "Dashboard", href: "/" },
    { label: "Runs Catalog", href: "/runs" },
    { label: "Supervisor Templates", href: "/supervisors" },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-neutral-800 bg-black">
      <div className="max-w-[1360px] w-full mx-auto px-6 sm:px-10 lg:px-14 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <div className="font-medium text-lg text-[#e6e6e6] tracking-tight">
            OrderPilot
          </div>
          <span className="text-[10px] uppercase font-medium px-2 py-1 rounded bg-[#141414] text-neutral-400 border border-neutral-800 hidden sm:inline-block">
            Temporal Agent
          </span>
        </Link>

        <nav className="flex items-center gap-4">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "text-sm font-medium transition-colors",
                  isActive
                    ? "text-white"
                    : "text-neutral-500 hover:text-white"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <a
          href="http://localhost:8233"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-[6px] border border-neutral-800 bg-[#141414] hover:bg-[#1f1f1f] text-xs text-neutral-400 hover:text-white transition-colors"
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span className="font-mono text-[11px]">Temporal UI (8233) ↗</span>
        </a>
      </div>
    </header>
  );
}
