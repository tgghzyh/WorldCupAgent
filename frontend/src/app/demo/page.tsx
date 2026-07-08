import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { AppChrome, PageIntro } from "@/components/AppChrome";
import { demoSteps } from "@/lib/site-data";

export default function DemoPage() {
  return (
    <AppChrome>
      <PageIntro
        eyebrow="Judge-ready walkthrough"
        title="A three-minute product story."
        description="This page gives the demo a controlled rhythm: result, reasoning, bracket, trust. It is designed for someone who needs to understand the product quickly."
      />

      <section className="mx-auto grid max-w-7xl gap-5 px-5 pb-16 md:grid-cols-4">
        {demoSteps.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.title} className="soft-card rounded-[2rem] p-6">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">0{index + 1}</span>
                <Icon className="h-5 w-5 text-accent" />
              </div>
              <h2 className="mt-10 text-xl font-semibold">{step.title}</h2>
              <p className="mt-3 text-sm leading-6 text-muted">{step.text}</p>
            </div>
          );
        })}
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-16">
        <div className="glass-panel flex flex-col items-start justify-between gap-6 rounded-[2rem] p-8 md:flex-row md:items-center">
          <div>
            <p className="text-sm text-muted">Recommended opening</p>
            <p className="mt-2 max-w-2xl text-2xl font-semibold">
              Start on the homepage, open the featured match, then walk the champion path.
            </p>
          </div>
          <Link href="/" className="inline-flex items-center gap-2 rounded-full bg-text px-5 py-3 text-sm font-medium text-bg">
            Start demo
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </AppChrome>
  );
}
