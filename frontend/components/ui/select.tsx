import type { SelectHTMLAttributes } from "react";

export function Select({
  className = "",
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`h-9 w-full rounded-sm border border-border bg-surface px-3 text-body text-ink ${className}`}
      {...props}
    >
      {children}
    </select>
  );
}
