"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { FieldError, Input, Label } from "@/components/ui/form";
import { ApiClientError, createDraftResource } from "@/lib/api/client";
import type { Resource } from "@/lib/types";

export function AddLinkDialog({
  open,
  projectId,
  onClose,
  onSaved,
}: {
  open: boolean;
  projectId: string;
  onClose: () => void;
  onSaved: (resource: Resource) => void;
}) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    setTitle("");
    setUrl("");
    setError(null);
  }, [open]);

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
      const resource = await createDraftResource(projectId, {
        title: title.trim(),
        url: url.trim(),
        type: "other",
      });
      onSaved(resource);
      onClose();
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to add link");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} title="Add link" onClose={onClose}>
      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <Label htmlFor="link-title">Title</Label>
          <Input
            id="link-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Figma file"
            maxLength={120}
            autoFocus
          />
        </div>
        <div>
          <Label htmlFor="link-url">URL</Label>
          <Input
            id="link-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://"
            maxLength={2048}
          />
        </div>
        <FieldError>{error}</FieldError>
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? "Adding…" : "Add link"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
