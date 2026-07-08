"use client";

import { Globe } from "lucide-react";
import { useI18n } from "@/i18n";
import { cn } from "@/lib/utils";

export function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <div className="flex items-center gap-1 rounded-full border border-[color:var(--border)] bg-[rgba(255,251,244,0.78)] p-1">
      <Globe className="ml-2 h-4 w-4 text-[color:var(--muted)]" />
      <button
        onClick={() => setLocale("en")}
        className={cn(
          "rounded-full px-3 py-1.5 text-sm font-medium transition-all",
          locale === "en"
            ? "bg-[rgba(10,102,194,0.12)] text-[color:var(--brand-blue)]"
            : "text-[color:var(--muted)] hover:bg-[color:var(--surface2)] hover:text-[color:var(--text)]"
        )}
        aria-label="Switch to English"
      >
        EN
      </button>
      <button
        onClick={() => setLocale("zh")}
        className={cn(
          "rounded-full px-3 py-1.5 text-sm font-medium transition-all",
          locale === "zh"
            ? "bg-[rgba(10,102,194,0.12)] text-[color:var(--brand-blue)]"
            : "text-[color:var(--muted)] hover:bg-[color:var(--surface2)] hover:text-[color:var(--text)]"
        )}
        aria-label={t("language.switch_to_zh")}
      >
        中文
      </button>
    </div>
  );
}
