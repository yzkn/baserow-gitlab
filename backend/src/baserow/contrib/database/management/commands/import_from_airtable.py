import sys
import re
from tqdm import tqdm

from django.db import transaction
from django.core.management.base import BaseCommand

from baserow.core.models import Group
from baserow.core.utils import Progress
from baserow.contrib.database.airtable.handler import import_from_airtable_to_group


class Command(BaseCommand):
    help = (
        "This management command copies all the data from a publicly shared Airtable "
        "base and tries to import a copy into the provided group. A base can be "
        "shared publicly by clicking on the `Share` button in the top right corner and "
        "then create a `Shared base link`. The resulting URL must be provided as "
        "argument."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "group_id",
            type=int,
            help="The group ID where a copy of the imported Airtable base must be "
            "added to.",
        )
        parser.add_argument(
            "public_base_url",
            type=str,
            help="The URL of the publicly shared Airtable base "
            "(e.g. https://airtable.com/shrxxxxxxxxxxxxxx).",
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
            nonlocal progress_bar
            progress_bar.set_description(state)
            progress_bar.update(percentage - progress_bar.n)

        progress = Progress(100)
        progress.register_updated_event(progress_updated)
        progress_bar = tqdm(total=100)

        share_id = f"shr{result.group(1)}"
        import_from_airtable_to_group(group, share_id, parent_progress=(progress, 100))
        progress_bar.close()
        self.stdout.write(f"Your base has been imported.")
