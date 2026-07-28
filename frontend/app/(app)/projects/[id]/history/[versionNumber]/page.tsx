"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  ApiClientError,
  createVersionDownloadUrl,
  getVersion,
} from "@/lib/api/client";
import { resourceTypeLabel } from "@/lib/resources";
import type { VersionDetail, VersionFile } from "@/lib/types";

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function VersionDetailPage() {
  const params = useParams<{ id: string; versionNumber: string }>();
  const projectId = params.id;
  const versionNumber = Number(params.versionNumber);

  const [detail, setDetail] = useState<VersionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!projectId || !Number.isFinite(versionNumber)) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getVersion(projectId, versionNumber);
      setDetail(data);
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to load version");
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [projectId, versionNumber]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onDownload(file: VersionFile) {
    if (!projectId) return;
    setDownloadingId(file.id);
    try {
      const data = await createVersionDownloadUrl(
        projectId,
        versionNumber,
        file.id,
      );
      window.open(data.download_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to download file");
    } finally {
      setDownloadingId(null);
    }
  }

  if (loading) {
    return <p className="text-body text-ink-secondary">Loading version…</p>;
  }

  if (error || !detail) {
    return (
      <div>
        <Link
          href={`/projects/${projectId}`}
          className="text-caption text-ink-secondary hover:text-ink"
        >
          ← Project Editor
        </Link>
        <p className="mt-4 text-body text-danger">{error ?? "Version not found"}</p>
      </div>
    );
  }

  const { version, files, resources } = detail;

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href={`/projects/${projectId}`}
        className="text-caption text-ink-secondary hover:text-ink"
      >
        ← Project Editor
      </Link>

      <h2 className="mt-4 text-title-2 text-ink">{version.name}</h2>
      <p className="mt-1 text-body text-ink-secondary">
        Version {version.version_number} · {formatDate(version.published_at)}
      </p>
      <p className="mt-2 text-caption text-ink-tertiary">Read-only published delivery</p>

      <section className="mt-8">
        <h3 className="text-title-3 text-ink">Release notes</h3>
        <p className="mt-2 whitespace-pre-wrap text-body text-ink-secondary">
          {version.release_notes}
        </p>
      </section>

      {version.overview ? (
        <section className="mt-8">
          <h3 className="text-title-3 text-ink">Overview</h3>
          <p className="mt-2 whitespace-pre-wrap text-body text-ink-secondary">
            {version.overview}
          </p>
        </section>
      ) : null}

      {resources.length > 0 ? (
        <section className="mt-8">
          <h3 className="text-title-3 text-ink">Resources</h3>
          <ul className="mt-3 space-y-3">
            {resources.map((resource) => (
              <li key={resource.id} className="rounded-md border border-border-subtle px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-sm bg-accent-muted px-2 py-0.5 text-caption text-accent">
                    {resourceTypeLabel(resource.type)}
                  </span>
                  <p className="text-body font-medium text-ink">{resource.title}</p>
                </div>
                <a
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 block truncate font-mono text-caption text-ink-tertiary hover:text-accent"
                >
                  {resource.url}
                </a>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {files.length > 0 ? (
        <section className="mt-8">
          <h3 className="text-title-3 text-ink">Files</h3>
          <ul className="mt-3 overflow-hidden rounded-md border border-border-subtle">
            {files.map((file) => (
              <li
                key={file.id}
                className="flex items-center justify-between gap-3 border-b border-border-subtle px-4 py-3 last:border-b-0"
              >
                <div className="min-w-0">
                  <p className="truncate text-body font-medium text-ink">{file.name}</p>
                  <p className="text-caption text-ink-tertiary">
                    {formatBytes(file.size_bytes)}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={downloadingId === file.id}
                  onClick={() => void onDownload(file)}
                >
                  {downloadingId === file.id ? "…" : "Download"}
                </Button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
