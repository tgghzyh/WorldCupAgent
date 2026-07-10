"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Braces, BrainCircuit, CalendarDays, DatabaseZap, Home, Search, Trophy } from "lucide-react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", key: "nav.dashboard", icon: Home, fallback: "Dashboard" },
  { href: "/schedule", key: "nav.schedule", icon: Braces, fallback: "Prediction Tree" },
  { href: "/real-schedule", key: "nav.realSchedule", icon: CalendarDays, fallback: "Real Schedule" },
  { href: "/tournament", key: "nav.champion", icon: Trophy, fallback: "Champion" },
  { href: "/teams", key: "nav.teams", icon: Search, fallback: "Teams" },
  { href: "/data", key: "nav.data", icon: DatabaseZap, fallback: "Data" },
  { href: "/agent", key: "nav.agent", icon: BrainCircuit, fallback: "Agent Run" },
];

export function SiteNavigation() {
  const pathname = usePathname();
  const { t } = useI18n();

  return (
    <header className="sticky top-0 z-40 border-b border-[color:var(--border)] bg-[rgba(247,241,232,0.88)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between md:px-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-full bg-[color:var(--brand-blue)] text-sm font-semibold text-white">
            26
          </span>
          <div>
            <p className="text-sm font-semibold leading-none">{t("brand.title")}</p>
            <p className="mt-1 text-xs text-[color:var(--muted)]">{t("brand.subtitle")}</p>
          </div>
        </Link>
        <div className="flex flex-col gap-3 md:flex-row md:items-center">
          <nav className="flex gap-1 overflow-x-auto rounded-full border border-[color:var(--border)] bg-[rgba(255,251,244,0.78)] p-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href;
              const label = t(item.key);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex shrink-0 items-center gap-2 rounded-full px-3 py-2 text-sm transition",
                    active
                      ? "border border-[rgba(10,102,194,0.22)] bg-[rgba(10,102,194,0.12)] text-[color:var(--brand-blue)] shadow-sm"
                      : "text-[color:var(--muted)] hover:bg-[color:var(--surface2)] hover:text-[color:var(--text)]"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label === item.key ? item.fallback : label}
                </Link>
              );
            })}
          </nav>
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
