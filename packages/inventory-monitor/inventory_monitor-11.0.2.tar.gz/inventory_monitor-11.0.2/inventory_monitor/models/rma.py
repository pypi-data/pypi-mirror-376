from django.db import models, transaction
from django.urls import reverse
from netbox.models import NetBoxModel
from utilities.choices import ChoiceSet
from utilities.querysets import RestrictedQuerySet


class RMAStatusChoices(ChoiceSet):
    key = "cesnet_service_path_plugin.rma.status"

    PENDING = "pending"
    SHIPPED = "shipped"
    RECEIVED = "received"
    INVESTIGATING = "investigating"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

    CHOICES = [
        (PENDING, "Pending", "yellow"),
        (SHIPPED, "Shipped to Vendor", "blue"),
        (RECEIVED, "Received by Vendor", "blue"),
        (INVESTIGATING, "Under Investigation", "blue"),
        (APPROVED, "Approved", "green"),
        (REJECTED, "Rejected", "red"),
        (COMPLETED, "Completed", "green"),
    ]


class RMA(NetBoxModel):
    objects = RestrictedQuerySet.as_manager()

    rma_number = models.CharField(
        max_length=100,
        unique=True,
        help_text="RMA identifier provided by vendor",
        blank=True,
        null=True,
    )

    asset = models.ForeignKey(to="inventory_monitor.Asset", on_delete=models.PROTECT, related_name="rmas")

    original_serial = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Original serial number of the returned asset",
    )

    replacement_serial = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="New serial number of the replacement asset",
    )

    status = models.CharField(
        max_length=30,
        choices=RMAStatusChoices,
        default=RMAStatusChoices.INVESTIGATING,
        blank=False,
        null=False,
    )

    date_issued = models.DateField(null=True, blank=True, help_text="Date when RMA was created")

    date_replaced = models.DateField(null=True, blank=True, help_text="Date when item was replaced")

    issue_description = models.TextField(help_text="Description of the issue with the asset")

    vendor_response = models.TextField(blank=True, help_text="Vendor response/resolution details")

    class Meta:
        ordering = ["date_issued"]
        verbose_name = "RMA"
        verbose_name_plural = "RMAs"

    def __str__(self):
        if self.rma_number:
            return f"RMA {self.rma_number} - {self.asset}"
        return f"RMA {self.pk} - {self.asset}"

    def get_absolute_url(self):
        return reverse("plugins:inventory_monitor:rma", args=[self.pk])

    def get_status_color(self):
        return RMAStatusChoices.colors.get(self.status, "gray")

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Automatically populate original_serial from asset if not set
        if not self.original_serial and self.asset:
            self.original_serial = self.asset.serial

        # Check if this is an existing RMA with status change
        if self.pk:
            previous = RMA.objects.get(pk=self.pk)
            if previous.status != self.status and self.status == RMAStatusChoices.COMPLETED:
                self.update_asset_serial()
        # Check if this is a new RMA with COMPLETED status
        elif self.status == RMAStatusChoices.COMPLETED:
            self.update_asset_serial()

        super().save(*args, **kwargs)

    def update_asset_serial(self):
        """
        Update the associated asset's serial number when replacement is received
        """
        if self.status == RMAStatusChoices.COMPLETED and self.replacement_serial:
            self.asset.serial = self.replacement_serial
            self.asset.save()
