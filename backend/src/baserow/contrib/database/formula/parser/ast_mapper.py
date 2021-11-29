from decimal import Decimal

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
from baserow.contrib.database.formula.parser.exceptions import (
    InvalidNumberOfArguments,
    BaserowFormulaSyntaxError,
    UnknownOperator,
    FieldByIdReferencesAreDeprecated,
    MaximumFormulaSizeError,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormula import (
    BaserowFormula,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormulaVisitor import (
    BaserowFormulaVisitor,
)
from baserow.contrib.database.formula.parser.parser import (
    convert_string_literal_token_to_string,
    get_parse_tree_for_formula,
)
from baserow.contrib.database.formula.registries import formula_function_registry
from baserow.contrib.database.formula.types.formula_type import UnTyped
from baserow.core.exceptions import InstanceTypeDoesNotExist


def raw_formula_to_untyped_expression(
    formula: str, allow_internal_functions=False
) -> BaserowExpression[UnTyped]:
    """
    Takes a raw user input string, syntax checks it to see if it matches the syntax of
    a Baserow Formula (raises a BaserowFormulaSyntaxError if not) and converts it into
    an untyped BaserowExpression.

    :param formula: A raw user supplied string possibly in the format of a Baserow
        Formula.
    :param allow_internal_functions: Whether the input formula is from a trusted source
        and can be allowed to use internal functions or not.
    :return: An untyped BaserowExpression which represents the provided raw formula.
    :raises BaserowFormulaSyntaxError: If the supplied formula is not in the syntax
        of the Baserow Formula language.
    """

    try:
        tree = get_parse_tree_for_formula(formula)
        return BaserowFormulaToBaserowASTMapper(allow_internal_functions).visit(tree)
    except RecursionError:
        raise MaximumFormulaSizeError()


def _invalid_function_error(function_name):
    return BaserowFormulaSyntaxError(f"{function_name} is not a valid function")


class BaserowFormulaToBaserowASTMapper(BaserowFormulaVisitor):
    """
    A Visitor which transforms an Antlr parse tree into a BaserowExpression AST.

    Raises an UnknownBinaryOperator if the formula contains an unknown binary operator.

    Raises an UnknownFunctionDefinition if the formula has a function call to a function
    not in the registry.
    """

    def __init__(self, allow_internal_functions=False) -> None:
        self.allow_internal_functions = allow_internal_functions

    def visitRoot(self, ctx: BaserowFormula.RootContext):
        return ctx.expr().accept(self)

    def visitStringLiteral(self, ctx: BaserowFormula.StringLiteralContext):
        # noinspection PyTypeChecker
        literal = self.process_string(ctx)
        return BaserowStringLiteral(literal, None)

    def visitDecimalLiteral(self, ctx: BaserowFormula.DecimalLiteralContext):
        return BaserowDecimalLiteral(Decimal(ctx.getText()), None)

    def visitBooleanLiteral(self, ctx: BaserowFormula.BooleanLiteralContext):
        return BaserowBooleanLiteral(ctx.TRUE() is not None, None)

    def visitBrackets(self, ctx: BaserowFormula.BracketsContext):
        return ctx.expr().accept(self)

    def process_string(self, ctx):
        literal_without_outer_quotes = ctx.getText()[1:-1]
        if ctx.SINGLEQ_STRING_LITERAL() is not None:
            literal = literal_without_outer_quotes.replace("\\'", "'")
        else:
            literal = literal_without_outer_quotes.replace('\\"', '"')
        return literal

    def visitFunctionCall(self, ctx: BaserowFormula.FunctionCallContext):
        function_name = ctx.func_name().accept(self).lower()
        function_argument_expressions = ctx.expr()

        return self._do_func(function_argument_expressions, function_name)

    def _do_func(self, function_argument_expressions, function_name):
        function_def = self._get_function_def(function_name)
        self._check_function_call_valid(function_argument_expressions, function_def)
        args = [expr.accept(self) for expr in function_argument_expressions]
        return BaserowFunctionCall[UnTyped](function_def, args, None)

    def visitBinaryOp(self, ctx: BaserowFormula.BinaryOpContext):
        if ctx.PLUS():
            op = "add"
        elif ctx.MINUS():
            op = "minus"
        elif ctx.SLASH():
            op = "divide"
        elif ctx.EQUAL():
            op = "equal"
        elif ctx.BANG_EQUAL():
            op = "not_equal"
        elif ctx.STAR():
            op = "multiply"
        elif ctx.GT():
            op = "greater_than"
        elif ctx.LT():
            op = "less_than"
        elif ctx.GTE():
            op = "greater_than_or_equal"
        elif ctx.LTE():
            op = "less_than_or_equal"
        else:
            raise UnknownOperator(ctx.getText())

        return self._do_func(ctx.expr(), op)

    @staticmethod
    def _check_function_call_valid(function_argument_expressions, function_def):
        num_expressions = len(function_argument_expressions)
        if not function_def.num_args.test(num_expressions):
            raise InvalidNumberOfArguments(function_def, num_expressions)

    def _get_function_def(self, function_name):
        try:
            function_def = formula_function_registry.get(function_name)
        except InstanceTypeDoesNotExist:
            raise _invalid_function_error(function_name)

        if function_def.internal and not self.allow_internal_functions:
            raise _invalid_function_error(function_name)
        return function_def

    def visitFunc_name(self, ctx: BaserowFormula.Func_nameContext):
        return ctx.getText()

    def visitIdentifier(self, ctx: BaserowFormula.IdentifierContext):
        return ctx.getText()

    def visitIntegerLiteral(self, ctx: BaserowFormula.IntegerLiteralContext):
        return BaserowIntegerLiteral[UnTyped](int(ctx.getText()), None)

    def visitFieldReference(self, ctx: BaserowFormula.FieldReferenceContext):
        reference = ctx.field_reference()
        field_name = convert_string_literal_token_to_string(
            reference.getText(), reference.SINGLEQ_STRING_LITERAL()
        )
        return BaserowFieldReference[UnTyped](field_name, None)

    def visitLookupFieldReference(
        self, ctx: BaserowFormula.LookupFieldReferenceContext
    ):
        reference = ctx.field_reference(0)
        through_field = convert_string_literal_token_to_string(
            reference.getText(), reference.SINGLEQ_STRING_LITERAL()
        )
        lookup = ctx.field_reference(1)
        target_field = convert_string_literal_token_to_string(
            lookup.getText(), reference.SINGLEQ_STRING_LITERAL()
        )
        return BaserowLookupReference[UnTyped](through_field, target_field, None)

    def visitFieldByIdReference(self, ctx: BaserowFormula.FieldByIdReferenceContext):
        raise FieldByIdReferencesAreDeprecated()

    def visitLeftWhitespaceOrComments(
        self, ctx: BaserowFormula.LeftWhitespaceOrCommentsContext
    ):
        return ctx.expr().accept(self)

    def visitRightWhitespaceOrComments(
        self, ctx: BaserowFormula.RightWhitespaceOrCommentsContext
    ):
        return ctx.expr().accept(self)
