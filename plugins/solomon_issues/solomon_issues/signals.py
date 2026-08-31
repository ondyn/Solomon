"""Signal handlers keeping the issue timeline and subscriber list consistent."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .choices import IssueEventTypeChoices
from .models import Issue, IssueEvent, IssueSubscriber


@receiver(post_save, sender=Issue)
def bootstrap_issue(sender, instance, created, **kwargs):
    if not created:
        return

    if not IssueEvent.objects.filter(
        issue=instance, event_type=IssueEventTypeChoices.EVENT_CREATED
    ).exists():
        instance.log_event(
            IssueEventTypeChoices.EVENT_CREATED,
            message=str(_("Problem reported.")),
            user=instance.reporter_user,
            actor_name=instance.reporter_name,
        )

    email = instance.reporter_email or (
        instance.reporter_user.email if instance.reporter_user else ""
    )
    if email:
        IssueSubscriber.objects.get_or_create(
            issue=instance,
            email=email,
            defaults={"name": instance.reporter_name, "is_reporter": True},
        )
