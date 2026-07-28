"use client";

import { useEffect, useState } from "react";

type ToastKind = "success" | "error";

type ToastState = {
  id: number;
  kind: ToastKind;
  message: string;
} | null;

let toastId = 0;
let pushToast: ((kind: ToastKind, message: string) => void) | null = null;

export function showToast(kind: ToastKind, message: string) {
  pushToast?.(kind, message);
}

export function ToastHost() {
  const [toast, setToast] = useState<ToastState>(null);

  useEffect(() => {
    pushToast = (kind, message) => {
      toastId += 1;
      setToast({ id: toastId, kind, message });
    };
    return () => {
      pushToast = null;
    };
  }, []);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 2800);
    return () => window.clearTimeout(timer);
  }, [toast]);

  if (!toast) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-6 z-[60] flex justify-center px-4">
      <div
        className={`rounded-md border px-4 py-2 text-caption shadow-md ${
          toast.kind === "success"
            ? "border-border-subtle bg-canvas-elevated text-success"
            : "border-border-subtle bg-canvas-elevated text-danger"
        }`}
        role="status"
        aria-live={toast.kind === "error" ? "assertive" : "polite"}
      >
        {toast.message}
      </div>
    </div>
  );
}
