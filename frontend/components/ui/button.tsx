import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const variantClass: Record<Variant, string> = {
  primary: "bg-accent text-ink-inverse hover:bg-accent-hover",
  secondary: "bg-surface text-ink border border-border hover:bg-surface-hover",
  ghost: "bg-transparent text-ink-secondary hover:bg-surface-hover hover:text-ink",
  danger: "bg-transparent text-danger hover:bg-[rgba(229,114,114,0.1)]",
};

const sizeClass: Record<Size, string> = {
  sm: "h-8 px-3 text-caption",
  md: "h-9 px-3.5 text-body font-medium",
  lg: "h-10 px-4 text-body font-medium",
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-md transition disabled:opacity-50 disabled:pointer-events-none ${variantClass[variant]} ${sizeClass[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
