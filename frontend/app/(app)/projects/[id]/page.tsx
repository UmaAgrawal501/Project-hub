"use client";

import { useParams } from "next/navigation";
import { ProjectEditor } from "@/components/projects/project-editor";

export default function ProjectEditorPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;

  if (!projectId) {
    return <p className="text-body text-danger">Project not found</p>;
  }

  return <ProjectEditor projectId={projectId} />;
}
