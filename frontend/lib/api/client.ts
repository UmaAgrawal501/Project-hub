import { clearSession, getAccessToken } from "@/lib/auth/session";
import type {
  ApiError,
  Draft,
  Project,
  ProjectFile,
  ProjectStatus,
  ProjectSummary,
  PublicPortal,
  PublishResult,
  Resource,
  ResourceType,
  Session,
  Share,
  ShareState,
  User,
  VersionDetail,
  VersionSummary,
  Workspace,
} from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export class ApiClientError extends Error {
  code: string;
  status: number;
  details: ApiError["error"]["details"];

  constructor(status: number, payload: ApiError) {
    super(payload.error.message);
    this.status = status;
    this.code = payload.error.code;
    this.details = payload.error.details ?? [];
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && options.auth !== false) {
      clearSession();
    }
    const errorPayload =
      payload && typeof payload === "object" && "error" in payload
        ? (payload as ApiError)
        : {
            error: {
              code: "internal_error",
              message: "Request failed",
              details: [],
            },
          };
    throw new ApiClientError(response.status, errorPayload);
  }

  return payload as T;
}

export async function signUp(input: {
  display_name: string;
  email: string;
  password: string;
}): Promise<{ user: User; workspace: Workspace; session: Session }> {
  const res = await request<{
    data: { user: User; workspace: Workspace; session: Session };
  }>("/auth/sign-up", {
    method: "POST",
    body: JSON.stringify(input),
    auth: false,
  });
  return res.data;
}

export async function signIn(input: {
  email: string;
  password: string;
}): Promise<{ user: User; workspace: Workspace; session: Session }> {
  const res = await request<{
    data: { user: User; workspace: Workspace; session: Session };
  }>("/auth/sign-in", {
    method: "POST",
    body: JSON.stringify(input),
    auth: false,
  });
  return res.data;
}

export async function signOut(): Promise<void> {
  try {
    await request<{ data: { ok: boolean } }>("/auth/sign-out", {
      method: "POST",
      body: JSON.stringify({}),
    });
  } finally {
    clearSession();
  }
}

export async function getMe(): Promise<{ user: User; workspace: Workspace }> {
  const res = await request<{ data: { user: User; workspace: Workspace } }>(
    "/auth/me",
  );
  return res.data;
}

export async function updateMe(input: {
  display_name: string;
}): Promise<User> {
  const res = await request<{ data: { user: User } }>("/auth/me", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  return res.data.user;
}

export async function changePassword(input: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  await request<{ data: { ok: boolean } }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function forgotPassword(input: { email: string }): Promise<void> {
  await request<{ data: { ok?: boolean; message?: string } }>(
    "/auth/forgot-password",
    {
      method: "POST",
      body: JSON.stringify(input),
      auth: false,
    },
  );
}

export async function resetPassword(input: {
  token: string;
  password: string;
}): Promise<void> {
  await request<{ data: { ok: boolean } }>("/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(input),
    auth: false,
  });
}

export async function listProjects(status: ProjectStatus): Promise<{
  data: ProjectSummary[];
  meta: { limit: number; offset: number; total: number };
}> {
  return request(`/projects?status=${status}`);
}

export async function createProject(input: {
  name: string;
  overview?: string;
}): Promise<Project> {
  const res = await request<{ data: Project }>("/projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
  return res.data;
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await request<{ data: Project }>(`/projects/${projectId}`);
  return res.data;
}

export async function updateProject(
  projectId: string,
  input: {
    name?: string;
    status?: ProjectStatus;
  },
): Promise<Project> {
  const res = await request<{ data: Project }>(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  return res.data;
}

export async function deleteProject(projectId: string): Promise<void> {
  await request<{ data: { ok: boolean } }>(`/projects/${projectId}`, {
    method: "DELETE",
  });
}

export async function getDraft(projectId: string): Promise<Draft> {
  const res = await request<{ data: Draft }>(`/projects/${projectId}/draft`);
  return res.data;
}

export async function updateDraft(
  projectId: string,
  input: { overview: string | null },
): Promise<Draft> {
  const res = await request<{ data: Draft }>(`/projects/${projectId}/draft`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  return res.data;
}

export async function listDraftResources(projectId: string): Promise<Resource[]> {
  const res = await request<{ data: Resource[] }>(
    `/projects/${projectId}/draft/resources`,
  );
  return res.data;
}

export async function createDraftResource(
  projectId: string,
  input: {
    title: string;
    url: string;
    type: ResourceType;
    description?: string;
  },
): Promise<Resource> {
  const res = await request<{ data: Resource }>(
    `/projects/${projectId}/draft/resources`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
  return res.data;
}

export async function updateDraftResource(
  projectId: string,
  resourceId: string,
  input: {
    title?: string;
    url?: string;
    type?: ResourceType;
    description?: string | null;
    position?: number;
  },
): Promise<Resource> {
  const res = await request<{ data: Resource }>(
    `/projects/${projectId}/draft/resources/${resourceId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
    },
  );
  return res.data;
}

export async function deleteDraftResource(
  projectId: string,
  resourceId: string,
): Promise<void> {
  await request<{ data: { ok: boolean } }>(
    `/projects/${projectId}/draft/resources/${resourceId}`,
    { method: "DELETE" },
  );
}

export async function listDraftFiles(projectId: string): Promise<ProjectFile[]> {
  const res = await request<{ data: ProjectFile[] }>(
    `/projects/${projectId}/draft/files`,
  );
  return res.data;
}

export async function createDraftUploadUrl(
  projectId: string,
  input: { name: string; mime_type: string; size_bytes: number },
): Promise<{
  upload_url: string;
  token: string;
  expires_at: string;
}> {
  const res = await request<{
    data: {
      upload_url: string;
      token: string;
      expires_at: string;
    };
  }>(`/projects/${projectId}/draft/files/upload-url`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return res.data;
}

export async function confirmDraftUpload(
  projectId: string,
  input: {
    token: string;
    name: string;
    mime_type: string;
    size_bytes: number;
  },
): Promise<ProjectFile> {
  const res = await request<{ data: ProjectFile }>(
    `/projects/${projectId}/draft/files/confirm`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
  return res.data;
}

export async function createDraftDownloadUrl(
  projectId: string,
  fileId: string,
): Promise<{ download_url: string; expires_at: string; name: string }> {
  const res = await request<{
    data: { download_url: string; expires_at: string; name: string };
  }>(`/projects/${projectId}/draft/files/${fileId}/download-url`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  return res.data;
}

export async function deleteDraftFile(
  projectId: string,
  fileId: string,
): Promise<void> {
  await request<{ data: { ok: boolean } }>(
    `/projects/${projectId}/draft/files/${fileId}`,
    { method: "DELETE" },
  );
}

export async function uploadFileToSignedUrl(
  uploadUrl: string,
  file: File,
  requiredHeaders: Record<string, string>,
  onProgress?: (percent: number) => void,
): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", uploadUrl);
    Object.entries(requiredHeaders).forEach(([key, value]) => {
      xhr.setRequestHeader(key, value);
    });
    xhr.upload.onprogress = (event) => {
      if (!onProgress || !event.lengthComputable) return;
      onProgress(Math.round((event.loaded / event.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error("Upload to storage failed"));
    };
    xhr.onerror = () => reject(new Error("Upload to storage failed"));
    xhr.send(file);
  });
}

export async function publishProject(
  projectId: string,
  input: { release_notes: string },
): Promise<PublishResult> {
  const res = await request<{ data: PublishResult }>(
    `/projects/${projectId}/publish`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
  return res.data;
}

export async function listVersions(projectId: string): Promise<VersionSummary[]> {
  const res = await request<{ data: VersionSummary[] }>(
    `/projects/${projectId}/versions`,
  );
  return res.data;
}

export async function getVersion(
  projectId: string,
  versionNumber: number,
): Promise<VersionDetail> {
  const res = await request<{ data: VersionDetail }>(
    `/projects/${projectId}/versions/${versionNumber}`,
  );
  return res.data;
}

export async function createVersionDownloadUrl(
  projectId: string,
  versionNumber: number,
  fileId: string,
): Promise<{ download_url: string; expires_at: string; name: string }> {
  const res = await request<{
    data: { download_url: string; expires_at: string; name: string };
  }>(
    `/projects/${projectId}/versions/${versionNumber}/files/${fileId}/download-url`,
    {
      method: "POST",
      body: JSON.stringify({}),
    },
  );
  return res.data;
}

export async function listProjectShares(projectId: string): Promise<Share[]> {
  const res = await request<{ data: Share[] }>(
    `/projects/${projectId}/shares`,
  );
  return res.data;
}

export async function getShareState(projectId: string): Promise<ShareState> {
  const res = await request<{ data: ShareState }>(
    `/projects/${projectId}/share`,
  );
  return res.data;
}

export async function enableShare(projectId: string): Promise<ShareState> {
  const res = await request<{ data: ShareState }>(
    `/projects/${projectId}/share/enable`,
    { method: "POST", body: JSON.stringify({}) },
  );
  return res.data;
}

export async function disableShare(projectId: string): Promise<ShareState> {
  const res = await request<{ data: ShareState }>(
    `/projects/${projectId}/share/disable`,
    { method: "POST", body: JSON.stringify({}) },
  );
  return res.data;
}

export async function regenerateShare(projectId: string): Promise<ShareState> {
  const res = await request<{ data: ShareState }>(
    `/projects/${projectId}/share/regenerate`,
    { method: "POST", body: JSON.stringify({}) },
  );
  return res.data;
}

export async function getPublicPortal(token: string): Promise<PublicPortal> {
  const res = await request<{ data: PublicPortal }>(`/public/${token}`, {
    auth: false,
  });
  return res.data;
}

export async function getPublicPortalVersion(
  token: string,
  versionNumber: number,
): Promise<PublicPortal> {
  const res = await request<{ data: PublicPortal }>(
    `/public/${token}/versions/${versionNumber}`,
    { auth: false },
  );
  return res.data;
}

export async function createPublicDownloadUrl(
  token: string,
  fileId: string,
  versionNumber?: number,
): Promise<{ download_url: string; expires_at: string; name: string }> {
  const res = await request<{
    data: { download_url: string; expires_at: string; name: string };
  }>(`/public/${token}/files/${fileId}/download-url`, {
    method: "POST",
    body: JSON.stringify(
      versionNumber != null ? { version_number: versionNumber } : {},
    ),
    auth: false,
  });
  return res.data;
}
