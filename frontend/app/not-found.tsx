import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 py-16 text-center">
      <h1 className="text-title-1 text-ink">Page not found</h1>
      <p className="mt-3 text-body text-ink-secondary">
        This page doesn’t exist or was moved.
      </p>
      <Link
        href="/projects"
        className="mt-6 inline-flex h-10 items-center justify-center rounded-md bg-accent px-4 text-body font-medium text-ink-inverse hover:bg-accent-hover"
      >
        Go to Dashboard
      </Link>
    </main>
  );
}
