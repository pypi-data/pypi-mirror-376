from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel
from utilities.fields import ColorField


class AssetType(NetBoxModel):
    """
    Model for categorizing and organizing assets by type.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name"),
    )
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True, verbose_name=_("description"))
    color = ColorField(verbose_name=_("color"), blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = _("asset type")
        verbose_name_plural = _("asset types")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("plugins:inventory_monitor:assettype", args=[self.pk])
