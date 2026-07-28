"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { FieldError, Input, Label, Textarea } from "@/components/ui/form";
import { Select } from "@/components/ui/select";
import { ApiClientError, createDraftResource, updateDraftResource } from "@/lib/api/client";
import { RESOURCE_TYPES, resourceTypeLabel } from "@/lib/resources";
import type { Resource, ResourceType } from "@/lib/types";

export function ResourceFormDialog({
  open,
  mode,
  initial,
  projectId,
  onClose,
  onSaved,
}: {
  open: boolean;
  mode: "create" | "edit";
  initial?: Resource | null;
  projectId: string;
  onClose: () => void;
  onSaved: (resource: Resource) => void;
}) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [type, setType] = useState<ResourceType>("github");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError(null);
    if (mode === "edit" && initial) {
      setTitle(initial.title);
      setUrl(initial.url);
      setType(initial.type);
      setDescription(initial.description ?? "");
    } else {
      setTitle("");
      setUrl("");
      setType("github");
      setDescription("");
    }
  }, [open, mode, initial]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim()) {
      setError("Title is required");
      return;
    }
    if (!url.trim()) {
      setError("URL is required");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        title: title.trim(),
        url: url.trim(),
        type,
        description: description.trim() || undefined,
      };
      const resource =
        mode === "create"
          ? await createDraftResource(projectId, payload)
          : await updateDraftResource(projectId, initial!.id, {
              ...payload,
              description: description.trim() ? description.trim() : null,
            });
      onSaved(resource);
      onClose();
      window.dispatchEvent(new CustomEvent("projecthub:project-refresh"));
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError(mode === "create" ? "Unable to add resource" : "Unable to save resource");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog
      open={open}
      title={mode === "create" ? "Add resource" : "Edit resource"}
      onClose={onClose}
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label htmlFor="resource-title">Title</Label>
          <Input
            id="resource-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={120}
            autoFocus
            required
          />
        </div>
        <div>
          <Label htmlFor="resource-url">URL</Label>
          <Input
            id="resource-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://"
            maxLength={2048}
            required
          />
        </div>
        <div>
          <Label htmlFor="resource-type">Type</Label>
          <Select
            id="resource-type"
            value={type}
            onChange={(e) => setType(e.target.value as ResourceType)}
          >
            {RESOURCE_TYPES.map((value) => (
              <option key={value} value={value}>
                {resourceTypeLabel(value)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label htmlFor="resource-description">Description</Label>
          <Textarea
            id="resource-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
            placeholder="Optional note"
          />
        </div>
        <FieldError>{error}</FieldError>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? "Saving…" : mode === "create" ? "Add" : "Save"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
