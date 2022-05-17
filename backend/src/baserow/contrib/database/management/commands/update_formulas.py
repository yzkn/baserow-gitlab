from django.core.management.base import BaseCommand

from baserow.contrib.database.formula import FormulaHandler
from baserow.contrib.database.table.cache import clear_generated_model_cache


class Command(BaseCommand):
    help = (
        "Ensures all formulas have been correctly calculated for the current "
        "formula version."
    )

    def handle(self, *args, **options):
        clear_generated_model_cache()
        FormulaHandler.recalculate_formulas_according_to_version()
