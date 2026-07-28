"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { CreateProjectModal } from "@/components/projects/create-project-modal";
import { EmptyDashboard } from "@/components/projects/empty-dashboard";
import { ProjectList } from "@/components/projects/project-list";
import { ApiClientError, listProjects } from "@/lib/api/client";
import type { ProjectStatus, ProjectSummary } from "@/lib/types";

const STATUSES: ProjectStatus[] = ["active", "completed", "archived"];

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await Promise.all(STATUSES.map((status) => listProjects(status)));
      const merged = results
        .flatMap((res) => res.data)
        .sort(
          (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
        );
      setProjects(merged);
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to load projects");
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="mb-8 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-title-1 text-ink">Projects</h1>
          {!loading && !error ? (
            <p className="mt-1 text-body text-ink-secondary">
              {projects.length === 0
                ? "No projects yet"
                : projects.length === 1
                  ? "1 project"
                  : `${projects.length} projects`}
            </p>
          ) : null}
        </div>
        <Button type="button" onClick={() => setCreateOpen(true)}>
          New project
        </Button>
      </div>

      {loading ? (
        <p className="text-body text-ink-secondary">Loading projects…</p>
      ) : error ? (
        <div className="rounded-md border border-border bg-surface px-4 py-6">
          <p className="text-body text-danger">{error}</p>
          <Button
            type="button"
            variant="secondary"
            className="mt-3"
            onClick={() => void load()}
          >
            Retry
          </Button>
        </div>
      ) : projects.length === 0 ? (
        <EmptyDashboard onCreate={() => setCreateOpen(true)} />
      ) : (
        <ProjectList projects={projects} />
      )}

      <CreateProjectModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(project) => {
          setCreateOpen(false);
          router.push(`/projects/${project.id}`);
        }}
      />
    </div>
  );
}
