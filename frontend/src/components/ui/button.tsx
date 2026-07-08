import * as React from "react";
import { cn } from "@/lib/utils";

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className, type = "button", ...props }, ref) => (
  <button
    ref={ref}
    type={type}
      className={cn(
      "inline-flex h-9 items-center justify-center gap-2 rounded-full border border-[rgba(10,102,194,0.22)] bg-[color:var(--brand-blue)] px-4 text-sm font-medium text-white shadow-sm transition hover:translate-y-[-1px] hover:bg-[rgba(10,102,194,0.88)] hover:shadow-md disabled:pointer-events-none disabled:opacity-50",
      className
    )}
    {...props}
  />
));

Button.displayName = "Button";
