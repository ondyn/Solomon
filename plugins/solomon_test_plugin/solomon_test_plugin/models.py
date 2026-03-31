from django.db import models

from netbox.models import NetBoxModel


class TestItem(NetBoxModel):
    """A simple model to verify plugin models work correctly."""

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("plugins:solomon_test_plugin:testitem", kwargs={"pk": self.pk})
