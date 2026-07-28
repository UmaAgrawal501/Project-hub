"use client";

import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { FieldError, Input, Label } from "@/components/ui/form";
import { ApiClientError, createProject } from "@/lib/api/client";
import type { Project } from "@/lib/types";

export function CreateProjectModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (project: Project) => void;
}) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    setLoading(true);
    try {
      const project = await createProject({ name: name.trim() });
      setName("");
      onCreated(project);
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to create project");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} title="New project" onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label htmlFor="project-name">Project name</Label>
          <Input
            id="project-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Acme Website Redesign"
            autoFocus
            maxLength={120}
          />
        </div>
        <FieldError>{error}</FieldError>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? "Creating…" : "Create"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
