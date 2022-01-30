import sys
import re

from django.db import transaction
from django.core.management.base import BaseCommand

from baserow.core.models import Group
from baserow.contrib.database.airtable.handler import import_from_airtable_to_group
from baserow.contrib.database.airtable.progress import Progress


class Command(BaseCommand):
    help = "@TODO docs"

    def add_arguments(self, parser):
        parser.add_argument(
            "group_id",
            type=int,
            help="@TODO",
        )
        parser.add_argument(
            "public_base_url",
            type=str,
            help="@TODO",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        group_id = options["group_id"]
        public_base_url = options["public_base_url"]

        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The group with id {group_id} was not found.")
            )
            sys.exit(1)

        result = re.search(r"https:\/\/airtable.com\/shr(.*)$", public_base_url)

        if not result:
            self.stdout.write(
                self.style.ERROR(
                    f"Please provide a valid shared Airtable URL (e.g. "
                    f"https://airtable.com/shrxxxxxxxxxxxxxx)"
                )
            )

        def progress_updated(percentage, state):
            print(f"progress {percentage} {state}")

        progress = Progress(100)
        progress.register_updated_event(progress_updated)

        share_id = f"shr{result.group(1)}"
        print(
            import_from_airtable_to_group(
                group, share_id, parent_progress=(progress, 100)
            )
        )
        self.stdout.write(f"Your base has been imported.")
