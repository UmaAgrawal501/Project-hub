"use client";

import Link from "next/link";
import type { ProjectSummary } from "@/lib/types";

function formatUpdated(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "P";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase();
}

export function ProjectList({ projects }: { projects: ProjectSummary[] }) {
  return (
    <ul className="space-y-2">
      {projects.map((project) => (
        <li key={project.id}>
          <Link
            href={`/projects/${project.id}`}
            className="group flex items-center gap-4 rounded-md border border-border-subtle bg-surface px-4 py-4 transition-colors hover:border-border hover:bg-surface-hover"
          >
            <span
              aria-hidden
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-accent-muted text-caption font-semibold text-accent"
            >
              {initials(project.name)}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-body font-medium text-ink">{project.name}</p>
              <p className="mt-0.5 text-caption text-ink-tertiary">
                Updated {formatUpdated(project.updated_at)}
              </p>
            </div>
            <span
              aria-hidden
              className="text-ink-tertiary transition-colors group-hover:text-accent"
            >
              →
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
