"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppTopBar } from "@/components/layout/app-top-bar";
import { ToastHost } from "@/components/ui/toast";
import { getMe } from "@/lib/api/client";
import { clearSession, hasSession } from "@/lib/auth/session";
import type { User } from "@/lib/types";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!hasSession()) {
      router.replace("/sign-in");
      return;
    }
    getMe()
      .then((data) => {
        setUser(data.user);
        setReady(true);
      })
      .catch(() => {
        clearSession();
        router.replace("/sign-in");
      });
  }, [router]);

  useEffect(() => {
    function onUserUpdated(event: Event) {
      const detail = (event as CustomEvent<User>).detail;
      if (detail) setUser(detail);
    }
    window.addEventListener("projecthub:user-updated", onUserUpdated);
    return () => window.removeEventListener("projecthub:user-updated", onUserUpdated);
  }, []);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-sm space-y-3" aria-busy="true" aria-label="Loading app">
          <div className="h-4 w-32 animate-pulse rounded-sm bg-surface-hover" />
          <div className="h-24 animate-pulse rounded-md bg-surface-hover" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas">
      <ToastHost />
      <AppTopBar displayName={user?.display_name} />
      <div className="px-4 py-6 sm:px-8 sm:py-8">{children}</div>
    </div>
  );
}
