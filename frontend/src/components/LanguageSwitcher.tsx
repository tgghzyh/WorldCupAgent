"use client";

import { useI18n } from "@/i18n";
import { Globe, ChevronDown } from "lucide-react";

export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  return (
    <div className="flex items-center gap-1 bg-[#1a2333] rounded-lg p-1">
      <button
        onClick={() => setLocale("en")}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
          locale === "en"
            ? "bg-[#58a6ff] text-white"
            : "text-[#768390] hover:text-[#cdd9e5]"
        }`}
        aria-label="Switch to English"
      >
        EN
      </button>
      <button
        onClick={() => setLocale("zh")}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
          locale === "zh"
            ? "bg-[#58a6ff] text-white"
            : "text-[#768390] hover:text-[#cdd9e5]"
        }`}
        aria-label="切换到中文"
      >
        中文
      </button>
    </div>
  );
}

export function LanguageSwitcherWithIcon() {
  const { locale, setLocale, t } = useI18n();

  return (
    <div className="relative group">
      <button
        className="flex items-center gap-2 px-3 py-2 bg-[#1a2333] hover:bg-[#1e2a3a] rounded-lg transition-colors"
        aria-label="Language"
      >
        <Globe className="w-4 h-4 text-[#768390]" />
        <span className="text-sm text-[#cdd9e5]">{locale === "zh" ? "中文" : "EN"}</span>
        <ChevronDown className="w-3 h-3 text-[#768390]" />
      </button>
      
      <div className="absolute right-0 mt-2 w-32 bg-[#1a2333] border border-[#1e2a3a] rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
        <button
          onClick={() => setLocale("en")}
          className={`w-full px-4 py-2 text-left text-sm hover:bg-[#1e2a3a] first:rounded-t-lg last:rounded-b-lg transition-colors ${
            locale === "en" ? "text-[#58a6ff]" : "text-[#cdd9e5]"
          }`}
        >
          English
        </button>
        <button
          onClick={() => setLocale("zh")}
          className={`w-full px-4 py-2 text-left text-sm hover:bg-[#1e2a3a] first:rounded-t-lg last:rounded-b-lg transition-colors ${
            locale === "zh" ? "text-[#58a6ff]" : "text-[#cdd9e5]"
          }`}
        >
          中文
        </button>
      </div>
    </div>
  );
}
