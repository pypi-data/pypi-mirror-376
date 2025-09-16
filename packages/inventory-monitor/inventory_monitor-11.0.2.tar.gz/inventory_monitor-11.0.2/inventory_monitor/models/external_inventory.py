from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from inventory_monitor.models.asset import Asset
from inventory_monitor.settings import get_external_inventory_status_config_safe


class ExternalInventory(NetBoxModel):
    """
    Model representing inventory items imported from external inventory management system

    Contains data directly mapped from the external system's export structure.
    """

    external_id = models.CharField(
        unique=True,
        verbose_name="External System ID",
        help_text="Unique identifier for the item in external inventory system (ID)",
        # TODO: after Migration and setting up the external_id, make this field non nullable and blankable
        null=True,
        blank=True,
        max_length=64,
    )

    inventory_number = models.CharField(
        max_length=64,
        verbose_name="Inventory Number (Asset Number)",
        help_text="External asset identifier (INVENT_CIS)",
    )
    name = models.CharField(max_length=255, verbose_name="Name", help_text="Item name/description (NAZEV)")
    serial_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Serial Number",
        help_text="Serial or production number (CVYR)",
    )
    person_id = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Person ID",
        help_text="ID of the person responsible for this item (OSOBA_OSCISLO)",
    )
    person_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Person Name",
        help_text="Name of the person responsible for this item (OSOBA)",
    )
    location_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Location Code",
        help_text="Code representing the location of this item (KOD_UMISTENI)",
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Location",
        help_text="Description of item location (UMISTENI)",
    )
    department_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Department Code",
        help_text="Department code (AKTIVITA)",
    )
    project_code = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Project Code",
        help_text="Project code (PROJEKT)",
    )
    user_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="User Name",
        help_text="Name of the user (NAZEV_UZIV)",
    )
    user_note = models.TextField(
        blank=True,
        null=True,
        verbose_name="User Notes",
        help_text="Notes from the user (POZN_UZIV)",
    )
    split_asset = models.CharField(
        # max_length=1,
        blank=True,
        null=True,
        verbose_name="Split Asset",
        help_text="Whether this is a split/shared asset (DELENY_MAJETEK): A=Yes, N=No",
    )
    status = models.CharField(
        # max_length=1,
        blank=True,
        null=True,
        verbose_name="Status",
        help_text="Current status of the item (STAV): 1=Active, 0=Inactive",
    )

    ############## EXTRA FIELDS
    assets = models.ManyToManyField(
        to=Asset,
        related_name="external_inventory_items",
        blank=True,
        verbose_name="Assets",
        help_text="Associated internal asset records",
    )

    class Meta:
        ordering = ("inventory_number", "name")
        verbose_name = "External Inventory Item"
        verbose_name_plural = "External Inventory Items"
        indexes = [
            models.Index(fields=["inventory_number"], name="ext_inv_invnum_idx"),
            models.Index(fields=["serial_number"], name="ext_inv_serial_idx"),
            models.Index(fields=["person_id"], name="ext_inv_personid_idx"),
            models.Index(fields=["location_code"], name="ext_inv_loccode_idx"),
            models.Index(fields=["department_code"], name="ext_inv_deptcode_idx"),
            models.Index(fields=["project_code"], name="ext_inv_projcode_idx"),
            models.Index(fields=["status"], name="ext_inv_status_idx"),
        ]
        # unique_together = [["inventory_number"]]

    def __str__(self):
        return f"{self.inventory_number}: {self.name}"

    def get_absolute_url(self):
        return reverse("plugins:inventory_monitor:externalinventory", args=[self.pk])

    def get_status_color(self):
        """Get the Bootstrap color class for the current status from configuration"""
        status_config, is_configured = get_external_inventory_status_config_safe()

        if not is_configured:
            return "secondary"

        # Get color for current status, default to 'secondary' if not found
        status_info = status_config.get(str(self.status), {})
        return status_info.get("color", "secondary")

    def get_status_display(self):
        """Get the human-readable status label from configuration"""

        status_config, is_configured = get_external_inventory_status_config_safe()

        if not is_configured:
            return str(self.status)

        # Get label for current status, default to the status value if not found
        status_info = status_config.get(str(self.status), {})
        return status_info.get("label", str(self.status))
