import React from "react";
import { cn } from "../../lib/cn";

type BadgeVariant = "default" | "success" | "warning" | "danger";

export function Badge({ className, variant = "default", ...props }: React.HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }): JSX.Element {
  const variants: Record<BadgeVariant, string> = {
    default: "bg-gray-100 text-gray-900",
    success: "bg-green-100 text-green-800",
    warning: "bg-yellow-100 text-yellow-800",
    danger: "bg-red-100 text-red-800",
  };
  return <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", variants[variant], className)} {...props} />;
}