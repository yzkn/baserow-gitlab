import dataclasses
from copy import deepcopy
from typing import Optional, Tuple, List

from django.contrib.auth.models import AbstractUser
from django.db.models.fields.related import ManyToManyField

from baserow.contrib.database.db.schema import safe_django_schema_editor
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field, SpecificFieldForUpdate
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.action.scopes import TableActionScopeType
from baserow.core.action.models import Action
from baserow.core.action.registries import ActionType, ActionScopeStr

from .models import SelectOption


class UpdateFieldActionType(ActionType):
    type = "update_field"

    @dataclasses.dataclass
    class Params:
        field_id: int
        original_type: str
        original_data: dict
        new_type: str
        new_data: dict

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        field: SpecificFieldForUpdate,
        new_type_name: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Field, List[Field]]:

        """
        Updates the values and/or type of the given field. See
        baserow.contrib.database.fields.handler.FieldHandler.update_field for further
        details.

        :param user: The user on whose behalf the table is updated.
        :param field: The field instance that needs to be updated.
        :param new_type_name: If the type needs to be changed it can be provided here.
        :return: The updated field instance. If return_updated_field is set then any
            updated fields as a result of updated the field are returned in a list
            as a second tuple value.

        :return: TODO
        """

        def get_prepared_values_for_data(view, field_type):
            return {
                key: value
                for key, value in field_type.export_prepared_values(field).items()
            }

        # Must create action first, because we need the ID.
        action = cls.register_action(user, {}, cls.scope(field.table_id))

        original_field_type = field_type_registry.get_by_model(field)
        original_type = original_field_type.type
        original_data = get_prepared_values_for_data(field, original_field_type)

        # Create a copy of the column or through table, because that's what we'll be
        # restoring when undoing the action.
        original_model = field.table.get_model(
            field_ids=[], fields=[field], add_dependencies=False
        )
        cls._copy_field(original_model, field.db_column, f"action_{action.id}")

        field, related_fields = FieldHandler().update_field(
            user, field, new_type_name, return_updated_fields=True, **kwargs
        )

        new_field_type = field_type_registry.get_by_model(field)
        new_type = new_field_type.type
        new_data = get_prepared_values_for_data(field, new_field_type)

        # Now that we have all the params, we can update the action.
        action.params = cls.Params(
            field_id=field.id,
            original_type=original_type,
            original_data=original_data,
            new_type=new_type,
            new_data=new_data,
        )
        if "select_options" in action.params.original_data:
            print(action.params.original_data["select_options"])
        action.save()

        return field, related_fields

    @classmethod
    def scope(cls, table_id) -> ActionScopeStr:
        return TableActionScopeType.value(table_id)

    @classmethod
    def undo(
        cls,
        user: AbstractUser,
        params: Params,
        action_being_undone: Action,
    ):
        field = FieldHandler().get_specific_field_for_update(params.field_id).specific
        field_options = deepcopy(params.original_data.get("select_options", []))

        new_model = field.table.get_model(
            field_ids=[], fields=[field], add_dependencies=False
        )

        # Copy the current data to a temporarily field, because it could later be
        # needed for a redo action.
        cls._copy_field(
            new_model,
            field.db_column,
            f"action_{action_being_undone.id}_undone",
        )

        field, related_fields = FieldHandler().update_field(
            user,
            field,
            params.original_type,
            return_updated_fields=True,
            migrate_data=False,
            **params.original_data,
        )

        original_model = field.table.get_model(
            field_ids=[], fields=[field], add_dependencies=False
        )
        cls._restore_field(
            original_model, field.db_column, f"action_{action_being_undone.id}"
        )

        # @TODO query optimize this
        field.select_options.all().delete()
        for field_option in field_options:
            SelectOption.objects.create(**field_option, field=field)

    @classmethod
    def redo(cls, user: AbstractUser, params: Params, action_being_redone: Action):
        # @TODO
        # * Rename the existing column/m2m to a temporary name
        # * Rename the backed up column/m2m to the production name
        # * Update the field without actually doing the conversion, just change the
        #   schema.
        print("@TODO redo")

    @classmethod
    def _restore_field(cls, model, field_name, backup_field_name):
        original_model_field = model._meta.get_field(field_name)
        original_is_m2m = isinstance(original_model_field, ManyToManyField)

        with safe_django_schema_editor(atomic=False) as schema_editor:
            if original_is_m2m:
                through = original_model_field.remote_field.through
                table_name = through._meta.db_table
                schema_editor.execute(
                    f"""
                    DELETE FROM {table_name} WHERE true
                    """
                )
                schema_editor.execute(
                    f"""
                    INSERT INTO {table_name} (SELECT * FROM {backup_field_name})
                    """
                )
            else:
                table_name = model._meta.db_table
                schema_editor.execute(
                    f"""
                    UPDATE {table_name} SET {field_name} = {backup_field_name} WHERE true
                    """
                )

    @classmethod
    def _copy_field(cls, model, original_field_name, new_field_name):
        """
        @TODO docs

        :param model:
        :param original_field_name:
        :param new_field_name:
        :return:
        """

        original_model_field = model._meta.get_field(original_field_name)
        original_is_m2m = isinstance(original_model_field, ManyToManyField)

        with safe_django_schema_editor(atomic=False) as schema_editor:
            backup_model_field = deepcopy(original_model_field)

            if original_is_m2m:
                through = backup_model_field.remote_field.through
                old_table_name = through._meta.db_table
                through._meta.db_table = new_field_name
                schema_editor.add_field(model, backup_model_field)
                schema_editor.execute(
                    f"""
                    INSERT INTO {new_field_name} (SELECT * FROM {old_table_name})
                    """
                )
            else:
                old_column = backup_model_field.column
                table_name = model._meta.db_table
                backup_model_field.column = new_field_name
                schema_editor.add_field(model, backup_model_field)
                schema_editor.execute(
                    f"""
                    UPDATE {table_name} SET {new_field_name} = {old_column} WHERE true
                    """
                )

        return original_is_m2m
