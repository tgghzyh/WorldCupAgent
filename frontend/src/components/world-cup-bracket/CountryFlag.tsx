import Image from "next/image";
import type { Team } from "@/lib/world-cup-bracket/types";
import { cn } from "@/lib/utils";

type CountryFlagProps = {
  team: Team;
  className?: string;
};

export function CountryFlag({ team, className }: CountryFlagProps) {
  if (team.name === "TBD" || !team.flagCode) {
    return <span className={cn("inline-block text-center text-[color:var(--muted)]", className)}>?</span>;
  }

  return (
    <Image
      src={`https://flagcdn.com/w80/${team.flagCode}.png`}
      alt={`${team.name} flag`}
      className={cn("inline-block h-4 w-6 shrink-0 rounded-[2px] object-cover shadow-sm", className)}
      width={80}
      height={60}
      unoptimized
    />
  );
}
