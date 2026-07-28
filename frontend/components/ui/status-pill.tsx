import type { ProjectStatus } from "@/lib/types";

const styles: Record<ProjectStatus, string> = {
  active: "bg-accent-muted text-accent",
  completed: "bg-surface-hover text-ink-secondary",
  archived: "border border-border text-ink-tertiary",
};

export function StatusPill({ status }: { status: ProjectStatus }) {
  const label =
    status === "active" ? "Active" : status === "completed" ? "Completed" : "Archived";
  return (
    <span
      className={`inline-flex rounded-sm px-2 py-0.5 text-caption capitalize ${styles[status]}`}
    >
      {label}
    </span>
  );
}
