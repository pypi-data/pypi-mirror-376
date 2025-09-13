import django_tables2 as tables
from netbox.tables import ChoiceFieldColumn, NetBoxTable, columns

from inventory_monitor.helpers import NumberColumn
from inventory_monitor.models import Contract


class ContractTable(NetBoxTable):
    name = tables.Column(linkify=True)
    contractor = tables.Column(linkify=True)
    subcontracts_count = tables.Column()
    invoices_count = tables.Column()
    contract_type = tables.Column(orderable=False)
    attachments_count = tables.Column()
    parent = tables.Column(linkify=True)
    type = ChoiceFieldColumn()
    price = NumberColumn()
    tags = columns.TagColumn()

    class Meta(NetBoxTable.Meta):
        model = Contract
        fields = (
            "pk",
            "id",
            "name",
            "name_internal",
            "contractor",
            "type",
            "contract_type",
            "price",
            "signed",
            "accepted",
            "invoicing_start",
            "invoicing_end",
            "parent",
            "comments",
            "invoices_count",
            "subcontracts_count",
            "attachments_count",
            "actions",
        )
        default_columns = (
            "id",
            "name",
            "name_internal",
            "contractor",
            "type",
            "contract_type",
            "price",
            "signed",
            "accepted",
            "invoicing_start",
            "invoicing_end",
            "parent",
            "attachments_count",
        )
