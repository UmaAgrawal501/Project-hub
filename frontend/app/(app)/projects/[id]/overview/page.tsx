import { redirect } from "next/navigation";

/** Legacy Draft Overview tab — Project Editor is the single owner surface. */
export default async function OverviewRedirect({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/projects/${id}`);
}
