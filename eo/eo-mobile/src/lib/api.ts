import { PUBLIC_API_BASE_URL } from "./config";
import type {
  OrganisationPublic,
  Paginated,
  PublicationDetail,
  PublicationSummary,
} from "../types/public";

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${PUBLIC_API_BASE_URL}${path}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Erreur API publique (${response.status}): ${text}`);
  }
  return response.json() as Promise<T>;
}

export function fetchOrganisations() {
  return apiGet<Paginated<OrganisationPublic>>("/organisations/");
}

export function fetchOrganisation(slug: string) {
  return apiGet<OrganisationPublic>(`/organisations/${encodeURIComponent(slug)}/`);
}

export function fetchPublicationsByOrganisation(slug: string) {
  return apiGet<Paginated<PublicationSummary>>(
    `/publications/?organisation_slug=${encodeURIComponent(slug)}`
  );
}

export function fetchPublication(id: number) {
  return apiGet<PublicationDetail>(`/publications/${id}/`);
}
