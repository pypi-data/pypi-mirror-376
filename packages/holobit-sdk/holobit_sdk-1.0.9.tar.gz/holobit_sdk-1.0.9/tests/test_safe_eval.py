import pytest

from holobit_sdk.utils.safe_eval import UnsafeExpression, safe_eval


def test_calls_are_blocked_by_default():
    with pytest.raises(UnsafeExpression):
        safe_eval("min(1, 2)", {"min": min})


def test_allowed_functions_can_be_called():
    assert safe_eval("min(1, 2)", {"min": min}, allowed_funcs={min}) == 1


def test_property_access_is_blocked():
    class WithProperty:
        @property
        def secret(self):  # pragma: no cover - simple descriptor
            return 42

    with pytest.raises(UnsafeExpression):
        safe_eval("obj.secret", {"obj": WithProperty()})


def test_descriptor_access_is_blocked():
    class Descriptor:
        def __get__(self, instance, owner):  # pragma: no cover - simple descriptor
            return 42

    class WithDescriptor:
        d = Descriptor()

    with pytest.raises(UnsafeExpression):
        safe_eval("obj.d", {"obj": WithDescriptor()})


def test_expression_too_long():
    expr = "1" * 11
    with pytest.raises(UnsafeExpression):
        safe_eval(expr, {}, max_length=10)


def test_expression_too_deep():
    expr = "+" * 6 + "1"
    with pytest.raises(UnsafeExpression):
        safe_eval(expr, {}, max_depth=5)
