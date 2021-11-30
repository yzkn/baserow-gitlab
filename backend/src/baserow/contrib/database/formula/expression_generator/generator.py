from typing import Optional, Type

from django.db.models import (
    Expression,
    Value,
    F,
    DecimalField,
    BooleanField,
    fields,
    ExpressionWrapper,
    Model,
    Q,
    FilteredRelation,
    Subquery,
    JSONField,
    OuterRef,
)
from django.db.models.functions import Cast, JSONObject

from baserow.contrib.database.formula.ast.exceptions import UnknownFieldReference
from baserow.contrib.database.formula.ast.tree import (
    BaserowStringLiteral,
    BaserowFunctionCall,
    BaserowIntegerLiteral,
    BaserowFieldReference,
    BaserowExpression,
    BaserowDecimalLiteral,
    BaserowBooleanLiteral,
    BaserowLookupReference,
)
from baserow.contrib.database.formula.ast.visitors import BaserowFormulaASTVisitor, X
from baserow.contrib.database.formula.exceptions import formula_exception_handler
from baserow.contrib.database.formula.parser.exceptions import (
    MaximumFormulaSizeError,
)
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaType,
    BaserowFormulaInvalidType,
)


def baserow_expression_to_update_django_expression(
    baserow_expression: BaserowExpression[BaserowFormulaType],
    model: Type[Model],
):
    return _baserow_expression_to_django_expression(baserow_expression, model, None)


def baserow_expression_to_single_row_update_django_expression(
    baserow_expression: BaserowExpression[BaserowFormulaType],
    model_instance: Model,
):
    return _baserow_expression_to_django_expression(
        baserow_expression, type(model_instance), model_instance, insert=False
    )


def baserow_expression_to_insert_django_expression(
    baserow_expression: BaserowExpression[BaserowFormulaType],
    model_instance: Model,
):
    return _baserow_expression_to_django_expression(
        baserow_expression, type(model_instance), model_instance, insert=True
    )


def _baserow_expression_to_django_expression(
    baserow_expression: BaserowExpression[BaserowFormulaType],
    model: Type[Model],
    model_instance: Optional[Model],
    insert=False,
) -> Expression:
    """
    Takes a BaserowExpression and converts it to a Django Expression which calculates
    the result of the expression when run on the provided model_instance or for the
    entire table when a model_instance is not provided.

    More specifically, when a model_instance is provided all field() references will
    be replaced by the values of those fields on the model_instance. If a model_instance
    is not provided instead these field references will be replaced by F() column
    references. When doing an create operation you will need to provide a model_instance
    as you cannot reference a column for a row that does not yet exist. Instead the
    initial defaults will be found and substituted in.

    :param baserow_expression: The BaserowExpression to convert.
    :param model: The Django model that the expression is being generated for.
    :param model_instance: If provided the expression will calculate the result for
        this single instance. If not provided then the expression will use F() column
        references and will calculate the result for every row in the table.
    :param insert: Must be set to True if the resulting expression will be used in
        a SQL INSERT statement. Will ensure any aggregate / lookup expressions are
        replaced with None as they cannot be calculated in an INSERT.
    :return: A Django Expression which can be used in a create operation when a
        model_instance is provided or an update operation when one is not provided.
    """

    try:
        if isinstance(baserow_expression.expression_type, BaserowFormulaInvalidType):
            return Value(None)
        else:
            # When inserting a row we can't possibly calculate the aggregate result
            # as there is no row id that can be used to connect it to other tables.
            inserting_aggregate = (
                baserow_expression.aggregate and model_instance is not None and insert
            )
            if inserting_aggregate:
                return Value(None)
            else:
                generator = BaserowExpressionToDjangoExpressionGenerator(
                    model, model_instance
                )
                return baserow_expression.accept(generator)
    except RecursionError as e:
        print(e)
        raise MaximumFormulaSizeError()
    except Exception as e:
        formula_exception_handler(e)
        return Value(None)


def _get_model_field_for_type(expression_type):
    (
        field_instance,
        baserow_field_type,
    ) = expression_type.get_baserow_field_instance_and_type()
    model_field = baserow_field_type.get_model_field(field_instance)
    return model_field


class BaserowExpressionToDjangoExpressionGenerator(
    BaserowFormulaASTVisitor[BaserowFormulaType, Expression]
):
    """
    Visits a BaserowExpression replacing it with the equivalent Django Expression.

    If a model_instance is provided then any field references will be replaced with
    direct Value() expressions of those fields on that model_instance. If one is not
    provided then instead a F() expression will be used to reference that field.
    """

    def __init__(
        self,
        model: Type[Model],
        model_instance: Optional[Model],
    ):
        self.model_instance = model_instance
        self.model = model

    def visit_lookup_reference(
        self, lookup_reference: BaserowLookupReference[BaserowFormulaType]
    ):
        raise Exception("Should never happen")

    def visit_field_reference(
        self, field_reference: BaserowFieldReference[BaserowFormulaType]
    ):
        raise Exception("Should never happen")

    def visit_function_call(
        self, function_call: BaserowFunctionCall[BaserowFormulaType]
    ) -> Expression:
        function_call.pending_joins = []
        if function_call.function_def.convert_args_to_expressions:
            args = [expr.accept(self) for expr in function_call.args]
        else:
            args = []
        for e in function_call.args:
            function_call.pending_joins += e.pending_joins
        expr = function_call.to_django_expression_given_args(
            args,
            self.model,
            self.model_instance,
        )
        return expr

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral[BaserowFormulaType]
    ) -> Expression:
        # We need to cast and be super explicit this is a text field so postgres
        # does not get angry and claim this is an unknown type.
        return Cast(
            Value(string_literal.literal, output_field=fields.TextField()),
            output_field=fields.TextField(),
        )

    def visit_int_literal(self, int_literal: BaserowIntegerLiteral[BaserowFormulaType]):
        return Value(
            int_literal.literal,
            output_field=DecimalField(max_digits=50, decimal_places=0),
        )

    def visit_decimal_literal(self, decimal_literal: BaserowDecimalLiteral):
        return Value(
            decimal_literal.literal,
            output_field=DecimalField(
                max_digits=50, decimal_places=decimal_literal.num_decimal_places()
            ),
        )

    def visit_boolean_literal(self, boolean_literal: BaserowBooleanLiteral):
        return Value(boolean_literal.literal, output_field=BooleanField())
