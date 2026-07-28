"use client";

import { Button } from "@/components/ui/button";

export function EmptyDashboard({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-md border border-dashed border-border bg-surface px-6 py-16 text-center">
      <h2 className="text-title-3 text-ink">Create your first project</h2>
      <p className="mt-2 max-w-sm text-body text-ink-secondary">
        Upload files, publish, and share one link with your client.
      </p>
      <Button type="button" className="mt-6" onClick={onCreate}>
        Create project
      </Button>
    </div>
  );
}
