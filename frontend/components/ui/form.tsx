import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

export function Label({
  htmlFor,
  children,
}: {
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-caption text-ink-secondary">
      {children}
    </label>
  );
}

export function Input({
  className = "",
  ...props
}: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`h-9 w-full rounded-sm border border-border bg-surface px-3 text-body text-ink placeholder:text-ink-tertiary ${className}`}
      {...props}
    />
  );
}

export function Textarea({
  className = "",
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`min-h-[88px] w-full rounded-sm border border-border bg-surface px-3 py-2 text-body text-ink placeholder:text-ink-tertiary ${className}`}
      {...props}
    />
  );
}

export function FieldError({
  id,
  children,
}: {
  id?: string;
  children?: React.ReactNode;
}) {
  if (!children) return null;
  return (
    <p id={id} className="mt-1.5 text-caption text-danger" role="alert">
      {children}
    </p>
  );
}
