"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FieldError, Input, Label } from "@/components/ui/form";
import { showToast } from "@/components/ui/toast";
import {
  ApiClientError,
  changePassword,
  getMe,
  signOut,
  updateMe,
} from "@/lib/api/client";
import type { User } from "@/lib/types";

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [displayName, setDisplayName] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const [savingName, setSavingName] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [savingPassword, setSavingPassword] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    setLoading(true);
    getMe()
      .then((data) => {
        setUser(data.user);
        setDisplayName(data.user.display_name);
        setLoadError(null);
      })
      .catch((err) => {
        if (err instanceof ApiClientError) setLoadError(err.message);
        else setLoadError("Unable to load settings");
      })
      .finally(() => setLoading(false));
  }, []);

  async function onSaveName(e: FormEvent) {
    e.preventDefault();
    setNameError(null);
    const trimmed = displayName.trim();
    if (!trimmed) {
      setNameError("Name is required");
      return;
    }
    if (trimmed.length > 80) {
      setNameError("Name must be 80 characters or fewer");
      return;
    }
    setSavingName(true);
    try {
      const updated = await updateMe({ display_name: trimmed });
      setUser(updated);
      setDisplayName(updated.display_name);
      window.dispatchEvent(
        new CustomEvent("projecthub:user-updated", { detail: updated }),
      );
      showToast("success", "Display name saved");
    } catch (err) {
      if (err instanceof ApiClientError) setNameError(err.message);
      else setNameError("Unable to save display name");
    } finally {
      setSavingName(false);
    }
  }

  async function onChangePassword(e: FormEvent) {
    e.preventDefault();
    setPasswordError(null);
    if (!currentPassword) {
      setPasswordError("Current password is required");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match");
      return;
    }
    setSavingPassword(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      showToast("success", "Password updated");
    } catch (err) {
      if (err instanceof ApiClientError) setPasswordError(err.message);
      else setPasswordError("Unable to change password");
    } finally {
      setSavingPassword(false);
    }
  }

  async function onSignOut() {
    setSigningOut(true);
    try {
      await signOut();
      router.replace("/sign-in");
    } catch {
      showToast("error", "Unable to sign out");
      setSigningOut(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-lg space-y-4" aria-busy="true">
        <div className="h-8 w-40 animate-pulse rounded-sm bg-surface-hover" />
        <div className="h-24 animate-pulse rounded-md bg-surface-hover" />
        <div className="h-40 animate-pulse rounded-md bg-surface-hover" />
      </div>
    );
  }

  if (loadError || !user) {
    return <p className="text-body text-danger">{loadError ?? "Unable to load settings"}</p>;
  }

  return (
    <div className="mx-auto max-w-lg">
      <h1 className="text-title-1 text-ink">Settings</h1>
      <p className="mt-1 text-body text-ink-secondary">
        Manage your account and security.
      </p>

      <section className="mt-8 rounded-md border border-border-subtle p-4 sm:p-5">
        <h2 className="text-title-3 text-ink">Account</h2>
        <div className="mt-4">
          <Label htmlFor="settings-email">Email</Label>
          <Input id="settings-email" value={user.email} readOnly disabled />
        </div>
        <form onSubmit={onSaveName} className="mt-4 space-y-4">
          <div>
            <Label htmlFor="settings-name">Display name</Label>
            <Input
              id="settings-name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={80}
              required
              aria-invalid={Boolean(nameError)}
              aria-describedby={nameError ? "settings-name-error" : undefined}
            />
            <FieldError id="settings-name-error">{nameError}</FieldError>
          </div>
          <Button type="submit" disabled={savingName}>
            {savingName ? "Saving…" : "Save name"}
          </Button>
        </form>
      </section>

      <section className="mt-6 rounded-md border border-border-subtle p-4 sm:p-5">
        <h2 className="text-title-3 text-ink">Security</h2>
        <form onSubmit={onChangePassword} className="mt-4 space-y-4">
          <div>
            <Label htmlFor="current-password">Current password</Label>
            <Input
              id="current-password"
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div>
            <Label htmlFor="new-password">New password</Label>
            <Input
              id="new-password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={8}
              required
            />
          </div>
          <div>
            <Label htmlFor="confirm-password">Confirm new password</Label>
            <Input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              minLength={8}
              required
              aria-invalid={Boolean(passwordError)}
              aria-describedby={passwordError ? "password-error" : undefined}
            />
            <FieldError id="password-error">{passwordError}</FieldError>
          </div>
          <Button type="submit" disabled={savingPassword}>
            {savingPassword ? "Updating…" : "Change password"}
          </Button>
        </form>
      </section>

      <section className="mt-6 rounded-md border border-border-subtle p-4 sm:p-5">
        <h2 className="text-title-3 text-ink">Session</h2>
        <p className="mt-2 text-body text-ink-secondary">
          Sign out of ProjectHub on this device.
        </p>
        <Button
          type="button"
          variant="secondary"
          className="mt-4"
          disabled={signingOut}
          onClick={() => void onSignOut()}
        >
          {signingOut ? "Signing out…" : "Sign out"}
        </Button>
      </section>
    </div>
  );
}
