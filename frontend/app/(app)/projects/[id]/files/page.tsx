import { redirect } from "next/navigation";

/** Legacy Draft Files tab — Project Editor is the single owner surface. */
export default async function FilesRedirect({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/projects/${id}`);
}
