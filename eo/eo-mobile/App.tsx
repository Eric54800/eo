import { StatusBar } from "expo-status-bar";
import {
  ActivityIndicator,
  Alert,
  Linking,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useDeferredValue, useEffect, useState } from "react";

import {
  fetchPublication,
  fetchOrganisation,
  fetchOrganisations,
  fetchPublicationsByOrganisation,
} from "./src/lib/api";
import {
  hidePublicationId,
  loadFollowedSlugs,
  loadHiddenPublicationIds,
  setNotificationSlugEnabled,
  toggleFollowedSlug,
} from "./src/lib/storage";
import {
  getNotificationPermissionState,
  requestNotificationPermission,
  scheduleNotificationPreferenceFeedback,
  topicFromSlug,
  type NotificationPermissionState,
} from "./src/lib/notifications";
import type {
  OrganisationPublic,
  PublicationDetail,
  PublicationSummary,
} from "./src/types/public";

type Screen =
  | { name: "home" }
  | { name: "organisation"; slug: string; returnSection?: HomeSection }
  | {
      name: "publication";
      id: number;
      organisationSlug: string;
      returnTo:
        | { name: "home"; section: HomeSection }
        | { name: "organisation"; slug: string; returnSection?: HomeSection };
    };

type FeedItem = PublicationSummary & {
  organisation_nom: string;
  organisation_slug: string;
};

type HomeSection = "followed" | "feed" | "discover";

export default function App() {
  const [screen, setScreen] = useState<Screen>({ name: "home" });
  const [homeSection, setHomeSection] = useState<HomeSection>("feed");
  const [followedSlugs, setFollowedSlugs] = useState<string[]>([]);
  const [hiddenPublicationIds, setHiddenPublicationIds] = useState<number[]>([]);
  const [notificationPermission, setNotificationPermission] =
    useState<NotificationPermissionState>("unknown");

  useEffect(() => {
    loadFollowedSlugs().then(setFollowedSlugs);
    loadHiddenPublicationIds().then(setHiddenPublicationIds);
    getNotificationPermissionState().then(setNotificationPermission);
  }, []);

  async function handleToggleFollow(slug: string, orgName: string) {
    const nextFollowed = await toggleFollowedSlug(slug);
    const nowFollowed = nextFollowed.includes(slug);
    setFollowedSlugs(nextFollowed);

    if (!nowFollowed) {
      await setNotificationSlugEnabled(slug, false);
      return;
    }

    let permission = notificationPermission;

    if (permission !== "granted") {
      permission = await requestNotificationPermission();
      setNotificationPermission(permission);
    }

    if (permission !== "granted") {
      Alert.alert(
        "Source suivie",
        "Cette source est bien suivie, mais les notifications iPhone ne sont pas autorisées sur cet appareil."
      );
      return;
    }

    await setNotificationSlugEnabled(slug, true);
    await scheduleNotificationPreferenceFeedback(orgName, true);
  }

  async function handleHidePublication(id: number) {
    const next = await hidePublicationId(id);
    setHiddenPublicationIds(next);
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      {screen.name === "home" ? (
        <HomeScreen
          activeSection={homeSection}
          onChangeSection={setHomeSection}
          followedSlugs={followedSlugs}
          hiddenPublicationIds={hiddenPublicationIds}
          notificationPermission={notificationPermission}
          onOpenOrganisation={(slug) =>
            setScreen({ name: "organisation", slug, returnSection: homeSection })
          }
          onOpenPublication={(id, organisationSlug) =>
            setScreen({
              name: "publication",
              id,
              organisationSlug,
              returnTo: { name: "home", section: homeSection },
            })
          }
          onToggleFollow={handleToggleFollow}
          onHidePublication={handleHidePublication}
        />
      ) : screen.name === "organisation" ? (
        <OrganisationScreen
          slug={screen.slug}
          followed={followedSlugs.includes(screen.slug)}
          notificationPermission={notificationPermission}
          onBack={() => {
            setHomeSection(screen.returnSection ?? "feed");
            setScreen({ name: "home" });
          }}
          onOpenPublication={(id) =>
            setScreen({
              name: "publication",
              id,
              organisationSlug: screen.slug,
              returnTo: {
                name: "organisation",
                slug: screen.slug,
                returnSection: screen.returnSection,
              },
            })
          }
          onToggleFollow={(orgName) => handleToggleFollow(screen.slug, orgName)}
        />
      ) : (
        <PublicationScreen
          id={screen.id}
          organisationSlug={screen.organisationSlug}
          onBack={() => {
            if (screen.returnTo.name === "home") {
              setHomeSection(screen.returnTo.section);
              setScreen({ name: "home" });
              return;
            }
            setScreen(screen.returnTo);
          }}
          onOpenOrganisation={(slug) =>
            setScreen({
              name: "organisation",
              slug,
              returnSection:
                screen.returnTo.name === "home" ? screen.returnTo.section : screen.returnTo.returnSection,
            })
          }
        />
      )}
    </SafeAreaView>
  );
}

function HomeScreen({
  activeSection,
  onChangeSection,
  followedSlugs,
  hiddenPublicationIds,
  notificationPermission,
  onOpenOrganisation,
  onOpenPublication,
  onHidePublication,
  onToggleFollow,
}: {
  activeSection: HomeSection;
  onChangeSection: (section: HomeSection) => void;
  followedSlugs: string[];
  hiddenPublicationIds: number[];
  notificationPermission: NotificationPermissionState;
  onOpenOrganisation: (slug: string) => void;
  onOpenPublication: (id: number, organisationSlug: string) => void;
  onHidePublication: (id: number) => Promise<void>;
  onToggleFollow: (slug: string, orgName: string) => Promise<void>;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [organisations, setOrganisations] = useState<OrganisationPublic[]>([]);
  const [feedLoading, setFeedLoading] = useState(false);
  const [feedError, setFeedError] = useState<string | null>(null);
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const deferredSearchQuery = useDeferredValue(searchQuery);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchOrganisations()
      .then((data) => {
        if (!active) return;
        setOrganisations(data.results);
      })
      .catch((err: Error) => {
        if (!active) return;
        setError(err.message);
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    if (followedSlugs.length === 0) {
      setFeedItems([]);
      setFeedError(null);
      setFeedLoading(false);
      return () => {
        active = false;
      };
    }

    setFeedLoading(true);
    setFeedError(null);

    Promise.all(
      followedSlugs.map(async (slug) => {
        const response = await fetchPublicationsByOrganisation(slug);
        return response.results.map((publication) => ({
          ...publication,
          organisation_slug: slug,
          organisation_nom:
            organisations.find((organisation) => organisation.slug === slug)?.nom ?? slug,
        }));
      })
    )
      .then((results) => {
        if (!active) return;
        const flattened = results
          .flat()
          .filter((publication) => !hiddenPublicationIds.includes(publication.id))
          .filter((publication) => shouldKeepPublicationInFeed(publication))
          .sort(compareFeedItems);
        setFeedItems(flattened);
      })
      .catch((err: Error) => {
        if (!active) return;
        setFeedError(err.message);
      })
      .finally(() => {
        if (!active) return;
        setFeedLoading(false);
      });

    return () => {
      active = false;
    };
  }, [followedSlugs, organisations, hiddenPublicationIds]);

  useEffect(() => {
    if (followedSlugs.length === 0 && activeSection === "feed") {
      onChangeSection("discover");
    }
  }, [followedSlugs, activeSection, onChangeSection]);

  const followedOrganisations = organisations.filter((organisation) =>
    followedSlugs.includes(organisation.slug)
  );
  const normalizedQuery = deferredSearchQuery.trim().toLowerCase();
  const filteredOrganisations = organisations.filter((organisation) => {
    if (!normalizedQuery) return true;
    return [
      organisation.nom,
      organisation.slug,
      organisation.ville,
      organisation.pays,
      organisation.presentation,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(normalizedQuery));
  });
  const highlightedOrganisation = filteredOrganisations[0] ?? null;
  const discoveryOrganisations = highlightedOrganisation
    ? filteredOrganisations.slice(1)
    : filteredOrganisations;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.hero}>
        <View style={styles.brandRow}>
          <View style={styles.brandMark}>
            <Text style={styles.brandMarkText}>É</Text>
          </View>
          <View style={styles.brandTextGroup}>
            <Text style={styles.eyebrow}>CRIEUR PUBLIC</Text>
            <Text style={styles.brandName}>Éo</Text>
          </View>
        </View>
        <View style={styles.heroHeaderRow}>
          <View style={styles.heroIntro}>
            <Text style={styles.heroTitle}>Vos criées locales</Text>
            <Text style={styles.heroSubtitle}>
              Retrouvez d’abord les criées, puis les infos sur ceux qui publient.
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.sectionTabs}>
        <Pressable
          onPress={() => onChangeSection("feed")}
          style={activeSection === "feed" ? styles.activeTab : styles.inactiveTab}
        >
          <Text
            style={activeSection === "feed" ? styles.activeTabText : styles.inactiveTabText}
          >
            Criées
          </Text>
        </Pressable>
        <Pressable
          onPress={() => onChangeSection("followed")}
          style={activeSection === "followed" ? styles.activeTab : styles.inactiveTab}
        >
          <Text
            style={activeSection === "followed" ? styles.activeTabText : styles.inactiveTabText}
          >
            Sources
          </Text>
        </Pressable>
        <Pressable
          onPress={() => onChangeSection("discover")}
          style={activeSection === "discover" ? styles.activeTab : styles.inactiveTab}
        >
          <Text
            style={activeSection === "discover" ? styles.activeTabText : styles.inactiveTabText}
          >
            Trouver
          </Text>
        </Pressable>
      </View>

      {activeSection === "followed" ? (
        <>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Vos sources</Text>
            <Text style={styles.sectionHint}>
              {followedSlugs.length === 0
                ? "Aucune source pour le moment."
                : `${followedSlugs.length} source(s) active(s) sur cet appareil.`}
            </Text>
          </View>

          <View style={styles.infoCard}>
            <Text style={styles.infoTitle}>Alertes</Text>
            <Text style={styles.infoText}>
              {notificationPermission === "granted"
                ? "Les alertes iPhone sont actives pour les sources que vous suivez."
                : "En suivant une source, l’app demandera l’autorisation iPhone pour les alertes."}
            </Text>
          </View>

          {followedOrganisations.length === 0 ? (
            <View style={styles.stateCard}>
              <Text style={styles.stateText}>
                Ajoutez au moins une source pour construire votre fil de criées.
              </Text>
            </View>
          ) : (
            followedOrganisations.map((organisation) => (
              <View key={`followed-${organisation.id}`} style={styles.card}>
                <Pressable onPress={() => onOpenOrganisation(organisation.slug)}>
                  <Text style={styles.cardTitle}>{organisation.nom}</Text>
                  <Text style={styles.cardMeta}>
                    {formatLocation(organisation.ville, organisation.pays)}
                  </Text>
                </Pressable>

                <View style={styles.cardActions}>
                  <Pressable
                    onPress={() => onToggleFollow(organisation.slug, organisation.nom)}
                    style={styles.secondaryButton}
                  >
                    <Text style={styles.secondaryButtonText}>Ne plus suivre</Text>
                  </Pressable>
                </View>
              </View>
            ))
          )}
        </>
      ) : null}

      {activeSection === "feed" ? (
        <>
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Vos criées</Text>
            <Text style={styles.sectionHint}>
              Les dernières criées publiées par les sources que vous suivez.
            </Text>
          </View>

          {followedSlugs.length === 0 ? (
            <View style={styles.stateCard}>
              <Text style={styles.stateText}>
                Ajoutez d’abord un suivi pour afficher vos criées.
              </Text>
            </View>
          ) : feedLoading ? (
            <View style={styles.stateCard}>
              <ActivityIndicator color="#4338ca" />
              <Text style={styles.stateText}>Chargement du fil des criées...</Text>
            </View>
          ) : feedError ? (
            <View style={styles.errorCard}>
              <Text style={styles.errorTitle}>Impossible de charger le fil</Text>
              <Text style={styles.errorText}>{feedError}</Text>
            </View>
          ) : feedItems.length === 0 ? (
            <View style={styles.stateCard}>
              <Text style={styles.stateText}>
                Aucune criée publiée pour les sources suivies.
              </Text>
            </View>
          ) : (
            feedItems.map((publication) => (
              <View
                key={`feed-${publication.organisation_slug}-${publication.id}`}
                style={styles.feedCard}
              >
                <Pressable
                  onPress={() =>
                    onOpenPublication(publication.id, publication.organisation_slug)
                  }
                >
                  <View style={styles.feedTopRow}>
                    <View
                      style={
                        publication.type === "evenement"
                          ? styles.eventPill
                          : styles.informationPill
                      }
                    >
                      <Text
                        style={
                          publication.type === "evenement"
                            ? styles.eventPillText
                            : styles.informationPillText
                        }
                      >
                        {publication.type === "evenement" ? "Événement" : "Information"}
                      </Text>
                    </View>
                    <View style={styles.sourcePill}>
                      <Text style={styles.sourcePillText}>{publication.organisation_nom}</Text>
                    </View>
                  </View>
                  <Text style={styles.cardTitle}>{publication.titre}</Text>
                  <Text style={styles.feedDate}>{formatFeedMeta(publication)}</Text>
                  <Text style={styles.cardBody}>{publication.contenu_preview}</Text>
                </Pressable>
                {publication.type === "information" ? (
                  <View style={styles.cardActions}>
                    <Pressable
                      onPress={() => onHidePublication(publication.id)}
                      style={styles.secondaryButton}
                    >
                      <Text style={styles.secondaryButtonText}>Masquer</Text>
                    </Pressable>
                  </View>
                ) : null}
              </View>
            ))
          )}
        </>
      ) : null}

      {activeSection === "discover" ? (
        <>
            <View style={styles.searchCard}>
            <Text style={styles.sectionTitle}>Trouver des criées</Text>
            <Text style={styles.sectionHint}>
              Commencez par trouver qui publie près de chez vous.
            </Text>
            <TextInput
              value={searchQuery}
              onChangeText={setSearchQuery}
              placeholder="Ex. mairie, association, bruville..."
              placeholderTextColor="#94a3b8"
              style={styles.searchInput}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <Text style={styles.searchResultHint}>
              {normalizedQuery
                ? `${filteredOrganisations.length} résultat(s) correspondent à votre recherche.`
                : `${organisations.length} lieu(x) ou compte(s) public(s) disponibles.`}
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Qui publie autour de vous</Text>
            <Text style={styles.sectionHint}>
              Mairies, associations, lieux ou comptes publics qui publient des criées.
            </Text>
          </View>

          {loading ? (
            <View style={styles.stateCard}>
              <ActivityIndicator color="#4338ca" />
              <Text style={styles.stateText}>Chargement des sources...</Text>
            </View>
          ) : error ? (
            <View style={styles.errorCard}>
              <Text style={styles.errorTitle}>Impossible de charger les sources</Text>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : filteredOrganisations.length === 0 ? (
            <View style={styles.stateCard}>
              <Text style={styles.stateText}>
                Aucun résultat ne correspond à votre recherche.
              </Text>
            </View>
          ) : (
            <>
              {highlightedOrganisation ? (
                <View style={styles.highlightCard}>
                  <Text style={styles.highlightEyebrow}>À LA UNE</Text>
                  <Text style={styles.highlightTitle}>{highlightedOrganisation.nom}</Text>
                  <Text style={styles.highlightMeta}>
                    {formatLocation(highlightedOrganisation.ville, highlightedOrganisation.pays)}
                  </Text>
                  <Text style={styles.highlightBody} numberOfLines={4}>
                    {highlightedOrganisation.presentation ||
                      "Aucune présentation publique pour le moment."}
                  </Text>
                  <View style={styles.cardActions}>
                    <Pressable
                      onPress={() => onOpenOrganisation(highlightedOrganisation.slug)}
                      style={styles.primaryButton}
                    >
                      <Text style={styles.primaryButtonText}>Voir les criées</Text>
                    </Pressable>
                      <Pressable
                        onPress={() =>
                          onToggleFollow(
                            highlightedOrganisation.slug,
                            highlightedOrganisation.nom
                          )
                        }
                        style={
                          followedSlugs.includes(highlightedOrganisation.slug)
                            ? styles.secondaryButton
                          : styles.secondaryGhostButton
                      }
                    >
                      <Text
                        style={
                          followedSlugs.includes(highlightedOrganisation.slug)
                            ? styles.secondaryButtonText
                            : styles.secondaryGhostButtonText
                        }
                      >
                        {followedSlugs.includes(highlightedOrganisation.slug)
                          ? "Déjà suivie"
                          : "Suivre"}
                      </Text>
                    </Pressable>
                  </View>
                </View>
              ) : null}

              {discoveryOrganisations.map((organisation) => {
                const followed = followedSlugs.includes(organisation.slug);
                return (
                  <View key={organisation.id} style={styles.card}>
                    <Pressable onPress={() => onOpenOrganisation(organisation.slug)}>
                      <Text style={styles.cardTitle}>{organisation.nom}</Text>
                      <Text style={styles.cardMeta}>
                        {formatLocation(organisation.ville, organisation.pays)}
                      </Text>
                      <Text style={styles.cardBody} numberOfLines={3}>
                        {organisation.presentation || "Aucune présentation publique pour le moment."}
                      </Text>
                    </Pressable>

                    <View style={styles.cardActions}>
                      <Pressable
                        onPress={() => onOpenOrganisation(organisation.slug)}
                        style={styles.secondaryButton}
                      >
                        <Text style={styles.secondaryButtonText}>Ouvrir</Text>
                      </Pressable>
                      <Pressable
                        onPress={() => onToggleFollow(organisation.slug, organisation.nom)}
                        style={followed ? styles.secondaryButton : styles.primaryButton}
                      >
                        <Text style={followed ? styles.secondaryButtonText : styles.primaryButtonText}>
                          {followed ? "Suivie" : "Suivre"}
                        </Text>
                      </Pressable>
                    </View>
                  </View>
                );
              })}
            </>
          )}
        </>
      ) : null}
    </ScrollView>
  );
}

function OrganisationScreen({
  slug,
  followed,
  notificationPermission,
  onBack,
  onOpenPublication,
  onToggleFollow,
}: {
  slug: string;
  followed: boolean;
  notificationPermission: NotificationPermissionState;
  onBack: () => void;
  onOpenPublication: (id: number) => void;
  onToggleFollow: (orgName: string) => Promise<void>;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [organisation, setOrganisation] = useState<OrganisationPublic | null>(null);
  const [publications, setPublications] = useState<PublicationSummary[]>([]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    Promise.all([fetchOrganisation(slug), fetchPublicationsByOrganisation(slug)])
      .then(([org, pubs]) => {
        if (!active) return;
        setOrganisation(org);
        setPublications(pubs.results);
      })
      .catch((err: Error) => {
        if (!active) return;
        setError(err.message);
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [slug]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable onPress={onBack} style={styles.backLink}>
        <Text style={styles.backLinkText}>Retour</Text>
      </Pressable>

      {loading ? (
        <View style={styles.stateCard}>
          <ActivityIndicator color="#4338ca" />
          <Text style={styles.stateText}>Chargement de la structure...</Text>
        </View>
      ) : error || !organisation ? (
        <View style={styles.errorCard}>
          <Text style={styles.errorTitle}>Impossible de charger la structure</Text>
          <Text style={styles.errorText}>{error || "Structure introuvable."}</Text>
        </View>
      ) : (
        <>
          <View style={styles.heroCard}>
            <Text style={styles.cardTitle}>{organisation.nom}</Text>
            <Text style={styles.cardMeta}>
              {formatLocation(organisation.ville, organisation.pays)}
            </Text>
            <Text style={styles.cardBody}>
              {organisation.presentation || "Aucune présentation publique pour le moment."}
            </Text>

            <View style={styles.metaGroup}>
              <Text style={styles.metaLabel}>Contact</Text>
              <Text style={styles.metaValue}>
                {organisation.public_email || organisation.telephone || "Aucun contact public"}
              </Text>
            </View>

            {organisation.horaires ? (
              <View style={styles.metaGroup}>
                <Text style={styles.metaLabel}>Horaires</Text>
                <Text style={styles.metaValue}>{organisation.horaires}</Text>
              </View>
            ) : null}

            <Pressable
              onPress={() => onToggleFollow(organisation.nom)}
              style={followed ? styles.secondaryButton : styles.primaryButton}
            >
              <Text style={followed ? styles.secondaryButtonText : styles.primaryButtonText}>
                {followed ? "Ne plus suivre" : "Suivre cette source"}
              </Text>
            </Pressable>

            <Text style={styles.inlineHint}>
              {followed
                ? notificationPermission === "granted"
                  ? `Les alertes sont actives sur cet appareil pour cette source. Canal prévu : ${topicFromSlug(
                      slug
                    )}.`
                  : "Cette source est suivie, mais les notifications iPhone ne sont pas autorisées sur cet appareil."
                : "Suivez cette source pour la retrouver plus vite et recevoir ses prochaines alertes sur cet appareil."}
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Criées récentes</Text>
            <Text style={styles.sectionHint}>
              Cette liste vient directement de l’API publique existante.
            </Text>
          </View>

          {publications.length === 0 ? (
            <View style={styles.stateCard}>
              <Text style={styles.stateText}>Aucune criée publiée pour le moment.</Text>
            </View>
          ) : (
            publications.map((publication) => (
              <Pressable
                key={publication.id}
                onPress={() => onOpenPublication(publication.id)}
                style={styles.card}
              >
                <Text style={styles.publicationType}>
                  {publication.type === "evenement" ? "Événement" : "Information"}
                </Text>
                <Text style={styles.cardTitle}>{publication.titre}</Text>
                <Text style={styles.cardMeta}>
                  {formatPublicationDate(publication.date_publication)}
                </Text>
                <Text style={styles.cardBody}>{publication.contenu_preview}</Text>
              </Pressable>
            ))
          )}
        </>
      )}
    </ScrollView>
  );
}

function PublicationScreen({
  id,
  organisationSlug,
  onBack,
  onOpenOrganisation,
}: {
  id: number;
  organisationSlug: string;
  onBack: () => void;
  onOpenOrganisation: (slug: string) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [publication, setPublication] = useState<PublicationDetail | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchPublication(id)
      .then((data) => {
        if (!active) return;
        setPublication(data);
      })
      .catch((err: Error) => {
        if (!active) return;
        setError(err.message);
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [id]);

  async function handleOpenAttachment(url: string) {
    const canOpen = await Linking.canOpenURL(url);
    if (!canOpen) {
      Alert.alert("Pièce jointe indisponible", "Impossible d’ouvrir ce document.");
      return;
    }
    await Linking.openURL(url);
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable onPress={onBack} style={styles.backLink}>
        <Text style={styles.backLinkText}>Retour à l’accueil</Text>
      </Pressable>

      {loading ? (
        <View style={styles.stateCard}>
          <ActivityIndicator color="#4338ca" />
          <Text style={styles.stateText}>Chargement de la criée...</Text>
        </View>
      ) : error || !publication ? (
        <View style={styles.errorCard}>
          <Text style={styles.errorTitle}>Impossible de charger la criée</Text>
          <Text style={styles.errorText}>{error || "Criée introuvable."}</Text>
        </View>
      ) : (
        <>
          <View style={styles.heroCard}>
            <Text style={styles.publicationType}>
              {publication.type === "evenement" ? "Événement" : "Information"}
            </Text>
            <Text style={styles.cardTitle}>{publication.titre}</Text>
            <Text style={styles.cardMeta}>
              {publication.organisation.nom} •{" "}
              {formatPublicationDate(publication.date_publication)}
            </Text>
            <Text style={styles.cardBody}>{publication.contenu}</Text>

            {publication.event_start || publication.event_end ? (
              <View style={styles.metaGroup}>
                <Text style={styles.metaLabel}>Quand</Text>
                <Text style={styles.metaValue}>
                  {formatEventWindow(publication.event_start, publication.event_end)}
                </Text>
              </View>
            ) : null}

            {publication.event_location ? (
              <View style={styles.metaGroup}>
                <Text style={styles.metaLabel}>Lieu</Text>
                <Text style={styles.metaValue}>{publication.event_location}</Text>
              </View>
            ) : null}

            <Pressable
              onPress={() => onOpenOrganisation(publication.organisation.slug || organisationSlug)}
              style={styles.secondaryButton}
            >
              <Text style={styles.secondaryButtonText}>Voir qui publie</Text>
            </Pressable>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Pièces jointes</Text>
            <Text style={styles.sectionHint}>
              Ouvrez les documents liés à cette criée si disponibles.
            </Text>
          </View>

          {publication.attachments.length === 0 ? (
            <View style={styles.stateCard}>
              <Text style={styles.stateText}>Aucune pièce jointe pour cette criée.</Text>
            </View>
          ) : (
            publication.attachments.map((attachment) => (
              <View key={attachment.id} style={styles.card}>
                <Text style={styles.cardTitle}>{attachment.display_name}</Text>
                <Pressable
                  onPress={() => handleOpenAttachment(attachment.file)}
                  style={styles.primaryButton}
                >
                  <Text style={styles.primaryButtonText}>Ouvrir le document</Text>
                </Pressable>
              </View>
            ))
          )}
        </>
      )}
    </ScrollView>
  );
}

function comparePublicationDates(a: string | null, b: string | null) {
  const left = a ? new Date(a).getTime() : 0;
  const right = b ? new Date(b).getTime() : 0;
  return left - right;
}

function shouldKeepPublicationInFeed(publication: PublicationSummary) {
  if (publication.type !== "evenement") return true;

  const now = Date.now();
  const eventEnd = publication.event_end ? new Date(publication.event_end).getTime() : null;
  const eventStart = publication.event_start
    ? new Date(publication.event_start).getTime()
    : null;

  const reference = eventEnd ?? eventStart;
  if (!reference) return true;

  const nextDay = reference + 24 * 60 * 60 * 1000;
  return nextDay >= now;
}

function compareFeedItems(a: FeedItem, b: FeedItem) {
  const now = Date.now();
  const aUpcoming = a.type === "evenement" && isUpcomingEvent(a, now);
  const bUpcoming = b.type === "evenement" && isUpcomingEvent(b, now);

  if (aUpcoming && bUpcoming) {
    return comparePublicationDates(a.event_start, b.event_start);
  }

  if (aUpcoming) return -1;
  if (bUpcoming) return 1;

  return comparePublicationDates(b.date_publication, a.date_publication);
}

function isUpcomingEvent(publication: PublicationSummary, now: number) {
  if (!publication.event_start) return false;
  return new Date(publication.event_start).getTime() >= now;
}

function formatFeedMeta(publication: PublicationSummary) {
  if (publication.type === "evenement" && publication.event_start) {
    const eventDate =
      formatDateTime(publication.event_start) ??
      formatPublicationDate(publication.date_publication);
    return `À partir du ${eventDate}`;
  }
  return `Publiée le ${formatPublicationDate(publication.date_publication)}`;
}

function formatLocation(ville?: string | null, pays?: string | null) {
  return [ville, pays].filter(Boolean).join(", ") || "Localisation non renseignée";
}

function formatPublicationDate(value: string | null) {
  if (!value) return "Date inconnue";
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(new Date(value));
}

function formatDateTime(value: string | null) {
  if (!value) return null;
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatEventWindow(start: string | null, end: string | null) {
  const startLabel = formatDateTime(start);
  const endLabel = formatDateTime(end);

  if (startLabel && endLabel) return `${startLabel} → ${endLabel}`;
  if (startLabel) return startLabel;
  if (endLabel) return `Jusqu’au ${endLabel}`;
  return "Horaire non renseigné";
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#f5f3ff",
  },
  container: {
    padding: 20,
    gap: 16,
  },
  hero: {
    gap: 14,
    padding: 16,
    borderRadius: 28,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
    shadowColor: "#4338ca",
    shadowOpacity: 0.08,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 14 },
  },
  heroCard: {
    gap: 12,
    padding: 20,
    borderRadius: 24,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1,
    color: "#6d28d9",
  },
  brandRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  brandMark: {
    width: 62,
    height: 62,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#ede9fe",
    borderWidth: 1,
    borderColor: "rgba(109, 40, 217, 0.14)",
  },
  brandMarkText: {
    fontSize: 34,
    fontWeight: "900",
    color: "#6d28d9",
  },
  brandTextGroup: {
    gap: 2,
  },
  brandName: {
    fontSize: 28,
    fontWeight: "900",
    color: "#0f172a",
  },
  heroHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 14,
  },
  heroIntro: {
    flex: 1,
    gap: 4,
  },
  heroTitle: {
    fontSize: 20,
    lineHeight: 24,
    fontWeight: "900",
    color: "#0f172a",
  },
  heroSubtitle: {
    fontSize: 14,
    lineHeight: 19,
    color: "#475569",
  },
  searchCard: {
    gap: 8,
    padding: 18,
    borderRadius: 22,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
  },
  searchInput: {
    height: 52,
    paddingHorizontal: 16,
    borderRadius: 16,
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
    color: "#0f172a",
    fontSize: 16,
    fontWeight: "600",
  },
  searchResultHint: {
    fontSize: 13,
    lineHeight: 18,
    color: "#6366f1",
  },
  sectionTabs: {
    flexDirection: "row",
    gap: 10,
  },
  activeTab: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 12,
    borderRadius: 18,
    backgroundColor: "#312e81",
    borderWidth: 1,
    borderColor: "rgba(49, 46, 129, 0.24)",
    alignItems: "center",
    justifyContent: "center",
  },
  inactiveTab: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 12,
    borderRadius: 18,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
    alignItems: "center",
    justifyContent: "center",
  },
  activeTabText: {
    fontSize: 14,
    fontWeight: "800",
    color: "#ffffff",
  },
  inactiveTabText: {
    fontSize: 14,
    fontWeight: "800",
    color: "#0f172a",
  },
  section: {
    gap: 4,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: "#0f172a",
  },
  sectionHint: {
    fontSize: 14,
    lineHeight: 20,
    color: "#64748b",
  },
  stateCard: {
    gap: 10,
    padding: 20,
    borderRadius: 20,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
    alignItems: "center",
  },
  stateText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#475569",
    textAlign: "center",
  },
  infoCard: {
    gap: 8,
    padding: 18,
    borderRadius: 20,
    backgroundColor: "#eef2ff",
    borderWidth: 1,
    borderColor: "rgba(67, 56, 202, 0.14)",
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#312e81",
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
    color: "#4338ca",
  },
  errorCard: {
    gap: 8,
    padding: 20,
    borderRadius: 20,
    backgroundColor: "#fff1f2",
    borderWidth: 1,
    borderColor: "rgba(225, 29, 72, 0.18)",
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#be123c",
  },
  errorText: {
    fontSize: 14,
    lineHeight: 20,
    color: "#881337",
  },
  card: {
    gap: 10,
    padding: 18,
    borderRadius: 22,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
  },
  feedCard: {
    gap: 12,
    padding: 18,
    borderRadius: 22,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
  },
  feedTopRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    alignItems: "center",
    marginBottom: 4,
  },
  eventPill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "#ede9fe",
  },
  eventPillText: {
    fontSize: 12,
    fontWeight: "800",
    color: "#6d28d9",
  },
  informationPill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "#ecfeff",
  },
  informationPillText: {
    fontSize: 12,
    fontWeight: "800",
    color: "#155e75",
  },
  sourcePill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
  },
  sourcePillText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#334155",
  },
  highlightCard: {
    gap: 10,
    padding: 22,
    borderRadius: 26,
    backgroundColor: "#312e81",
    borderWidth: 1,
    borderColor: "rgba(79, 70, 229, 0.2)",
  },
  highlightEyebrow: {
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1,
    color: "#c4b5fd",
  },
  highlightTitle: {
    fontSize: 28,
    lineHeight: 34,
    fontWeight: "900",
    color: "#ffffff",
  },
  highlightMeta: {
    fontSize: 14,
    fontWeight: "700",
    color: "#ddd6fe",
  },
  highlightBody: {
    fontSize: 15,
    lineHeight: 22,
    color: "#e2e8f0",
  },
  cardTitle: {
    fontSize: 22,
    lineHeight: 28,
    fontWeight: "800",
    color: "#0f172a",
  },
  cardMeta: {
    fontSize: 14,
    fontWeight: "700",
    color: "#6b7280",
  },
  cardBody: {
    fontSize: 15,
    lineHeight: 22,
    color: "#475569",
  },
  cardActions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 4,
  },
  primaryButton: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 16,
    backgroundColor: "#6d28d9",
    alignItems: "center",
    justifyContent: "center",
  },
  primaryButtonText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 15,
  },
  secondaryButton: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 16,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.12)",
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryGhostButton: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 16,
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.28)",
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryButtonText: {
    color: "#0f172a",
    fontWeight: "800",
    fontSize: 15,
  },
  secondaryGhostButtonText: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 15,
  },
  backLink: {
    alignSelf: "flex-start",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "rgba(15, 23, 42, 0.08)",
  },
  backLinkText: {
    fontSize: 14,
    fontWeight: "800",
    color: "#0f172a",
  },
  metaGroup: {
    gap: 4,
  },
  metaLabel: {
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1,
    color: "#6d28d9",
  },
  metaValue: {
    fontSize: 15,
    lineHeight: 22,
    color: "#334155",
  },
  inlineHint: {
    fontSize: 13,
    lineHeight: 19,
    color: "#6366f1",
  },
  publicationType: {
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1,
    color: "#6d28d9",
    textTransform: "uppercase",
  },
  feedDate: {
    fontSize: 14,
    fontWeight: "700",
    color: "#475569",
  },
});
