from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from baserow.core.handler import CoreHandler
from baserow.core.models import Template

User = get_user_model()


class Command(BaseCommand):
    help = "Fills a table with random data."

    def handle(self, *args, **options):
        for t in Template.objects.all():
            first = User.objects.first()
            CoreHandler().install_template(first, first.group_set.first(), t)
