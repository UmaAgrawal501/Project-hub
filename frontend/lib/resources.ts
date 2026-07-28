import type { ResourceType } from "@/lib/types";

export const RESOURCE_TYPES: ResourceType[] = [
  "github",
  "figma",
  "production",
  "staging",
  "api_docs",
  "postman",
  "database_diagram",
  "drive",
  "other",
];

const LABELS: Record<ResourceType, string> = {
  github: "GitHub",
  figma: "Figma",
  production: "Production",
  staging: "Staging",
  api_docs: "API docs",
  postman: "Postman",
  database_diagram: "Database diagram",
  drive: "Drive",
  other: "Other",
};

export function resourceTypeLabel(type: ResourceType): string {
  return LABELS[type];
}
