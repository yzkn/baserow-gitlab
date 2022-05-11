from django.db import migrations
from baserow.contrib.database.models import TableWebhookEvent


def forward(apps, schema_editor):
    TableWebhookEvent.objects.filter(event_type='row.created').update(event_type='rows.created')
    TableWebhookEvent.objects.filter(event_type='row.updated').update(event_type='rows.updated')
    TableWebhookEvent.objects.filter(event_type='row.deleted').update(event_type='rows.deleted')


def reverse(apps, schema_editor):
    ...


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0071_alter_linkrowfield_link_row_relation_id'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
