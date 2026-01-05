import os
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import Association, Evenement

@receiver(pre_save, sender=Association)
def delete_old_logo(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Association.objects.get(pk=instance.pk).logo
    except Association.DoesNotExist:
        return
    new = instance.logo
    if old and old != new:
        try:
            if os.path.isfile(old.path):
                os.remove(old.path)
        except Exception:
            pass

@receiver(post_delete, sender=Association)
def delete_logo_on_delete(sender, instance, **kwargs):
    if instance.logo:
        try:
            if os.path.isfile(instance.logo.path):
                os.remove(instance.logo.path)
        except Exception:
            pass

@receiver(pre_save, sender=Evenement)
def delete_old_piece(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Evenement.objects.get(pk=instance.pk).piece_jointe
    except Evenement.DoesNotExist:
        return
    new = instance.piece_jointe
    if old and old != new:
        try:
            if os.path.isfile(old.path):
                os.remove(old.path)
        except Exception:
            pass

@receiver(post_delete, sender=Evenement)
def delete_piece_on_delete(sender, instance, **kwargs):
    if instance.piece_jointe:
        try:
            if os.path.isfile(instance.piece_jointe.path):
                os.remove(instance.piece_jointe.path)
        except Exception:
            pass

