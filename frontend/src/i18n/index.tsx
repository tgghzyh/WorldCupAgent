/**
 * Internationalization (i18n) Hook and Context
 * Provides bilingual (Chinese/English) support for the WC2026 prediction system
 */

"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import zhTranslations from "./zh.json";
import enTranslations from "./en.json";

export type Locale = "zh" | "en";

type Translations = typeof zhTranslations;

// Context
interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  translations: Translations;
}

const I18nContext = createContext<I18nContextValue | null>(null);

// Provider
interface I18nProviderProps {
  children: React.ReactNode;
  defaultLocale?: Locale;
}

export function I18nProvider({ children, defaultLocale = "en" }: I18nProviderProps) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);

  const translations: Translations =
    locale === "zh" ? zhTranslations : enTranslations;

  // Load the saved locale after hydration so server and first client render match.
  useEffect(() => {
    const saved = localStorage.getItem("wc2026-locale");
    if (saved === "zh" || saved === "en") {
      window.setTimeout(() => setLocaleState(saved), 0);
    }
  }, []);

  const setLocale = useCallback((newLocale: Locale) => {
    localStorage.setItem("wc2026-locale", newLocale);
    setLocaleState(newLocale);
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      const keys = key.split(".");
      let value: unknown = translations;

      for (const k of keys) {
        if (value && typeof value === "object" && k in value) {
          value = (value as Record<string, unknown>)[k];
        } else {
          console.warn(`Translation key not found: ${key}`);
          return key;
        }
      }

      if (typeof value !== "string") {
        console.warn(`Translation value is not a string: ${key}`);
        return key;
      }

      // Replace parameters like {name} with actual values
      if (params) {
        return value.replace(/\{(\w+)\}/g, (_, paramKey) => {
          return params[paramKey]?.toString() ?? `{${paramKey}}`;
        });
      }

      return value;
    },
    [translations]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t, translations }}>
      {children}
    </I18nContext.Provider>
  );
}

// Hook
export function useI18n(): I18nContextValue {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within an I18nProvider");
  }
  return context;
}

// Hook for just translation function (lighter weight)
export function useTranslation() {
  const { t, locale, setLocale } = useI18n();
  return { t, locale, setLocale };
}

// Utility to get team name
export function getTeamName(teamName: string, locale: Locale): string {
  const teamKeyMap: Record<string, string> = {
    Argentina: "argentina",
    Brazil: "brazil",
    France: "france",
    England: "england",
    Germany: "germany",
    Spain: "spain",
    Italy: "italy",
    Portugal: "portugal",
    Netherlands: "netherlands",
    Belgium: "belgium",
    Croatia: "croatia",
    Uruguay: "uruguay",
    Colombia: "colombia",
    Mexico: "mexico",
    USA: "usa",
    Japan: "japan",
    Morocco: "morocco",
    Senegal: "senegal",
    Cameroon: "cameroon",
    Qatar: "qatar",
    Ecuador: "ecuador",
    Iran: "iran",
    Wales: "wales",
    Serbia: "serbia",
    Ghana: "ghana",
    Australia: "australia",
    "South Korea": "south_korea",
    Poland: "poland",
    Sweden: "sweden",
    Austria: "austria",
    Egypt: "egypt",
    Nigeria: "nigeria",
    "Ivory Coast": "ivory_coast",
    Greece: "greece",
    Denmark: "denmark",
    Tunisia: "tunisia",
    Peru: "peru",
    Paraguay: "paraguay",
    Panama: "panama",
    Bolivia: "bolivia",
    Algeria: "algeria",
    "South Africa": "south_africa",
    "Burkina Faso": "burkina_faso",
    "New Zealand": "new_zealand",
    Canada: "canada",
    "Costa Rica": "costa_rica",
    Jamaica: "jamaica",
    Zambia: "zambia",
  };

  const key = teamKeyMap[teamName];
  if (!key) return teamName;

  const allTranslations = locale === "zh" ? zhTranslations : enTranslations;
  const translated = (allTranslations.teams as Record<string, string>)[key];
  return translated || teamName;
}

// Utility to get stage name
export function getStageName(stage: string, locale: Locale): string {
  const stageKeyMap: Record<string, string> = {
    "Group Stage": "stages.group_stage",
    "Round of 32": "stages.round_of_32",
    "Round of 16": "stages.round_of_16",
    "Quarter-finals": "stages.quarter_finals",
    "Semi-finals": "stages.semi_finals",
    "Final": "stages.final",
    "Third Place": "stages.third_place",
  };

  const key = stageKeyMap[stage];
  if (!key) return stage;

  const allTranslations = locale === "zh" ? zhTranslations : enTranslations;
  const keys = key.split(".");
  let value: unknown = allTranslations;
  for (const k of keys) {
    value = (value as Record<string, unknown>)[k];
  }
  return (value as string) || stage;
}

// Utility to get confidence level
export function getConfidenceLevel(level: string, locale: Locale): string {
  const allTranslations = locale === "zh" ? zhTranslations : enTranslations;
  
  const levelMap: Record<string, string> = {
    high: "confidence.high",
    High: "confidence.high",
    medium: "confidence.medium",
    Medium: "confidence.medium",
    low: "confidence.low",
    Low: "confidence.low",
  };

  const key = levelMap[level];
  if (!key) return level;

  const keys = key.split(".");
  let value: unknown = allTranslations;
  for (const k of keys) {
    value = (value as Record<string, unknown>)[k];
  }
  return (value as string) || level;
}

// Re-export translations for direct access
export { zhTranslations, enTranslations };
