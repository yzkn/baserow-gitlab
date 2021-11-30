import abc
from typing import Optional, List, Type, Tuple, Any, Dict

from django.db.models import Expression, Model

from baserow.contrib.database.formula.ast.tree import (
    ArgCountSpecifier,
    BaserowFunctionCall,
    BaserowExpression,
)
from baserow.contrib.database.formula.types import formula_type
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaValidType,
    UnTyped,
    BaserowFormulaType,
)
from baserow.contrib.database.formula.types.type_checker import (
    SingleArgumentTypeChecker,
    BaserowArgumentTypeChecker,
)
from baserow.core.registry import Instance


class BaserowFunctionDefinition(Instance, abc.ABC):
    """
    A registrable instance which defines a function for use in the Baserow Formula
    language. You most likely want to instead work with one of the simpler to use
    abstract sub classes of this class, depending on how many arguments your function
    takes:
    - OneArgumentBaserowFunction
    - TwoArgumentBaserowFunction
    - ThreeArgumentBaserowFunction
    """

    @property
    @abc.abstractmethod
    def type(self) -> str:
        """
        :return: The unique name case insensitive name for this function. Users will
            call this function using the name defined here.
        """

        pass

    @property
    def aggregate(self) -> bool:
        """
        :return: If this function is an aggregate one which collapses a many expression
            down to a single value.
        """

        return False

    @property
    def internal(self) -> bool:
        """
        :return: If this function should never be directly callable/usable by a user
            but instead only for use by the internal Baserow typing system.
        """

        return False

    @property
    def operator(self) -> Optional[str]:
        """
        :return: If this function definition is used by an operator return the operators
             text representation here.
        """

        return None

    @property
    @abc.abstractmethod
    def num_args(self) -> ArgCountSpecifier:
        """
        :return: An ArgCountSpecifier which defines how many arguments this function
            supports.
        """

        pass

    @property
    @abc.abstractmethod
    def arg_types(self) -> BaserowArgumentTypeChecker:
        """
        :return: An argument type checker which checks all arguments provided to this
            function have valid types.
        """

        pass

    @property
    def requires_refresh_after_insert(self) -> bool:
        """
        :return: True if by using this function to have it's value calculated properly
            a row must first be inserted and then refreshed.
        """

        return False

    @property
    def convert_args_to_expressions(self) -> bool:
        """
        TODO
        """

        return True

    @property
    def wrapper(self) -> bool:
        """
        TODO
        """

        return False

    @property
    def many(self) -> bool:
        """
        TODO
        """

        return False

    @abc.abstractmethod
    def type_function_given_valid_args(
        self,
        args: List[BaserowExpression[BaserowFormulaValidType]],
        expression: BaserowFunctionCall[UnTyped],
    ) -> BaserowExpression[BaserowFormulaType]:
        """
        Given a list of arguments extracted from the function call expression, already
        typed and checked by the self.arg_types property should calculate and return
        a typed BaserowExpression for this function.

        :param args: The typed and valid arguments taken from expression.
        :param expression: A func call expression for this function type which is
            untyped.
        :return: A typed and possibly transformed or changed BaserowExpression for this
            function call.
        """

        pass

    def prepare_func_call(self, func_call, args, **kwargs) -> Dict[str, Any]:
        return kwargs

    @abc.abstractmethod
    def to_django_expression_given_args(
        self,
        args: List[Expression],
        model: Type[Model],
        model_instance: Optional[Model],
        function_call: "BaserowFunctionCall",
    ) -> Expression:
        """
        Given the args already converted to Django Expressions should return a Django
        Expression which calculates the result of a call to this function.

        Will only be called if all the args have passed the type check and the function
        itself was typed with a BaserowValidType.

        :param model: The model the expression is being generated for.
        :param args: The already converted to Django expression args.
        :param model_instance: If set then the model instance which is being inserted
            or if False then the django expression is for an update statement.
        :param function_call: The function call.
        :return: A Django Expression which calculates the result of this function.
        """

        pass

    def type_function_given_typed_args(
        self,
        typed_args: "List[BaserowExpression[formula_type.BaserowFormulaType]]",
        expression: "BaserowFunctionCall[formula_type.UnTyped]",
    ) -> "BaserowExpression[formula_type.BaserowFormulaType]":
        """
        Given the already typed arguments for a func_call to a function of this
        definition this function will check the type of each argument against the
        arg_types property. If they all pass the type check then the user implemented
        type_function_given_valid_args will be called. If they don't a
        BaserowInvalidType will be returned containing a relavent error message.

        :param typed_args: The typed but not checked argument BaserowExpressions.
        :param expression: The func_call expression which contains the typed_args but
            is not yet typed as we first need to type and check the args.
        :return: A fully typed and possibly transformed BaserowExpression which
            implements a call to this function.
        """

        # noinspection PyTypeChecker
        valid_args: List[
            BaserowExpression[formula_type.BaserowFormulaValidType]
        ] = list()
        invalid_results: List[Tuple[int, formula_type.BaserowFormulaInvalidType]] = []
        for i, typed_arg in enumerate(typed_args):
            arg_type = typed_arg.expression_type

            if isinstance(arg_type, formula_type.BaserowFormulaInvalidType):
                invalid_results.append((i, arg_type))
            else:
                checked_typed_arg = expression.check_arg_type_valid(
                    i, typed_arg, typed_args
                )
                if isinstance(
                    checked_typed_arg.expression_type,
                    formula_type.BaserowFormulaInvalidType,
                ):
                    invalid_results.append((i, checked_typed_arg.expression_type))
                else:
                    # Must be a valid type but the intellij type checker isn't so smart
                    # noinspection PyTypeChecker
                    valid_args.append(checked_typed_arg)
        if len(invalid_results) > 0:
            message = ", ".join([t.error for _, t in invalid_results])
            return expression.with_invalid_type(message)
        else:
            return self.type_function_given_valid_args(valid_args, expression)

    def call_and_type_with_args(
        self,
        args: "List[BaserowExpression[formula_type.BaserowFormulaType]]",
    ) -> "BaserowFunctionCall[formula_type.BaserowFormulaType]":
        func_call = BaserowFunctionCall[formula_type.UnTyped](self, args, None)
        return func_call.type_function_given_typed_args(args)

    def check_arg_type_valid(
        self,
        arg_index: int,
        typed_arg: "BaserowExpression[formula_type.BaserowFormulaType]",
        all_typed_args: "List[BaserowExpression[formula_type.BaserowFormulaType]]",
    ) -> "BaserowExpression[formula_type.BaserowFormulaType]":
        """
        Checks if the typed argument at arg_index is a valid type using the
        self.arg_types type checker.

        :param arg_index: The 0 based index for this argument.
        :param typed_arg: The already typed but not checked argument expression.
        :param all_typed_args: All other typed but not checked arguments for this
            function call.
        :return: The updated typed expression for this argument (the same type if it
            passes the check, an invalid type if it does not pass).
        """

        if callable(self.arg_types):
            arg_types_for_this_arg = self.arg_types(
                arg_index, [t.expression_type for t in all_typed_args]
            )
        else:
            arg_types_for_this_arg = self.arg_types[arg_index]

        expression_type = typed_arg.expression_type
        valid_type_names = []
        for valid_arg_type in arg_types_for_this_arg:
            if isinstance(valid_arg_type, SingleArgumentTypeChecker):
                if valid_arg_type.check(expression_type):
                    return typed_arg
                else:
                    valid_type_names.append(
                        valid_arg_type.invalid_message(expression_type)
                    )
            elif isinstance(expression_type, valid_arg_type):
                return typed_arg
            else:
                valid_type_names.append(valid_arg_type.type)

        expression_type_name = expression_type.type
        if len(valid_type_names) == 1:
            postfix = f"the only usable type for this argument is {valid_type_names[0]}"
        elif len(valid_type_names) == 0:
            postfix = f"there are no possible types usable here"
        else:
            postfix = (
                f"the only usable types for this argument are "
                f"{','.join(valid_type_names)}"
            )

        return typed_arg.with_invalid_type(
            f"argument number {arg_index+1} given to {self} was of type "
            f"{expression_type_name} but {postfix}"
        )

    def _wrap_aggregate_with_subquery(self, expr):
        if self.aggregate and not self.type == "subquery":
            from baserow.contrib.database.formula.registries import (
                formula_function_registry,
            )

            subquery_def = formula_function_registry.get("subquery")
            subquery_call = subquery_def.call_and_type_with_args([expr])
            return subquery_call
        else:
            return expr

    def __str__(self):
        if self.operator is None:
            return "function " + self.type
        else:
            return "operator " + self.operator

    def __eq__(self, other):
        if type(other) is type(self):
            return self.type == other.type
        else:
            return False

    def __hash__(self):
        return hash(self.type)

    def to_django_expression(self, function_call, self1):
        pass
