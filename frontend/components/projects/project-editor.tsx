"use client";

import Link from "next/link";
import {
  DragEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { showToast } from "@/components/ui/toast";
import { AddLinkDialog } from "@/components/projects/add-link-dialog";
import {
  ApiClientError,
  confirmDraftUpload,
  createDraftDownloadUrl,
  createDraftUploadUrl,
  deleteDraftFile,
  deleteDraftResource,
  deleteProject,
  getProject,
  listDraftFiles,
  listDraftResources,
  listProjectShares,
  listVersions,
  publishProject,
  updateProject,
  uploadFileToSignedUrl,
} from "@/lib/api/client";
import type { Project, ProjectFile, Resource, Share, VersionSummary } from "@/lib/types";

type EditorTab = "files" | "versions" | "delete";

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

function excerpt(text: string, max = 140): string {
  const cleaned = text.trim();
  if (cleaned.length <= max) return cleaned;
  return `${cleaned.slice(0, max).trimEnd()}…`;
}

function resolveMimeType(file: File): string {
  if (file.type) return file.type;
  const ext = file.name.split(".").pop()?.toLowerCase();
  const byExt: Record<string, string> = {
    pdf: "application/pdf",
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    webp: "image/webp",
    gif: "image/gif",
    zip: "application/zip",
    doc: "application/msword",
    docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    xls: "application/vnd.ms-excel",
    xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    txt: "text/plain",
  };
  return byExt[ext ?? ""] ?? "application/octet-stream";
}

function publicUrl(path: string): string {
  if (typeof window === "undefined") return path;
  return `${window.location.origin}${path}`;
}

function IconCopy({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <rect x="9" y="9" width="13" height="13" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function IconDownload({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
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

function IconTrash({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M3 6h18" />
      <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </svg>
  );
}

export function ProjectEditor({ projectId }: { projectId: string }) {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [tab, setTab] = useState<EditorTab>("files");
  const [project, setProject] = useState<Project | null>(null);
  const [name, setName] = useState("");
  const [nameDirty, setNameDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(true);
  const [filesError, setFilesError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [deletingFile, setDeletingFile] = useState<ProjectFile | null>(null);
  const [deleteFileLoading, setDeleteFileLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const [links, setLinks] = useState<Resource[]>([]);
  const [linksLoading, setLinksLoading] = useState(true);
  const [addLinkOpen, setAddLinkOpen] = useState(false);
  const [deletingLink, setDeletingLink] = useState<Resource | null>(null);
  const [deleteLinkLoading, setDeleteLinkLoading] = useState(false);

  const [versions, setVersions] = useState<VersionSummary[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(true);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [sharesByVersion, setSharesByVersion] = useState<Record<number, Share>>(
    {},
  );

  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [publicLink, setPublicLink] = useState<string | null>(null);

  const refreshProject = useCallback(async () => {
    const data = await getProject(projectId);
    setProject(data);
    return data;
  }, [projectId]);

  const loadFiles = useCallback(async () => {
    setFilesLoading(true);
    setFilesError(null);
    try {
      setFiles(await listDraftFiles(projectId));
    } catch (err) {
      if (err instanceof ApiClientError) setFilesError(err.message);
      else setFilesError("Unable to load files");
      setFiles([]);
    } finally {
      setFilesLoading(false);
    }
  }, [projectId]);

  const loadLinks = useCallback(async () => {
    setLinksLoading(true);
    try {
      setLinks(await listDraftResources(projectId));
    } catch {
      setLinks([]);
    } finally {
      setLinksLoading(false);
    }
  }, [projectId]);

  const loadVersions = useCallback(async () => {
    setVersionsLoading(true);
    setVersionsError(null);
    try {
      const [versionRows, shareRows] = await Promise.all([
        listVersions(projectId),
        listProjectShares(projectId),
      ]);
      setVersions(versionRows);
      const map: Record<number, Share> = {};
      for (const share of shareRows) {
        map[share.version_number] = share;
      }
      setSharesByVersion(map);
    } catch (err) {
      if (err instanceof ApiClientError) setVersionsError(err.message);
      else setVersionsError("Unable to load versions");
      setVersions([]);
      setSharesByVersion({});
    } finally {
      setVersionsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    setPageLoading(true);
    getProject(projectId)
      .then((proj) => {
        setProject(proj);
        setName(proj.name);
        setNameDirty(false);
        setPageError(null);
        if (proj.share?.is_enabled && proj.share.public_path) {
          setPublicLink(publicUrl(proj.share.public_path));
        }
      })
      .catch((err) => {
        if (err instanceof ApiClientError) setPageError(err.message);
        else setPageError("Unable to load project");
        setProject(null);
      })
      .finally(() => setPageLoading(false));

    void loadFiles();
    void loadLinks();
    void loadVersions();
  }, [projectId, loadFiles, loadLinks, loadVersions]);

  async function saveNameIfNeeded(): Promise<Project | null> {
    if (!project) return null;
    const trimmed = name.trim();
    if (!trimmed) {
      setActionError("Project name is required");
      return null;
    }
    if (!nameDirty && trimmed === project.name) return project;
    const updated = await updateProject(projectId, { name: trimmed });
    setProject(updated);
    setName(updated.name);
    setNameDirty(false);
    return updated;
  }

  async function onSave() {
    setActionError(null);
    setSaving(true);
    try {
      const saved = await saveNameIfNeeded();
      if (!saved) return;
      showToast("success", "Saved");
    } catch (err) {
      if (err instanceof ApiClientError) setActionError(err.message);
      else setActionError("Unable to save");
    } finally {
      setSaving(false);
    }
  }

  async function onPublish() {
    setActionError(null);
    if (files.length < 1 && links.length < 1) {
      setActionError("Add a file or link before publishing");
      return;
    }
    setPublishing(true);
    try {
      const saved = await saveNameIfNeeded();
      if (!saved) return;

      const nextNumber = (saved.latest_version_number ?? 0) + 1;
      const result = await publishProject(projectId, {
        release_notes: `Version ${nextNumber}`,
      });
      const link =
        result.share?.public_path != null
          ? publicUrl(result.share.public_path)
          : null;
      setPublicLink(link);
      setProject(await refreshProject());
      await loadVersions();
      showToast(
        "success",
        link
          ? `Published Version ${result.version.version_number} — new link ready`
          : `Published Version ${result.version.version_number}`,
      );
    } catch (err) {
      if (err instanceof ApiClientError) setActionError(err.message);
      else setActionError("Unable to publish");
    } finally {
      setPublishing(false);
    }
  }

  async function uploadOne(file: File) {
    const mimeType = resolveMimeType(file);
    const intent = await createDraftUploadUrl(projectId, {
      name: file.name,
      mime_type: mimeType,
      size_bytes: file.size,
    });
    await uploadFileToSignedUrl(
      intent.upload_url,
      file,
      { "Content-Type": mimeType },
      (percent) => setUploadProgress(percent),
    );
    const saved = await confirmDraftUpload(projectId, {
      token: intent.token,
      name: file.name,
      mime_type: mimeType,
      size_bytes: file.size,
    });
    setFiles((prev) => [saved, ...prev.filter((item) => item.id !== saved.id)]);
  }

  async function onUploadFiles(fileList: FileList | File[] | null) {
    if (!fileList || fileList.length === 0) return;
    const list = Array.from(fileList);
    setUploadError(null);
    setUploading(true);
    setUploadProgress(0);
    try {
      for (const file of list) {
        await uploadOne(file);
      }
      await refreshProject();
    } catch (err) {
      if (err instanceof ApiClientError) setUploadError(err.message);
      else if (err instanceof Error) setUploadError(err.message);
      else setUploadError("Unable to upload file");
    } finally {
      setUploading(false);
      setUploadProgress(null);
      setDragOver(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function onDragOver(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(true);
  }

  function onDragLeave(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    void onUploadFiles(e.dataTransfer.files);
  }

  async function onDownloadFile(file: ProjectFile) {
    setDownloadingId(file.id);
    setUploadError(null);
    try {
      const data = await createDraftDownloadUrl(projectId, file.id);
      window.open(data.download_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      if (err instanceof ApiClientError) setUploadError(err.message);
      else setUploadError("Unable to download file");
    } finally {
      setDownloadingId(null);
    }
  }

  async function onConfirmDeleteFile() {
    if (!deletingFile) return;
    setDeleteFileLoading(true);
    try {
      await deleteDraftFile(projectId, deletingFile.id);
      setFiles((prev) => prev.filter((item) => item.id !== deletingFile.id));
      setDeletingFile(null);
      await refreshProject();
    } catch (err) {
      if (err instanceof ApiClientError) setUploadError(err.message);
      else setUploadError("Unable to delete file");
    } finally {
      setDeleteFileLoading(false);
    }
  }

  async function onConfirmDeleteLink() {
    if (!deletingLink) return;
    setDeleteLinkLoading(true);
    try {
      await deleteDraftResource(projectId, deletingLink.id);
      setLinks((prev) => prev.filter((item) => item.id !== deletingLink.id));
      setDeletingLink(null);
      await refreshProject();
    } catch (err) {
      if (err instanceof ApiClientError) showToast("error", err.message);
      else showToast("error", "Unable to delete link");
    } finally {
      setDeleteLinkLoading(false);
    }
  }

  async function onDeleteProject() {
    setDeleting(true);
    try {
      await deleteProject(projectId);
      showToast("success", "Project deleted");
      router.push("/projects");
    } catch (err) {
      if (err instanceof ApiClientError) showToast("error", err.message);
      else showToast("error", "Unable to delete project");
    } finally {
      setDeleting(false);
      setDeleteConfirmOpen(false);
    }
  }

  async function copyText(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      showToast("success", "Link copied");
    } catch {
      showToast("error", "Unable to copy link");
    }
  }

  async function onCopyDeliveryLink() {
    if (publicLink) {
      await copyText(publicLink);
      return;
    }
    if (project?.share?.is_enabled && project.share.public_path) {
      await copyText(publicUrl(project.share.public_path));
      return;
    }
    showToast("error", "Publish to create a delivery link");
  }

  if (pageLoading) {
    return <p className="text-body text-ink-secondary">Loading project…</p>;
  }

  if (pageError || !project) {
    return (
      <div>
        <Link href="/projects" className="text-caption text-ink-secondary hover:text-ink">
          ← Projects
        </Link>
        <p className="mt-4 text-body text-danger">{pageError ?? "Project not found"}</p>
      </div>
    );
  }

  const navItems: { id: EditorTab; label: string }[] = [
    { id: "files", label: "Files" },
    { id: "versions", label: "Versions" },
    { id: "delete", label: "Delete project" },
  ];

  return (
    <div>
      <Link href="/projects" className="text-caption text-ink-secondary hover:text-ink">
        ← Projects
      </Link>

      {/* Title + Save / Publish */}
      <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <input
          id="project-name"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setNameDirty(true);
            setActionError(null);
          }}
          aria-label="Project name"
          maxLength={120}
          className="w-full max-w-xl border-0 bg-transparent p-0 text-title-2 font-semibold text-ink outline-none placeholder:text-ink-tertiary focus:ring-0"
          placeholder="Project name"
        />
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            type="button"
            variant="secondary"
            disabled={saving || publishing}
            onClick={() => void onSave()}
          >
            {saving ? "Saving…" : "Save"}
          </Button>
          <Button
            type="button"
            disabled={saving || publishing}
            onClick={() => void onPublish()}
          >
            {publishing ? "Publishing…" : "Publish"}
          </Button>
        </div>
      </div>

      {actionError ? (
        <p className="mt-2 text-caption text-danger">{actionError}</p>
      ) : null}

      <div className="mt-8 flex flex-col gap-8 lg:flex-row lg:items-start">
        <aside className="w-full shrink-0 lg:w-48">
          <nav className="flex flex-row gap-2 overflow-x-auto lg:flex-col lg:gap-1">
            {navItems.map((item) => {
              const active = tab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setTab(item.id)}
                  className={`min-h-11 rounded-sm px-3 py-2 text-left text-body ${
                    active
                      ? "bg-accent-muted text-accent"
                      : item.id === "delete"
                        ? "text-danger hover:bg-surface-hover"
                        : "text-ink-secondary hover:bg-surface-hover hover:text-ink"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>
        </aside>

        <div className="min-w-0 flex-1">
          {tab === "files" ? (
            <section>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-title-3 text-ink">Files</h2>
                  <p className="mt-1 text-body text-ink-secondary">
                    Upload files or add links, then Save or Publish.
                  </p>
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setAddLinkOpen(true)}
                >
                  Add link
                </Button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                multiple
                onChange={(e) => void onUploadFiles(e.target.files)}
              />

              <div
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                className={`mt-4 flex flex-col items-center justify-center rounded-md border border-dashed px-6 py-12 text-center transition-colors ${
                  dragOver
                    ? "border-accent bg-accent-muted"
                    : "border-border bg-surface"
                }`}
              >
                <p className="text-body text-ink">Drag and drop files here</p>
                <p className="mt-1 text-caption text-ink-tertiary">or</p>
                <Button
                  type="button"
                  variant="secondary"
                  className="mt-3"
                  disabled={uploading}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {uploading ? "Uploading…" : "Choose files"}
                </Button>
              </div>

              {uploading && uploadProgress !== null ? (
                <div className="mt-4 rounded-md border border-border-subtle px-4 py-3">
                  <p className="text-caption text-ink-secondary">
                    Uploading… {uploadProgress}%
                  </p>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-sm bg-surface-hover">
                    <div
                      className="h-full bg-accent transition-[width]"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              ) : null}

              {uploadError ? (
                <p className="mt-3 text-caption text-danger">{uploadError}</p>
              ) : null}

              {filesLoading ? (
                <p className="mt-4 text-body text-ink-secondary">Loading files…</p>
              ) : filesError ? (
                <div className="mt-4">
                  <p className="text-body text-danger">{filesError}</p>
                  <Button
                    type="button"
                    variant="secondary"
                    className="mt-3"
                    onClick={() => void loadFiles()}
                  >
                    Retry
                  </Button>
                </div>
              ) : files.length === 0 ? (
                <p className="mt-4 text-body text-ink-secondary">No files yet.</p>
              ) : (
                <ul className="mt-4 divide-y divide-border-subtle overflow-hidden rounded-md border border-border-subtle">
                  {files.map((file) => (
                    <li
                      key={file.id}
                      className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-body font-medium text-ink">
                          {file.name}
                        </p>
                        <p className="mt-0.5 text-caption text-ink-tertiary">
                          {formatBytes(file.size_bytes)} · {formatDate(file.created_at)}
                        </p>
                      </div>
                      <div className="flex shrink-0 items-center gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-11 w-11 px-0"
                          aria-label={`Copy delivery link for ${file.name}`}
                          title="Copy link"
                          onClick={() => void onCopyDeliveryLink()}
                        >
                          <IconCopy />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-11 w-11 px-0"
                          aria-label={`Download ${file.name}`}
                          title="Download"
                          disabled={downloadingId === file.id}
                          onClick={() => void onDownloadFile(file)}
                        >
                          {downloadingId === file.id ? (
                            <span className="text-caption">…</span>
                          ) : (
                            <IconDownload />
                          )}
                        </Button>
                        <Button
                          type="button"
                          variant="danger"
                          size="sm"
                          className="h-11 w-11 px-0"
                          aria-label={`Delete ${file.name}`}
                          title="Delete"
                          onClick={() => setDeletingFile(file)}
                        >
                          <IconTrash />
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}

              <div className="mt-8">
                <h3 className="text-body font-medium text-ink">Links</h3>
                {linksLoading ? (
                  <p className="mt-2 text-body text-ink-secondary">Loading links…</p>
                ) : links.length === 0 ? (
                  <p className="mt-2 text-body text-ink-secondary">No links yet.</p>
                ) : (
                  <ul className="mt-3 divide-y divide-border-subtle overflow-hidden rounded-md border border-border-subtle">
                    {links.map((link) => (
                      <li
                        key={link.id}
                        className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="min-w-0">
                          <p className="text-body font-medium text-ink">{link.title}</p>
                          <a
                            href={link.url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-0.5 block truncate font-mono text-caption text-ink-tertiary hover:text-accent"
                          >
                            {link.url}
                          </a>
                        </div>
                        <Button
                          type="button"
                          variant="danger"
                          size="sm"
                          className="h-11 w-11 px-0"
                          aria-label={`Delete ${link.title}`}
                          title="Delete"
                          onClick={() => setDeletingLink(link)}
                        >
                          <IconTrash />
                        </Button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </section>
          ) : null}

          {tab === "versions" ? (
            <section>
              <h2 className="text-title-3 text-ink">Versions</h2>
              <p className="mt-1 text-body text-ink-secondary">
                Use the copy icon for the client link. Details is only for you.
              </p>
              {versionsLoading ? (
                <p className="mt-4 text-body text-ink-secondary">Loading versions…</p>
              ) : versionsError ? (
                <div className="mt-4">
                  <p className="text-body text-danger">{versionsError}</p>
                  <Button
                    type="button"
                    variant="secondary"
                    className="mt-3"
                    onClick={() => void loadVersions()}
                  >
                    Retry
                  </Button>
                </div>
              ) : versions.length === 0 ? (
                <p className="mt-4 text-body text-ink-secondary">
                  No versions yet. Click Publish when you are ready.
                </p>
              ) : (
                <ul className="mt-4 divide-y divide-border-subtle overflow-hidden rounded-md border border-border-subtle">
                  {versions.map((version) => {
                    const share = sharesByVersion[version.version_number];
                    const link =
                      share?.is_enabled && share.public_path
                        ? publicUrl(share.public_path)
                        : null;
                    return (
                      <li
                        key={version.id}
                        className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-start sm:justify-between"
                      >
                        <div className="min-w-0">
                          <p className="text-body font-medium text-ink">
                            Version {version.version_number}
                            <span className="ml-2 text-caption font-normal text-ink-tertiary">
                              {formatDate(version.published_at)}
                            </span>
                          </p>
                          <p className="mt-2 text-body text-ink-secondary">
                            {excerpt(version.release_notes)}
                          </p>
                          {link ? (
                            <p className="mt-2 truncate font-mono text-caption text-ink-tertiary">
                              {link}
                            </p>
                          ) : null}
                        </div>
                        <div className="flex shrink-0 items-center gap-1">
                          {link ? (
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="h-11 w-11 px-0"
                              aria-label={`Copy link for Version ${version.version_number}`}
                              title="Copy link"
                              onClick={() => void copyText(link)}
                            >
                              <IconCopy />
                            </Button>
                          ) : null}
                          <Link
                            href={`/projects/${projectId}/history/${version.version_number}`}
                          >
                            <Button type="button" variant="secondary" size="sm">
                              Details
                            </Button>
                          </Link>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
          ) : null}

          {tab === "delete" ? (
            <section>
              <h2 className="text-title-3 text-ink">Delete project</h2>
              <p className="mt-2 text-body text-ink-secondary">
                Removes “{project.name}” and turns off all delivery links. This cannot be
                undone.
              </p>
              <Button
                type="button"
                variant="danger"
                className="mt-6"
                onClick={() => setDeleteConfirmOpen(true)}
              >
                Delete project
              </Button>
            </section>
          ) : null}
        </div>
      </div>

      <ConfirmDialog
        open={Boolean(deletingFile)}
        title="Delete file?"
        body="Removes this file from the project. Published versions stay unchanged."
        loading={deleteFileLoading}
        onClose={() => {
          if (!deleteFileLoading) setDeletingFile(null);
        }}
        onConfirm={() => void onConfirmDeleteFile()}
      />

      <ConfirmDialog
        open={Boolean(deletingLink)}
        title="Delete link?"
        body="Removes this link from the project. Published versions stay unchanged."
        loading={deleteLinkLoading}
        onClose={() => {
          if (!deleteLinkLoading) setDeletingLink(null);
        }}
        onConfirm={() => void onConfirmDeleteLink()}
      />

      <AddLinkDialog
        open={addLinkOpen}
        projectId={projectId}
        onClose={() => setAddLinkOpen(false)}
        onSaved={(resource) => {
          setLinks((prev) => [...prev, resource]);
          void refreshProject();
        }}
      />

      <ConfirmDialog
        open={deleteConfirmOpen}
        title="Delete project?"
        body={`“${project.name}” will be removed and all delivery links will stop working.`}
        confirmLabel="Delete"
        loadingLabel="Deleting…"
        loading={deleting}
        danger
        onClose={() => {
          if (!deleting) setDeleteConfirmOpen(false);
        }}
        onConfirm={() => void onDeleteProject()}
      />
    </div>
  );
}
