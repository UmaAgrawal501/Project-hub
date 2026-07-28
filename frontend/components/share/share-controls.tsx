"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { showToast } from "@/components/ui/toast";
import {
  ApiClientError,
  disableShare,
  enableShare,
  getShareState,
  regenerateShare,
} from "@/lib/api/client";
import type { Share, ShareState } from "@/lib/types";

function publicUrl(share: Share): string {
  if (typeof window === "undefined") return share.public_path;
  return `${window.location.origin}${share.public_path}`;
}

export function ShareControls({
  projectId,
  neverPublished = false,
}: {
  projectId: string;
  neverPublished?: boolean;
}) {
  const [state, setState] = useState<ShareState | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState<"disable" | "regenerate" | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getShareState(projectId);
      setState(data);
    } catch (err) {
      if (err instanceof ApiClientError) showToast("error", err.message);
      else showToast("error", "Unable to load share state");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onEnable() {
    setBusy(true);
    try {
      const data = await enableShare(projectId);
      setState(data);
      if (neverPublished) {
        showToast(
          "success",
          "Sharing enabled — publish Version 1 before clients can open this link",
        );
      } else {
        showToast("success", "Sharing enabled");
      }
    } catch (err) {
      if (err instanceof ApiClientError) showToast("error", err.message);
      else showToast("error", "Unable to enable sharing");
    } finally {
      setBusy(false);
    }
  }

  async function onDisable() {
    setBusy(true);
    try {
      const data = await disableShare(projectId);
      setState(data);
      setConfirm(null);
      showToast("success", "Sharing disabled");
    } catch (err) {
      if (err instanceof ApiClientError) showToast("error", err.message);
      else showToast("error", "Unable to disable sharing");
    } finally {
      setBusy(false);
    }
  }

  async function onRegenerate() {
    setBusy(true);
    try {
      const data = await regenerateShare(projectId);
      setState(data);
      setConfirm(null);
      showToast("success", "New link created");
    } catch (err) {
      if (err instanceof ApiClientError) showToast("error", err.message);
      else showToast("error", "Unable to regenerate link");
    } finally {
      setBusy(false);
    }
  }

  async function onCopy() {
    if (!state?.share) return;
    try {
      await navigator.clipboard.writeText(publicUrl(state.share));
      showToast("success", "Link copied");
      if (neverPublished) {
        showToast("success", "Publish Version 1 before clients can open this link");
      }
    } catch {
      showToast("error", "Unable to copy link");
    }
  }

  if (loading && !state) {
    return <p className="text-caption text-ink-tertiary">Loading share…</p>;
  }

  const enabled = Boolean(state?.enabled && state.share);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {!enabled ? (
        <Button type="button" size="sm" disabled={busy} onClick={() => void onEnable()}>
          {busy ? "Enabling…" : "Enable"}
        </Button>
      ) : (
        <>
          <span className="max-w-[180px] truncate font-mono text-caption text-ink-tertiary">
            {publicUrl(state!.share!)}
          </span>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={busy}
            onClick={() => void onCopy()}
          >
            Copy
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={busy}
            onClick={() => setConfirm("regenerate")}
          >
            Regenerate
          </Button>
          <Button
            type="button"
            variant="danger"
            size="sm"
            disabled={busy}
            onClick={() => setConfirm("disable")}
          >
            Disable
          </Button>
        </>
      )}

      <ConfirmDialog
        open={confirm === "disable"}
        title="Disable sharing?"
        body="The public link will stop working until you enable sharing again."
        confirmLabel="Disable"
        loadingLabel="Disabling…"
        loading={busy}
        onClose={() => {
          if (!busy) setConfirm(null);
        }}
        onConfirm={() => void onDisable()}
      />

      <ConfirmDialog
        open={confirm === "regenerate"}
        title="Regenerate link?"
        body="The current link will stop working immediately. Anyone with the old link will lose access."
        confirmLabel="Regenerate"
        loadingLabel="Regenerating…"
        loading={busy}
        onClose={() => {
          if (!busy) setConfirm(null);
        }}
        onConfirm={() => void onRegenerate()}
      />
    </div>
  );
}
