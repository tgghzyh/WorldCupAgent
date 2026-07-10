import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { AppChrome, PageIntro } from "@/components/AppChrome";
import { LocalizedText } from "@/components/LocalizedText";
import { demoSteps } from "@/lib/site-data";

export default function DemoPage() {
  return (
    <AppChrome>
      <PageIntro
        eyebrow={<LocalizedText en="Judge-ready walkthrough" zh="评审演示导览" />}
        title={<LocalizedText en="A three-minute product story." zh="三分钟了解产品。" />}
        description={<LocalizedText en="This page gives the demo a controlled rhythm: result, reasoning, bracket, trust. It is designed for someone who needs to understand the product quickly." zh="本页面按结果、推理、赛程树与可信度组织演示，帮助评审快速理解产品。" />}
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
              <h2 className="mt-10 text-xl font-semibold">
                <LocalizedText en={step.title} zh={step.titleZh} />
              </h2>
              <p className="mt-3 text-sm leading-6 text-muted">
                <LocalizedText en={step.text} zh={step.textZh} />
              </p>
            </div>
          );
        })}
      </section>

      <section className="mx-auto max-w-7xl px-5 pb-16">
        <div className="glass-panel flex flex-col items-start justify-between gap-6 rounded-[2rem] p-8 md:flex-row md:items-center">
          <div>
            <p className="text-sm text-muted"><LocalizedText en="Recommended opening" zh="建议演示顺序" /></p>
            <p className="mt-2 max-w-2xl text-2xl font-semibold">
              <LocalizedText en="Start on the homepage, open the featured match, then walk the champion path." zh="从首页开始，打开重点比赛，再查看冠军晋级路径。" />
            </p>
          </div>
          <Link href="/" className="inline-flex items-center gap-2 rounded-full bg-text px-5 py-3 text-sm font-medium text-bg">
            <LocalizedText en="Start demo" zh="开始演示" />
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>
    </AppChrome>
  );
}
