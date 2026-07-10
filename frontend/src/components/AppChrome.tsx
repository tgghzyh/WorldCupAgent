export function AppChrome({ children }: { children: React.ReactNode }) {
  return <main className="page-shell text-text">{children}</main>;
}

export function PageIntro({
  eyebrow,
  title,
  description,
}: {
  eyebrow: React.ReactNode;
  title: React.ReactNode;
  description: React.ReactNode;
}) {
  return (
    <section className="mx-auto max-w-7xl px-5 pb-8 pt-14">
      <p className="text-sm font-medium text-accent">{eyebrow}</p>
      <h1 className="mt-3 max-w-4xl text-4xl font-semibold tracking-normal text-text md:text-6xl">
        {title}
      </h1>
      <p className="mt-5 max-w-2xl text-base leading-7 text-muted md:text-lg">
        {description}
      </p>
    </section>
  );
}

export function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="soft-card rounded-2xl p-5">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-text">{value}</p>
      <p className="mt-2 text-sm leading-6 text-muted">{detail}</p>
    </div>
  );
}

export function ProbabilityBar({
  home,
  draw,
  away,
}: {
  home: number;
  draw: number;
  away: number;
}) {
  return (
    <div className="overflow-hidden rounded-full border hairline bg-surface2/70">
      <div className="flex h-3 w-full">
        <span className="bg-green" style={{ width: `${home * 100}%` }} />
        <span className="bg-gold" style={{ width: `${draw * 100}%` }} />
        <span className="bg-red" style={{ width: `${away * 100}%` }} />
      </div>
    </div>
  );
}
