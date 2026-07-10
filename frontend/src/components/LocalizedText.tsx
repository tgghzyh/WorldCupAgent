"use client";

import { getStageName, useI18n } from "@/i18n";

type LocalizedTextProps = {
  en: string;
  zh: string;
};

export function LocalizedText({ en, zh }: LocalizedTextProps) {
  const { locale } = useI18n();
  return <>{locale === "zh" ? zh : en}</>;
}

export function LocalizedStage({ stage }: { stage: string }) {
  const { locale } = useI18n();
  return <>{getStageName(stage, locale)}</>;
}
