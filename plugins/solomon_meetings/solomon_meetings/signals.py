from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from solomon_property.models import Flat, FlatOwner

from .models import VoteWeightStyle


@receiver(post_save, sender=FlatOwner)
def sync_vote_styles_on_flat_owner_save(sender, instance, **kwargs):
    VoteWeightStyle.sync_current_share_styles()


@receiver(post_delete, sender=FlatOwner)
def sync_vote_styles_on_flat_owner_delete(sender, instance, **kwargs):
    VoteWeightStyle.sync_current_share_styles()


@receiver(post_save, sender=Flat)
def sync_vote_styles_on_flat_share_save(sender, instance, **kwargs):
    VoteWeightStyle.sync_current_share_styles()
