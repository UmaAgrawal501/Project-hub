"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FieldError, Input, Label } from "@/components/ui/form";
import { ApiClientError, resetPassword } from "@/lib/api/client";
import { hasSession } from "@/lib/auth/session";

function readRecoveryToken(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("token") || params.get("access_token");
  if (fromQuery) return fromQuery;

  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) return null;
  const hashParams = new URLSearchParams(hash);
  return hashParams.get("access_token") || hashParams.get("token");
}

export default function ResetPasswordPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (hasSession()) router.replace("/projects");
  }, [router]);

  useEffect(() => {
    setToken(readRecoveryToken());
  }, []);

  const missingToken = useMemo(() => token == null || token.length === 0, [token]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!token) {
      setError("This reset link is invalid or incomplete.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await resetPassword({ token, password });
      setDone(true);
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to reset password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-[400px]">
        <p className="mb-6 text-body font-semibold text-ink">ProjectHub</p>
        <h1 className="text-title-1 text-ink">Reset password</h1>
        {done ? (
          <div className="mt-6 space-y-4">
            <p className="text-body text-ink-secondary">
              Your password has been updated. You can sign in with your new password.
            </p>
            <Link href="/sign-in" className="text-accent hover:underline">
              Sign in
            </Link>
          </div>
        ) : missingToken ? (
          <div className="mt-6 space-y-4">
            <p className="text-body text-ink-secondary">
              This reset link is invalid or incomplete. Request a new link from the forgot
              password page.
            </p>
            <Link href="/forgot-password" className="text-accent hover:underline">
              Forgot password
            </Link>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <div>
              <Label htmlFor="password">New password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <div>
              <Label htmlFor="confirm">Confirm password</Label>
              <Input
                id="confirm"
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <FieldError>{error}</FieldError>
            <Button type="submit" className="w-full" size="lg" disabled={loading}>
              {loading ? "Saving…" : "Set new password"}
            </Button>
          </form>
        )}
      </div>
    </main>
  );
}
