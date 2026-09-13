export type PublicDocument = {
  id: number;
  file: string;
  display_name: string;
};

export type OrganisationPublic = {
  id: number;
  nom: string;
  slug: string;
  adresse: string | null;
  code_postal: string | null;
  ville: string | null;
  pays: string | null;
  presentation: string | null;
  public_email: string | null;
  telephone: string | null;
  public_cover_image_url: string | null;
  public_avatar_image_url: string | null;
  cover_position_x: number;
  cover_position_y: number;
  horaires: string | null;
  public_documents: PublicDocument[];
};

export type PublicationSummary = {
  id: number;
  type: "information" | "evenement";
  status: "published";
  titre: string;
  contenu_preview: string;
  date_publication: string | null;
  event_start: string | null;
  event_end: string | null;
  event_location: string;
  attachments_count: number;
};

export type PublicationDetail = {
  id: number;
  organisation: {
    id: number;
    nom: string;
    slug: string;
  };
  type: "information" | "evenement";
  status: "published";
  titre: string;
  contenu: string;
  date_publication: string | null;
  event_start: string | null;
  event_end: string | null;
  event_location: string;
  attachments: PublicDocument[];
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
