import React from "react";
import { cn } from "../../lib/cn";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps): JSX.Element {
  return <input className={cn("input", className)} {...props} />;
}