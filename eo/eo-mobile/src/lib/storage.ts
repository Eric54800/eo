import AsyncStorage from "@react-native-async-storage/async-storage";

const FOLLOWED_ORGANISATIONS_KEY = "eo.followed-organisations";
const NOTIFICATION_SLUGS_KEY = "eo.notification-slugs";
const HIDDEN_PUBLICATIONS_KEY = "eo.hidden-publications";

export async function loadFollowedSlugs(): Promise<string[]> {
  const raw = await AsyncStorage.getItem(FOLLOWED_ORGANISATIONS_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((value) => typeof value === "string") : [];
  } catch {
    return [];
  }
}

export async function saveFollowedSlugs(slugs: string[]) {
  await AsyncStorage.setItem(FOLLOWED_ORGANISATIONS_KEY, JSON.stringify(slugs));
}

export async function toggleFollowedSlug(slug: string) {
  const current = await loadFollowedSlugs();
  const next = current.includes(slug)
    ? current.filter((value) => value !== slug)
    : [...current, slug];
  await saveFollowedSlugs(next);
  return next;
}

export async function loadNotificationSlugs(): Promise<string[]> {
  const raw = await AsyncStorage.getItem(NOTIFICATION_SLUGS_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((value) => typeof value === "string") : [];
  } catch {
    return [];
  }
}

export async function saveNotificationSlugs(slugs: string[]) {
  await AsyncStorage.setItem(NOTIFICATION_SLUGS_KEY, JSON.stringify(slugs));
}

export async function toggleNotificationSlug(slug: string) {
  const current = await loadNotificationSlugs();
  const next = current.includes(slug)
    ? current.filter((value) => value !== slug)
    : [...current, slug];
  await saveNotificationSlugs(next);
  return next;
}

export async function setNotificationSlugEnabled(slug: string, enabled: boolean) {
  const current = await loadNotificationSlugs();
  const next = enabled
    ? current.includes(slug)
      ? current
      : [...current, slug]
    : current.filter((value) => value !== slug);
  await saveNotificationSlugs(next);
  return next;
}

export async function loadHiddenPublicationIds(): Promise<number[]> {
  const raw = await AsyncStorage.getItem(HIDDEN_PUBLICATIONS_KEY);
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.filter((value) => typeof value === "number")
      : [];
  } catch {
    return [];
  }
}

export async function saveHiddenPublicationIds(ids: number[]) {
  await AsyncStorage.setItem(HIDDEN_PUBLICATIONS_KEY, JSON.stringify(ids));
}

export async function hidePublicationId(id: number) {
  const current = await loadHiddenPublicationIds();
  if (current.includes(id)) return current;
  const next = [...current, id];
  await saveHiddenPublicationIds(next);
  return next;
}
