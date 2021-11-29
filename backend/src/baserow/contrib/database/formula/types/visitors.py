from typing import Any, Set, List

from baserow.contrib.database.fields.dependencies.exceptions import (
    SelfReferenceFieldDependencyError,
)
from baserow.contrib.database.fields.dependencies.types import FieldDependencies
from baserow.contrib.database.formula.ast.tree import (
    BaserowFunctionCall,
    BaserowStringLiteral,
    BaserowFieldReference,
    BaserowIntegerLiteral,
    BaserowDecimalLiteral,
    BaserowBooleanLiteral,
    BaserowLookupReference,
)
from baserow.contrib.database.formula.ast.function_def import BaserowFunctionDefinition
from baserow.contrib.database.formula.ast.visitors import BaserowFormulaASTVisitor, X
from baserow.contrib.database.formula.types.formula_type import (
    UnTyped,
    BaserowFormulaValidType,
)
from baserow.contrib.database.formula.types.formula_types import (
    BaserowExpression,
    BaserowFormulaType,
    BaserowFormulaTextType,
    BaserowFormulaNumberType,
    BaserowFormulaBooleanType,
)


class FunctionsUsedVisitor(
    BaserowFormulaASTVisitor[Any, Set[BaserowFunctionDefinition]]
):
    def visit_lookup_reference(self, lookup_reference: BaserowLookupReference) -> X:
        return set()

    def visit_field_reference(self, field_reference: BaserowFieldReference):
        return set()

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()

    def visit_boolean_literal(
        self, boolean_literal: BaserowBooleanLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()

    def visit_function_call(
        self, function_call: BaserowFunctionCall
    ) -> Set[BaserowFunctionDefinition]:
        all_used_functions = {function_call.function_def}
        for expr in function_call.args:
            all_used_functions.update(expr.accept(self))

        return all_used_functions

    def visit_int_literal(
        self, int_literal: BaserowIntegerLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()

    def visit_decimal_literal(
        self, decimal_literal: BaserowDecimalLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()


class FieldReferenceExtractingVisitor(
    BaserowFormulaASTVisitor[UnTyped, FieldDependencies]
):
    """
    Calculates and returns all the field dependencies that the baserow expression has.
    """

    def __init__(self, table, field_lookup_cache):
        self.field_lookup_cache = field_lookup_cache
        self.table = table

    def visit_lookup_reference(
        self, lookup_reference: BaserowLookupReference[UnTyped]
    ) -> FieldDependencies:
        return {(lookup_reference.through_field, lookup_reference.target_field)}

    def visit_field_reference(
        self, field_reference: BaserowFieldReference[UnTyped]
    ) -> FieldDependencies:
        field = self.field_lookup_cache.lookup_by_name(
            self.table, field_reference.referenced_field_name
        )
        from baserow.contrib.database.fields.models import LinkRowField

        if field is not None and isinstance(field, LinkRowField):
            primary_field = field.get_related_primary_field()
            return {
                (
                    field_reference.referenced_field_name,
                    primary_field.name if primary_field is not None else "unknown",
                )
            }

        return {field_reference.referenced_field_name}

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()

    def visit_function_call(
        self, function_call: BaserowFunctionCall[UnTyped]
    ) -> FieldDependencies:
        field_references: FieldDependencies = set()
        for expr in function_call.args:
            field_references.update(expr.accept(self))
        return field_references

    def visit_int_literal(
        self, int_literal: BaserowIntegerLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()

    def visit_decimal_literal(
        self, decimal_literal: BaserowDecimalLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()

    def visit_boolean_literal(
        self, boolean_literal: BaserowBooleanLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()


class FormulaTypingVisitor(
    BaserowFormulaASTVisitor[UnTyped, BaserowExpression[BaserowFormulaType]]
):
    def __init__(self, field_being_typed, field_lookup_cache):
        self.field_lookup_cache = field_lookup_cache
        self.field_being_typed = field_being_typed

    def visit_lookup_reference(
        self, lookup_reference: BaserowLookupReference[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        from baserow.contrib.database.fields.models import LinkRowField

        through_field_name = lookup_reference.through_field

        if through_field_name == self.field_being_typed.name:
            raise SelfReferenceFieldDependencyError()

        through_field = self.field_lookup_cache.lookup_by_name(
            self.field_being_typed.table, through_field_name
        )
        if through_field is None:
            return lookup_reference.with_invalid_type(
                f"cannot lookup through unknown field {through_field_name}"
            )
        elif not isinstance(through_field, LinkRowField):
            return lookup_reference.with_invalid_type(
                f"cannot lookup through non link row field {through_field_name}"
            )

        target_table = through_field.link_row_table
        target_field_name = lookup_reference.target_field

        target_field = self.field_lookup_cache.lookup_by_name(
            target_table, target_field_name
        )
        if target_field is None:
            return lookup_reference.with_invalid_type(
                f"references the deleted or unknown field"
                f" {target_field_name} in table "
                f"{target_table.name}"
            )
        else:
            from baserow.contrib.database.fields.registries import field_type_registry

            target_field_type = field_type_registry.get_by_model(target_field)
            # Can return a lookup to the primary field of a link row field
            # Can return a single select extract func
            target_expression = target_field_type.to_baserow_formula_expression(
                target_field, for_lookup=True
            )
            if target_expression.wrapper:
                target_expression = (
                    target_expression.expression_type.unwrap_at_field_level(
                        target_expression
                    )
                )
            from baserow.contrib.database.formula.registries import (
                formula_function_registry,
            )

            db_lookup = formula_function_registry.get("db_lookup")
            return db_lookup.call_and_type_with_args(
                [
                    BaserowStringLiteral(
                        through_field.db_column, BaserowFormulaTextType()
                    ),
                    target_expression,
                ]
            )

    def visit_field_reference(
        self, field_reference: BaserowFieldReference[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        from baserow.contrib.database.fields.registries import field_type_registry

        referenced_field_name = field_reference.referenced_field_name
        if referenced_field_name == self.field_being_typed.name:
            raise SelfReferenceFieldDependencyError()

        table = self.field_being_typed.table
        referenced_field = self.field_lookup_cache.lookup_by_name(
            table, referenced_field_name
        )
        if referenced_field is None:
            return field_reference.with_invalid_type(
                f"references the deleted or unknown field"
                f" {field_reference.referenced_field_name}"
            )
        else:
            field_type = field_type_registry.get_by_model(referenced_field)
            # Can return a lookup to the primary field of a link row field
            # Can return a single select extract func
            expression = field_type.to_baserow_formula_expression(referenced_field)
            if expression.wrapper:
                expression = expression.expression_type.unwrap_at_field_level(
                    expression
                )
            return expression

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return string_literal.with_valid_type(BaserowFormulaTextType())

    def visit_function_call(
        self, function_call: BaserowFunctionCall[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        typed_args: List[BaserowExpression[BaserowFormulaValidType]] = []
        pending_aggregate_filter = None
        for index, expr in enumerate(function_call.args):
            arg_expr = expr.accept(self)
            if arg_expr.pending_aggregate_filter:
                if pending_aggregate_filter is not None:
                    return function_call.with_invalid_type(
                        "cannot provide multiple filtered inputs to a function"
                    )
                else:
                    pending_aggregate_filter = arg_expr
            typed_args.append(arg_expr)

        if (
            pending_aggregate_filter is not None
            and not function_call.function_def.aggregate
        ):
            return function_call.with_invalid_type(
                "the filter function must be wrapped directly by an aggregate function"
                "like sum,avg,count etc."
            )
        return function_call.with_pending_aggregate_filter(
            pending_aggregate_filter
        ).type_function_given_typed_args(typed_args)

    def visit_int_literal(
        self, int_literal: BaserowIntegerLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return int_literal.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=0,
            ),
        )

    def visit_decimal_literal(
        self, decimal_literal: BaserowDecimalLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return decimal_literal.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=decimal_literal.num_decimal_places()
            )
        )

    def visit_boolean_literal(
        self, boolean_literal: BaserowBooleanLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return boolean_literal.with_valid_type(BaserowFormulaBooleanType())
