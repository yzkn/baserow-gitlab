import abc
from decimal import Decimal
from typing import List, TypeVar, Generic, Optional, Type

from django.conf import settings
from django.db.models import Expression, Model

from baserow.contrib.database.formula.ast import visitors
from baserow.contrib.database.formula.ast.exceptions import (
    InvalidStringLiteralProvided,
    TooLargeStringLiteralProvided,
    InvalidIntLiteralProvided,
)
from baserow.contrib.database.formula.parser.parser import (
    convert_string_to_string_literal_token,
)
from baserow.contrib.database.formula.types import formula_type

A = TypeVar("A")
T = TypeVar("T")
R = TypeVar("R")


class PendingJoin:
    def __init__(self, join_path, join_table):
        self.join_table = join_table
        self.join_path = join_path

    def get_unique_annotation_name(self):
        unique_annotation_path_name = f"not_trashed_{self.join_path}".replace("__", "_")
        return unique_annotation_path_name

    def __str__(self) -> str:
        return f"pending_join({self.join_path}, {self.join_table})"


class BaserowExpression(abc.ABC, Generic[A]):
    """
    The root base class for a BaserowExpression which can be seen as an abstract
    syntax tree of a Baserow Formula.

    For example the formula `concat(field('a'),1+1)` is equivalently represented by the
    following BaserowExpression AST:

    ```
    BaserowFunctionCall(
        BaserowConcat(),
        [
            BaserowFieldReference('a'),
            BaserowFunctionCall(
                BaserowAdd(),
                [
                    BaserowIntegerLiteral(1),
                    BaserowIntegerLiteral(1)
                ]
            )
        ]
    )
    ```

    A BaserowExpression has a generic type parameter A. This indicates the type of
    the additional field `expression_type` attached to every BaserowExpression.
    This allows us to talk about BaserowExpression's as they go through the various
    stages of parsing and typing using the python type system to help us.

    For example, imagine I parse a raw input string and have yet to figure out the types
    of a baserow expression. Then the type of the `expression_type` attached to each
    node in the BaserowExpression tree is None as we don't know it yet. And so we can
    write for the formula `concat('a', 'b')`:


    ```
    # Look at what UnTyped is defined as (its `type(None)`)!
    untyped_expr = BaserowFunctionCall[UnTyped](
        BaserowConcat(),
        [
            BaserowStringLiteral[UnTyped]('a'),
            BaserowStringLiteral[UnTyped]('b')
        ]
    )
    ```

    Pythons type system will now help us as we have used a generic type here and if
    we try to do something with `untyped_expr.expression_type` we will get a nice type
    warning that it is None.

    Now imagine we go through and figure out the types, now we can use the various
    with_type functions defined below to transform an expression into a different
    generically typed form!

    ```
    untyped_expr = BaserowFunctionCall[UnTyped](
        BaserowConcat(),
        [
            BaserowStringLiteral[UnTyped]('a').with_valid_type(
                BaserowFormulaTextType()
            ),
            BaserowStringLiteral[UnTyped]('b').with_valid_type(
                BaserowFormulaTextType()
            )
        ]
    )
    typed_expression = untyped_expr.with_valid_type(BaserowFormulaTextType())
    # Now python knows that typed_expression is of type
    # BaserowExpression[BaserowFormulaType] and so we can safely access it:
    do_thing_with_type(typed_expression.expression_type)
    ```
    """

    def __init__(
        self,
        expression_type: A,
        aggregate=False,
        many=False,
        pending_aggregate_filter=False,
        pending_joins: List[PendingJoin] = None,
        wrapper=False,
        parent: Optional["BaserowExpression"] = None,
    ):
        self.expression_type: A = expression_type
        self.aggregate = aggregate
        self.many = many
        self.pending_aggregate_filter = pending_aggregate_filter
        if pending_joins is None:
            pending_joins = []
        self.pending_joins = pending_joins
        self.wrapper = wrapper
        self.parent = parent

    @abc.abstractmethod
    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        pass

    def with_type(self, expression_type: "R") -> "BaserowExpression[R]":
        self.expression_type = expression_type
        return self

    def with_valid_type(
        self, expression_type: "formula_type.BaserowFormulaValidType"
    ) -> "BaserowExpression[formula_type.BaserowFormulaValidType]":
        return self.with_type(expression_type)

    def with_invalid_type(
        self, error: str
    ) -> "BaserowExpression[formula_type.BaserowFormulaInvalidType]":
        return self.with_type(formula_type.BaserowFormulaInvalidType(error))

    def get_last_parent_join(self):
        if self.parent and self.parent.pending_joins:
            return self.parent.pending_joins[-1]
        else:
            return None

    def get_parent_join_prefix(self):
        last_join = self.get_last_parent_join()
        if last_join:
            return last_join.get_unique_annotation_name() + "__"
        else:
            return ""


class BaserowStringLiteral(BaserowExpression[A]):
    """
    Represents a string literal typed directly into the formula.
    """

    def __init__(self, literal: str, expression_type: A):
        super().__init__(expression_type)

        if not isinstance(literal, str):
            raise InvalidStringLiteralProvided()
        if len(literal) > settings.MAX_FORMULA_STRING_LENGTH:
            raise TooLargeStringLiteralProvided()
        self.literal = literal

    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        return visitor.visit_string_literal(self)

    def __str__(self):
        return convert_string_to_string_literal_token(self.literal, True)


class BaserowIntegerLiteral(BaserowExpression[A]):
    """
    Represents a literal integer typed into the formula.
    """

    def __init__(self, literal: int, expression_type: A):
        super().__init__(expression_type)

        if not isinstance(literal, int):
            raise InvalidIntLiteralProvided()
        self.literal = literal

    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        return visitor.visit_int_literal(self)

    def __str__(self):
        return str(self.literal)


class BaserowDecimalLiteral(BaserowExpression[A]):
    """
    Represents a literal decimal typed into the formula.
    """

    def __init__(self, literal: Decimal, expression_type: A):
        super().__init__(expression_type)
        self.literal = literal

    def num_decimal_places(self):
        return -self.literal.as_tuple().exponent

    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        return visitor.visit_decimal_literal(self)

    def __str__(self):
        return str(self.literal)


class BaserowBooleanLiteral(BaserowExpression[A]):
    """
    Represents a literal boolean typed into the formula.
    """

    def __init__(self, literal: bool, expression_type: A):
        super().__init__(expression_type)
        self.literal = literal

    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        return visitor.visit_boolean_literal(self)

    def __str__(self):
        return "true" if self.literal else "false"


class BaserowFieldReference(BaserowExpression[A]):
    """
    Represents a reference to a field with the same name as the referenced_field_name.
    """

    def __init__(
        self,
        referenced_field_name: str,
        expression_type: A,
    ):
        super().__init__(expression_type)
        self.referenced_field_name = referenced_field_name

    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        return visitor.visit_field_reference(self)

    def __str__(self):
        escaped_name = convert_string_to_string_literal_token(
            self.referenced_field_name, True
        )
        return f"field({escaped_name})"


class BaserowLookupReference(BaserowExpression[A]):
    def __init__(
        self,
        through_field: str,
        target_field: str,
        expression_type: A,
    ):
        super().__init__(
            expression_type,
        )
        self.through_field = through_field
        self.target_field = target_field

    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        return visitor.visit_lookup_reference(self)

    def __str__(self):
        return f"lookup({self.through_field},{self.target_field})"


class ArgCountSpecifier(abc.ABC):
    """
    A base class defining a checker which returns if the number of arguments given to
    a function is correct or not.
    """

    def __init__(self, count):
        self.count = count

    @abc.abstractmethod
    def test(self, num_args: int):
        """
        Should return if the provided num_args matches this ArgCountSpecifier.
        For example if you were extending this class to create a ArgCountSpecifier that
        required the num_args to be less than a fixed number, then here you would check
        return num_args < fixed_number.
        :param num_args: The number of args being provided.
        :return: Whether or not the number of args meets this specification.
        """

        pass

    @abc.abstractmethod
    def __str__(self):
        """
        Should be implemented to explain how to meet this specification in a human
        readable string format.
        """

        pass


class BaserowFunctionCall(BaserowExpression[A]):
    """
    Represents a function call with arguments to the function defined by function_def.
    """

    def __init__(
        self,
        func_def,
        args: List[BaserowExpression[A]],
        expression_type: A,
        pending_aggregate_filter=False,
        pending_joins=None,
    ):
        if pending_joins is None:
            pending_joins = []
        many = False
        aggregate = False
        for a in args:
            pending_joins += a.pending_joins
            many = many or a.many
            aggregate = aggregate or a.aggregate
            a.parent = self
        many = many or func_def.many
        super().__init__(
            expression_type,
            many=many,
            aggregate=aggregate,
            pending_aggregate_filter=pending_aggregate_filter,
            pending_joins=pending_joins,
            wrapper=func_def.wrapper,
        )

        self.function_def = func_def
        self.args = args

    def accept(self, visitor: "visitors.BaserowFormulaASTVisitor[A, T]") -> T:
        return visitor.visit_function_call(self)

    def type_function_given_typed_args(
        self,
        args: "List[BaserowExpression[formula_type.BaserowFormulaType]]",
    ) -> "BaserowExpression[formula_type.BaserowFormulaType]":
        return self.function_def.type_function_given_typed_args(
            args, self.with_args(args)
        )

    def type_function_given_valid_args(
        self,
        args: "List[BaserowExpression[formula_type.BaserowFormulaValidType]]",
    ) -> "BaserowExpression[formula_type.BaserowFormulaType]":
        return self.function_def.type_function_given_valid_args(
            args, self.with_args(args)
        )

    def to_django_expression_given_args(
        self,
        args: List[Expression],
        model: Type[Model],
        model_instance: Optional[Model],
    ) -> Expression:
        return self.function_def.to_django_expression_given_args(
            args, model, model_instance, self
        )

    def check_arg_type_valid(
        self,
        i: int,
        typed_arg: "BaserowExpression[formula_type.BaserowFormulaType]",
        all_typed_args: "List[BaserowExpression[formula_type.BaserowFormulaType]]",
    ) -> "BaserowExpression[formula_type.BaserowFormulaType]":
        return self.function_def.check_arg_type_valid(i, typed_arg, all_typed_args)

    def with_args(self, new_args) -> "BaserowFunctionCall[A]":
        """
        :param new_args: The arguments to use in the newly constructed function call.
        :return: A new BaserowFunctionCall to the same function_def but with replaced
            arguments.
        """

        return BaserowFunctionCall(
            self.function_def,
            new_args,
            self.expression_type,
            pending_aggregate_filter=self.pending_aggregate_filter,
            pending_joins=self.pending_joins,
        )

    def with_pending_joins(self, pending_joins) -> "BaserowFunctionCall[A]":
        """
        :param pending_joins: The pending_joins to use in the new function call.
        :return: A new BaserowFunctionCall to the same function_def but with replaced
            pending_joins.
        """

        return BaserowFunctionCall(
            self.function_def,
            self.args,
            self.expression_type,
            pending_aggregate_filter=self.pending_aggregate_filter,
            pending_joins=pending_joins,
        )

    def with_pending_aggregate_filter(
        self, pending_aggregate_filter
    ) -> "BaserowFunctionCall[A]":
        return BaserowFunctionCall(
            self.function_def,
            self.args,
            self.expression_type,
            pending_aggregate_filter=pending_aggregate_filter,
            pending_joins=self.pending_joins,
        )

    def __str__(self):
        args_string = ",".join([str(a) for a in self.args])
        return f"{self.function_def.type}({args_string})"
