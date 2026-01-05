from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Membership


class IsOrganisationAdmin(BasePermission):
    """
    Autorise l'écriture seulement si user est admin/owner de l'organisation.
    IMPORTANT : pour les ViewSets, il faut gérer has_object_permission
    (sinon un member peut passer sur des endpoints qui manipulent un objet).
    """

    def has_permission(self, request, view):
        # Lecture : OK si authentifié (le queryset filtre déjà par membership)
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        # Écriture : on laisse has_object_permission décider (quand on a l'objet).
        # Si jamais on est sur une action qui n'a pas d'objet, on bloque par défaut.
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Lecture : OK
        if request.method in SAFE_METHODS:
            return True

        # Staff/superuser : OK
        user = request.user
        if user.is_staff or user.is_superuser:
            return True

        # obj doit avoir une organisation (Subscription.organisation, Publication.organisation, etc.)
        org = getattr(obj, "organisation", None)
        if org is None:
            return False

        role = (
            Membership.objects
            .filter(user=user, organisation=org)
            .values_list("role", flat=True)
            .first()
        )

        return role in ("admin", "owner")