export type ProjectStatus = "active" | "completed" | "archived";

export type ResourceType =
  | "github"
  | "figma"
  | "production"
  | "staging"
  | "api_docs"
  | "postman"
  | "database_diagram"
  | "drive"
  | "other";

export type User = {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
  updated_at: string;
};

export type Workspace = {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type Session = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
};

export type Share = {
  id: string;
  project_id: string;
  version_number: number;
  token: string;
  is_enabled: boolean;
  public_path: string;
  created_at: string;
  updated_at: string;
};

export type ShareState = {
  enabled: boolean;
  share: Share | null;
};

export type DraftSummary = {
  overview: string | null;
  updated_at: string;
  has_unpublished_changes: boolean;
  file_count: number;
  resource_count: number;
};

export type ProjectSummary = {
  id: string;
  workspace_id: string;
  name: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
  latest_version_number: number | null;
  has_unpublished_changes: boolean;
};

export type Project = ProjectSummary & {
  draft: DraftSummary;
  share: Share | null;
};

export type Draft = {
  overview: string | null;
  updated_at: string;
  has_unpublished_changes: boolean;
};

export type Resource = {
  id: string;
  project_id: string;
  title: string;
  url: string;
  type: ResourceType;
  description: string | null;
  position: number;
  created_at: string;
  updated_at: string;
};

export type ProjectFile = {
  id: string;
  project_id: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

export type VersionSummary = {
  id: string;
  project_id: string;
  version_number: number;
  name: string;
  release_notes: string;
  overview: string | null;
  published_at: string;
};

export type Version = {
  id: string;
  project_id: string;
  version_number: number;
  name: string;
  release_notes: string;
  overview: string | null;
  published_at: string;
  published_by_user_id: string;
};

export type VersionFile = {
  id: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

export type VersionResource = {
  id: string;
  title: string;
  url: string;
  type: ResourceType;
  description: string | null;
  position: number;
};

export type VersionDetail = {
  version: Version;
  files: VersionFile[];
  resources: VersionResource[];
};

export type PublishResult = VersionDetail & {
  share: Share;
};

export type PublicPortalProject = {
  name: string;
  status: ProjectStatus;
};

export type PublicPortalVersion = {
  version_number: number;
  name: string;
  release_notes: string;
  overview: string | null;
  published_at: string;
};

export type PublicVersionRef = {
  version_number: number;
  published_at: string;
};

export type PublicFile = {
  id: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

export type PublicResource = {
  id: string;
  title: string;
  url: string;
  type: ResourceType;
  description: string | null;
  position: number;
};

export type PublicPortal = {
  project: PublicPortalProject;
  version: PublicPortalVersion;
  resources: PublicResource[];
  files: PublicFile[];
  versions_available: PublicVersionRef[];
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    details: Array<{ field: string; message: string; code: string }>;
  };
};
