import { redirect } from "next/navigation";

/** Legacy History tab — Version History lives on the Project Editor. */
export default async function HistoryRedirect({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/projects/${id}`);
}
