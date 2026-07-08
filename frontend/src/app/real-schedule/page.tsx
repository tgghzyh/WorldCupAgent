"use client";

import { CalendarDays, ExternalLink, Globe2, MapPin, ShieldCheck, Trophy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useI18n } from "@/i18n";
import { realWorldCupSchedule } from "@/lib/real-schedule";

const dateFormatter = (locale: string) =>
  new Intl.DateTimeFormat(locale === "zh" ? "zh-CN" : "en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

export default function RealSchedulePage() {
  const { locale, t } = useI18n();
  const formatter = dateFormatter(locale);

  return (
    <main className="min-h-screen bg-[color:var(--bg)] text-[color:var(--text)]">
      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-8 md:px-6 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="rounded-lg border border-[color:var(--border)] bg-[linear-gradient(135deg,rgba(255,251,244,0.94),rgba(232,246,239,0.82))] p-6 shadow-sm md:p-8">
          <Badge className="mb-5 bg-white/70">
            <ShieldCheck className="mr-2 h-3.5 w-3.5 text-emerald-700" />
            {t("realSchedule.eyebrow")}
          </Badge>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-normal md:text-6xl">
            {t("realSchedule.title")}
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-[color:var(--muted)] md:text-lg">
            {t("realSchedule.description")}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Badge className="border-emerald-200 bg-emerald-50 text-emerald-800">
              {t("realSchedule.realBadge")}
            </Badge>
            <Badge className="bg-white/70">
              {t("realSchedule.verified", {
                date: realWorldCupSchedule.verifiedAt,
              })}
            </Badge>
          </div>
        </div>

        <Card className="bg-[color:var(--surface)]">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-full bg-[color:var(--brand-blue)] text-white">
                <Trophy className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold">{t("realSchedule.summaryTitle")}</p>
                <p className="text-xs text-[color:var(--muted)]">
                  {realWorldCupSchedule.summary.dateRange[locale]}
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {[
                [t("realSchedule.teams"), realWorldCupSchedule.summary.teams],
                [t("realSchedule.matches"), realWorldCupSchedule.summary.matches],
                [t("realSchedule.hostCities"), realWorldCupSchedule.summary.hostCities],
                [t("realSchedule.hostNations"), 3],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4"
                >
                  <p className="text-2xl font-semibold">{value}</p>
                  <p className="mt-1 text-xs text-[color:var(--muted)]">{label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-4 pb-8 md:px-6 lg:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <CalendarDays className="h-5 w-5 text-emerald-700" />
              <div>
                <h2 className="text-xl font-semibold">{t("realSchedule.milestones")}</h2>
                <p className="text-sm text-[color:var(--muted)]">{t("realSchedule.milestonesHint")}</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {realWorldCupSchedule.milestones.map((item) => (
              <article
                key={`${item.date}-${item.venue}`}
                className="rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.68)] p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">{item.title[locale]}</p>
                    <p className="mt-1 text-xs text-[color:var(--muted)]">
                      {formatter.format(new Date(`${item.date}T00:00:00`))}
                    </p>
                  </div>
                  <Badge className="border-amber-200 bg-amber-50 text-amber-900">{item.badge[locale]}</Badge>
                </div>
                <div className="mt-3 flex items-center gap-2 text-sm">
                  <MapPin className="h-4 w-4 text-rose-700" />
                  <span>{item.venue}</span>
                  <span className="text-[color:var(--muted)]">/ {item.location[locale]}</span>
                </div>
                <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">{item.description[locale]}</p>
              </article>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Globe2 className="h-5 w-5 text-sky-700" />
              <div>
                <h2 className="text-xl font-semibold">{t("realSchedule.phaseTitle")}</h2>
                <p className="text-sm text-[color:var(--muted)]">{t("realSchedule.phaseHint")}</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2">
              {realWorldCupSchedule.phases.map((phase) => (
                <article
                  key={phase.title.en}
                  className="rounded-lg border border-[color:var(--border)] bg-[color:var(--surface2)] p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold">{phase.title[locale]}</h3>
                      <p className="mt-1 text-xs text-[color:var(--muted)]">{phase.dateRange[locale]}</p>
                    </div>
                    <Badge>{t("realSchedule.matchCount", { count: phase.matches })}</Badge>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-[color:var(--muted)]">{phase.description[locale]}</p>
                </article>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-12 md:px-6">
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">{t("realSchedule.hostCityTitle")}</h2>
            <p className="text-sm text-[color:var(--muted)]">{t("realSchedule.hostCityHint")}</p>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {realWorldCupSchedule.hostCities.map((city) => (
                <article
                  key={`${city.country.en}-${city.city.en}`}
                  className="rounded-lg border border-[color:var(--border)] bg-[rgba(255,251,244,0.72)] p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{city.city[locale]}</p>
                      <p className="mt-1 text-xs text-[color:var(--muted)]">{city.country[locale]}</p>
                    </div>
                    <Badge>{city.role[locale]}</Badge>
                  </div>
                  <p className="mt-4 text-sm text-[color:var(--muted)]">{city.venue}</p>
                </article>
              ))}
            </div>

            <div className="mt-6 rounded-lg border border-dashed border-[color:var(--border)] bg-[color:var(--surface2)] p-4">
              <p className="text-sm leading-6 text-[color:var(--muted)]">{t("realSchedule.disclaimer")}</p>
              <div className="mt-4 flex flex-wrap gap-3">
                {realWorldCupSchedule.sources.map((source) => (
                  <a
                    key={source.url}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-full border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2 text-sm text-[color:var(--text)] transition hover:translate-y-[-1px]"
                  >
                    {source.label}
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
