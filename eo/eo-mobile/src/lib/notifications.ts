import * as Notifications from "expo-notifications";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

export type NotificationPermissionState = "unknown" | "granted" | "denied";

export function topicFromSlug(slug: string) {
  return `eo_org_${slug}`;
}

export async function getNotificationPermissionState(): Promise<NotificationPermissionState> {
  const permissions = await Notifications.getPermissionsAsync();
  if (permissions.granted || permissions.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL) {
    return "granted";
  }
  if (permissions.canAskAgain === false) {
    return "denied";
  }
  return "unknown";
}

export async function requestNotificationPermission(): Promise<NotificationPermissionState> {
  const permissions = await Notifications.requestPermissionsAsync();
  if (permissions.granted || permissions.ios?.status === Notifications.IosAuthorizationStatus.PROVISIONAL) {
    return "granted";
  }
  return "denied";
}

export async function scheduleNotificationPreferenceFeedback(orgName: string, enabled: boolean) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: enabled ? "Notifications activées" : "Notifications désactivées",
      body: enabled
        ? `Vous recevrez les prochaines alertes pour ${orgName} lorsque le canal push sera branché.`
        : `Les alertes pour ${orgName} ne sont plus actives sur cet appareil.`,
    },
    trigger: null,
  });
}
