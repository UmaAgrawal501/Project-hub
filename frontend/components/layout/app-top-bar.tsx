"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { signOut } from "@/lib/api/client";

export function AppTopBar({ displayName }: { displayName?: string }) {
  const router = useRouter();

  async function onSignOut() {
    await signOut();
    router.replace("/sign-in");
  }

  return (
    <header className="flex h-12 items-center justify-between border-b border-border-subtle px-4 sm:px-8">
      <Link href="/projects" className="text-body font-semibold text-ink">
        ProjectHub
      </Link>
      <div className="flex items-center gap-2 sm:gap-3">
        {displayName ? (
          <span className="hidden max-w-[140px] truncate text-caption text-ink-secondary sm:inline">
            {displayName}
          </span>
        ) : null}
        <Link
          href="/settings"
          className="rounded-md px-2 py-1.5 text-caption text-ink-secondary hover:bg-surface-hover hover:text-ink"
        >
          Settings
        </Link>
        <Button type="button" variant="ghost" size="sm" onClick={onSignOut}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
