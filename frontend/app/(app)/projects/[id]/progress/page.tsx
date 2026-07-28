import { redirect } from "next/navigation";

/** V1 Progress timeline removed — Project Editor is the single owner surface. */
export default async function ProgressRedirect({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/projects/${id}`);
}
