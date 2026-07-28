import type { ProjectSummary } from "@/lib/types";

export function DeliveryBadges({
  project,
}: {
  project: Pick<
    ProjectSummary,
    "latest_version_number" | "has_unpublished_changes"
  >;
}) {
  const n = project.latest_version_number;
  if (n == null) {
    return (
      <span className="inline-flex rounded-sm border border-border px-2 py-0.5 text-caption text-ink-tertiary">
        Not published
      </span>
    );
  }
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5">
      <span className="inline-flex rounded-sm bg-accent-muted px-2 py-0.5 text-caption text-accent">
        v{n}
      </span>
      {project.has_unpublished_changes ? (
        <span className="inline-flex rounded-sm border border-border px-2 py-0.5 text-caption text-ink-secondary">
          Unpublished changes
        </span>
      ) : null}
    </span>
  );
}
