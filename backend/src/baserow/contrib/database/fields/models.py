from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.functional import lazy

from baserow.contrib.database.fields.mixins import (
    BaseDateMixin,
    TimezoneMixin,
    DATE_FORMAT_CHOICES,
    DATE_TIME_FORMAT_CHOICES,
    DATE_FORMAT,
    DATE_TIME_FORMAT,
)
from baserow.contrib.database.formula.registries import formula_type_handler_registry
from baserow.contrib.database.mixins import ParentFieldTrashableModelMixin
from baserow.core.mixins import (
    OrderableMixin,
    PolymorphicContentTypeMixin,
    CreatedAndUpdatedOnMixin,
    TrashableModelMixin,
)
from baserow.core.utils import to_snake_case, remove_special_characters

NUMBER_TYPE_INTEGER = "INTEGER"
NUMBER_TYPE_DECIMAL = "DECIMAL"
NUMBER_TYPE_CHOICES = (
    ("INTEGER", "Integer"),
    ("DECIMAL", "Decimal"),
)

NUMBER_MAX_DECIMAL_PLACES = 5

NUMBER_DECIMAL_PLACES_CHOICES = [
    (1, "1.0"),
    (2, "1.00"),
    (3, "1.000"),
    (4, "1.0000"),
    (NUMBER_MAX_DECIMAL_PLACES, "1.00000"),
]

# Allow the underlying database fields to store int's without a decimal place.
NUMBER_DECIMAL_PLACES_INTERNAL_CHOICES = [(0, "1")] + NUMBER_DECIMAL_PLACES_CHOICES


def get_default_field_content_type():
    return ContentType.objects.get_for_model(Field)


class Field(
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    PolymorphicContentTypeMixin,
    models.Model,
):
    """
    Because each field type can have custom settings, for example precision for a number
    field, values for an option field or checkbox style for a boolean field we need a
    polymorphic content type to store these settings in another table.
    """

    table = models.ForeignKey("database.Table", on_delete=models.CASCADE)
    order = models.PositiveIntegerField(help_text="Lowest first.")
    name = models.CharField(max_length=255)
    primary = models.BooleanField(
        default=False,
        help_text="Indicates if the field is a primary field. If `true` the field "
        "cannot be deleted and the value should represent the whole row.",
    )
    content_type = models.ForeignKey(
        ContentType,
        verbose_name="content type",
        related_name="database_fields",
        on_delete=models.SET(get_default_field_content_type),
    )

    class Meta:
        ordering = (
            "-primary",
            "order",
        )

    @classmethod
    def get_last_order(cls, table):
        queryset = Field.objects.filter(table=table)
        return cls.get_highest_order_of_queryset(queryset) + 1

    @property
    def db_column(self):
        return f"field_{self.id}"

    @property
    def model_attribute_name(self):
        """
        Generates a pascal case based model attribute name based on the field name.

        :return: The generated model attribute name.
        :rtype: str
        """

        name = remove_special_characters(self.name, False)
        name = to_snake_case(name)

        if name[0].isnumeric():
            name = f"field_{name}"

        return name


class SelectOption(ParentFieldTrashableModelMixin, models.Model):
    value = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField()
    field = models.ForeignKey(
        Field, on_delete=models.CASCADE, related_name="select_options"
    )

    class Meta:
        ordering = (
            "order",
            "id",
        )

    def __str__(self):
        return self.value


class TextField(Field):
    text_default = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="If set, this value is going to be added every time a new row "
        "created.",
    )


class LongTextField(Field):
    pass


class URLField(Field):
    pass


class NumberField(Field):
    number_type = models.CharField(
        max_length=32, choices=NUMBER_TYPE_CHOICES, default=NUMBER_TYPE_INTEGER
    )
    number_decimal_places = models.IntegerField(
        choices=NUMBER_DECIMAL_PLACES_INTERNAL_CHOICES,
        default=1,
        help_text="The amount of digits allowed after the point.",
    )
    number_negative = models.BooleanField(
        default=False, help_text="Indicates if negative values are allowed."
    )

    def save(self, *args, **kwargs):
        """Check if the number_type and number_decimal_places has a valid choice."""

        if not any(self.number_type in _tuple for _tuple in NUMBER_TYPE_CHOICES):
            raise ValueError(f"{self.number_type} is not a valid choice.")
        if self.number_type == NUMBER_TYPE_DECIMAL and not any(
            self.number_decimal_places in _tuple
            for _tuple in NUMBER_DECIMAL_PLACES_CHOICES
        ):
            raise ValueError(f"{self.number_decimal_places} is not a valid choice.")
        super(NumberField, self).save(*args, **kwargs)


class BooleanField(Field):
    pass


class DateField(Field, BaseDateMixin):
    pass


class LastModifiedField(Field, BaseDateMixin, TimezoneMixin):
    pass


class CreatedOnField(Field, BaseDateMixin, TimezoneMixin):
    pass


class LinkRowField(Field):
    THROUGH_DATABASE_TABLE_PREFIX = "database_relation_"
    link_row_table = models.ForeignKey(
        "database.Table",
        on_delete=models.CASCADE,
        help_text="The table that the field has a relation with.",
        blank=True,
    )
    link_row_related_field = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        help_text="The relation field in the other table.",
        null=True,
        blank=True,
    )
    link_row_relation_id = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Every LinkRow needs to have a unique relation id that is shared with the
        related link row field in the other table.
        """

        if self.link_row_relation_id is None:
            self.link_row_relation_id = self.get_new_relation_id()

        super().save(*args, **kwargs)

    @property
    def through_table_name(self):
        """
        Generating a unique through table name based on the relation id.

        :return: The table name of the through model.
        :rtype: string
        """

        if not self.link_row_relation_id:
            raise ValueError("The link row field does not yet have a relation id.")

        return f"{self.THROUGH_DATABASE_TABLE_PREFIX}{self.link_row_relation_id}"

    @staticmethod
    def get_new_relation_id():
        last_id = (
            LinkRowField.objects_and_trash.all().aggregate(
                largest=models.Max("link_row_relation_id")
            )["largest"]
            or 0
        )
        return last_id + 1


class EmailField(Field):
    pass


class FileField(Field):
    pass


class SingleSelectField(Field):
    pass


class PhoneNumberField(Field):
    pass


class FormulaField(Field):
    formula = models.TextField()
    error = models.TextField(null=True, blank=True)

    formula_type = models.TextField(
        choices=lazy(formula_type_handler_registry.get_types_as_tuples, list)(),
        default="invalid",
    )
    number_type = models.CharField(
        max_length=32, choices=NUMBER_TYPE_CHOICES, default=None, null=True
    )
    number_decimal_places = models.IntegerField(
        choices=NUMBER_DECIMAL_PLACES_INTERNAL_CHOICES,
        default=None,
        null=True,
        help_text="The amount of digits allowed after the point.",
    )
    date_format = models.CharField(
        choices=DATE_FORMAT_CHOICES,
        default=None,
        max_length=32,
        help_text="EU (20/02/2020), US (02/20/2020) or ISO (2020-02-20)",
        null=True,
    )
    date_include_time = models.BooleanField(
        default=None,
        help_text="Indicates if the field also includes a time.",
        null=True,
    )
    date_time_format = models.CharField(
        choices=DATE_TIME_FORMAT_CHOICES,
        default=None,
        null=True,
        max_length=32,
        help_text="24 (14:30) or 12 (02:30 PM)",
    )

    def get_psql_format(self):
        """
        Returns the sql datetime format as a string based on the field's properties.
        This could for example be 'YYYY-MM-DD HH12:MIAM'.

        :return: The sql datetime format based on the field's properties.
        :rtype: str
        """

        return self._get_format("sql")

    def _get_format(self, format_type):
        date_format = DATE_FORMAT[self.date_format][format_type]
        time_format = DATE_TIME_FORMAT[self.date_time_format][format_type]
        if self.date_include_time:
            return f"{date_format} {time_format}"
        else:
            return date_format

    def compare(self, other):
        # TODO Why do we need to use str
        return (
            str(self.formula) == str(other.formula)
            and str(self.error) == str(other.error)
            and str(self.formula_type) == str(other.formula_type)
            and str(self.number_type) == str(other.number_type)
            and str(self.number_decimal_places) == str(other.number_decimal_places)
        )

    def save(self, *args, **kwargs):
        """Check if the number_type and number_decimal_places has a valid choice."""

        if self.formula_type == "numeric":
            # TODO: dedupe somehow
            if not any(self.number_type in _tuple for _tuple in NUMBER_TYPE_CHOICES):
                raise ValueError(f"{self.number_type} is not a valid choice.")
            if self.number_type == NUMBER_TYPE_DECIMAL and not any(
                self.number_decimal_places in _tuple
                for _tuple in NUMBER_DECIMAL_PLACES_CHOICES
            ):
                raise ValueError(f"{self.number_decimal_places} is not a valid choice.")
        super().save(*args, **kwargs)
