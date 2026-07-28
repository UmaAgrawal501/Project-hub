"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FieldError, Input, Label } from "@/components/ui/form";
import { ApiClientError, forgotPassword } from "@/lib/api/client";
import { hasSession } from "@/lib/auth/session";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (hasSession()) router.replace("/projects");
  }, [router]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await forgotPassword({ email: email.trim() });
      setSent(true);
    } catch (err) {
      if (err instanceof ApiClientError) setError(err.message);
      else setError("Unable to send reset email");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-[400px]">
        <p className="mb-6 text-body font-semibold text-ink">ProjectHub</p>
        <h1 className="text-title-1 text-ink">Forgot password</h1>
        {sent ? (
          <div className="mt-6 space-y-4">
            <p className="text-body text-ink-secondary">
              If an account exists for that email, a reset link has been sent. Check your
              inbox and follow the link to set a new password.
            </p>
            <Link href="/sign-in" className="text-accent hover:underline">
              Back to sign in
            </Link>
          </div>
        ) : (
          <>
            <p className="mt-2 text-body text-ink-secondary">
              Enter your email and we will send a reset link if an account exists.
            </p>
            <form onSubmit={onSubmit} className="mt-6 space-y-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <FieldError>{error}</FieldError>
              <Button type="submit" className="w-full" size="lg" disabled={loading}>
                {loading ? "Sending…" : "Send reset link"}
              </Button>
            </form>
            <p className="mt-4 text-caption text-ink-secondary">
              <Link href="/sign-in" className="text-accent hover:underline">
                Back to sign in
              </Link>
            </p>
          </>
        )}
      </div>
    </main>
  );
}
