"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  ApiClientError,
  createPublicDownloadUrl,
  getPublicPortal,
} from "@/lib/api/client";
import type { PublicFile, PublicPortal } from "@/lib/types";

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function IconDownload({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M12 3v12" />
      <path d="m7 10 5 5 5-5" />
      <path d="M5 21h14" />
    </svg>
  );
}

function isPdf(file: PublicFile): boolean {
  return (
    file.mime_type === "application/pdf" ||
    file.name.toLowerCase().endsWith(".pdf")
  );
}

function isImage(file: PublicFile): boolean {
  return file.mime_type.startsWith("image/");
}

function canPreview(file: PublicFile): boolean {
  return isPdf(file) || isImage(file);
}

function downloadUrlWithFilename(url: string, filename: string): string {
  try {
    const parsed = new URL(url);
    parsed.searchParams.set("download", filename);
    return parsed.toString();
  } catch {
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}download=${encodeURIComponent(filename)}`;
  }
}

function Unavailable() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-16 text-center">
      <h1 className="text-title-1 text-ink">This link is no longer active</h1>
      <p className="mt-3 text-body text-ink-secondary">
        This delivery is unavailable. Contact the project owner if you still need
        access.
      </p>
    </main>
  );
}

export default function PublicSharePage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const [data, setData] = useState<PublicPortal | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    getPublicPortal(token)
      .then((payload) => {
        setData(payload);
        setUnavailable(false);
      })
      .catch(() => {
        setUnavailable(true);
        setData(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  // Auto-load signed URLs so PDF/images open on the page immediately.
  useEffect(() => {
    if (!token || !data) return;
    const previewable = data.files.filter(canPreview);
    if (previewable.length === 0) return;

    let cancelled = false;
    setPreviewError(null);

    void (async () => {
      const next: Record<string, string> = {};
      try {
        await Promise.all(
          previewable.map(async (file) => {
            const result = await createPublicDownloadUrl(
              token,
              file.id,
              data.version.version_number,
            );
            next[file.id] = result.download_url;
          }),
        );
        if (!cancelled) setPreviewUrls(next);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiClientError) setPreviewError(err.message);
        else setPreviewError("Unable to open files.");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [token, data]);

  async function onDownload(file: PublicFile) {
    if (!token || !data) return;
    setActionError(null);
    setBusyId(file.id);
    try {
      const cached = previewUrls[file.id];
      const url =
        cached ??
        (
          await createPublicDownloadUrl(
            token,
            file.id,
            data.version.version_number,
          )
        ).download_url;
      const forced = downloadUrlWithFilename(url, file.name);
      try {
        const res = await fetch(forced);
        if (!res.ok) throw new Error("fetch failed");
        const blob = await res.blob();
        const objectUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = objectUrl;
        a.download = file.name;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(objectUrl);
      } catch {
        window.open(forced, "_blank", "noopener,noreferrer");
      }
    } catch (err) {
      if (err instanceof ApiClientError) setActionError(err.message);
      else setActionError("Unable to download file. Try again.");
    } finally {
      setBusyId(null);
    }
  }

  if (loading && !data) {
    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <p className="text-body text-ink-secondary">Loading…</p>
      </main>
    );
  }

  if (unavailable || !data) {
    return <Unavailable />;
  }

  const { project, resources, files } = data;
  const previewFiles = files.filter(canPreview);
  const otherFiles = files.filter((f) => !canPreview(f));
  const empty = files.length === 0 && resources.length === 0;

  return (
    <main className="mx-auto min-h-screen w-full max-w-4xl px-4 py-8 sm:px-6 sm:py-10">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-title-2 text-ink">{project.name}</h1>
        </div>
      </header>

      {actionError || previewError ? (
        <p className="mb-4 text-caption text-danger">
          {actionError ?? previewError}
        </p>
      ) : null}

      {empty ? (
        <p className="text-body text-ink-secondary">Nothing shared yet.</p>
      ) : null}

      {previewFiles.map((file) => {
        const url = previewUrls[file.id];
        return (
          <section key={file.id} className="mb-8">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate text-body font-medium text-ink">
                  {file.name}
                </p>
                <p className="text-caption text-ink-tertiary">
                  {formatBytes(file.size_bytes)}
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-9 w-9 px-0"
                aria-label={`Download ${file.name}`}
                title="Download"
                disabled={busyId === file.id}
                onClick={() => void onDownload(file)}
              >
                {busyId === file.id ? (
                  <span className="text-caption">…</span>
                ) : (
                  <IconDownload />
                )}
              </Button>
            </div>

            <div className="overflow-hidden rounded-md border border-border-subtle bg-surface">
              {!url ? (
                <div className="flex min-h-[70vh] items-center justify-center px-4">
                  <p className="text-body text-ink-secondary">Opening file…</p>
                </div>
              ) : isPdf(file) ? (
                <iframe
                  title={file.name}
                  src={url}
                  className="h-[75vh] w-full bg-white"
                />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={url}
                  alt={file.name}
                  className="mx-auto max-h-[75vh] w-auto max-w-full object-contain"
                />
              )}
            </div>
          </section>
        );
      })}

      {otherFiles.length > 0 ? (
        <section className="mb-8">
          <h2 className="text-title-3 text-ink">Other files</h2>
          <ul className="mt-4 divide-y divide-border-subtle overflow-hidden rounded-md border border-border-subtle bg-surface">
            {otherFiles.map((file) => (
              <li
                key={file.id}
                className="flex items-center justify-between gap-3 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="truncate text-body font-medium text-ink">
                    {file.name}
                  </p>
                  <p className="text-caption text-ink-tertiary">
                    {formatBytes(file.size_bytes)}
                  </p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-9 w-9 px-0"
                  aria-label={`Download ${file.name}`}
                  title="Download"
                  disabled={busyId === file.id}
                  onClick={() => void onDownload(file)}
                >
                  <IconDownload />
                </Button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {resources.length > 0 ? (
        <section className="mb-8">
          <h2 className="text-title-3 text-ink">Links</h2>
          <ul className="mt-4 divide-y divide-border-subtle overflow-hidden rounded-md border border-border-subtle bg-surface">
            {resources.map((resource) => (
              <li key={resource.id} className="px-4 py-3">
                <a
                  href={resource.url}
                  target="_blank"
                  rel="noreferrer"
                  className="block min-h-11 text-body font-medium text-ink hover:text-accent"
                >
                  {resource.title}
                </a>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </main>
  );
}
