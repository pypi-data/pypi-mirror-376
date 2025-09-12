from itertools import product
from typing import Any
from typing import TypeVar

import pytest

from ccu.fancyplots.validation import Validator
from ccu.fancyplots.validation import no_validation_validator
from ccu.fancyplots.validation import type_hint_to_validator


@pytest.fixture(name="value", params=["1", 0, None, (1, 0)])
def fixture_value(request: pytest.FixtureRequest) -> Any:
    value: Any = request.param
    return value


class TestNoValidationValidator:
    @staticmethod
    def test_should_return_value(value: Any) -> None:
        assert no_validation_validator(value, False) == value


@pytest.fixture(name="valid_value")
def fixture_valid_value(value: Any) -> Any:
    return value


@pytest.fixture(name="validated_value")
def fixture_validated_value(valid_value: Any, type_hint: type) -> Any:
    if type_hint is bool:
        return str(valid_value).lower() == "true"
    return valid_value if type_hint is Any else type_hint(valid_value)


@pytest.fixture(name="type_hint")
def fixture_type_hint() -> Any:
    return Any


@pytest.fixture(name="validator")
def fixture_validator(type_hint: type) -> Validator[Any]:
    return type_hint_to_validator(type_hint, "")


class TestValidation:
    @staticmethod
    def test_should_return_true_for_valid_values_with_no_validation(
        valid_value: Any, validator: Validator[Any]
    ) -> None:
        assert validator(valid_value, validate_only=True)

    @staticmethod
    def test_should_return_valid_values_with_no_validation(
        valid_value: Any, validator: Validator[Any], validated_value: Any
    ) -> None:
        assert validator(valid_value, validate_only=False) == validated_value

    @staticmethod
    @pytest.mark.parametrize(
        ("valid_value", "type_hint"), [(x, str) for x in ("1", "", "Value")]
    )
    def test_should_return_true_for_valid_strings(
        valid_value: Any, validator: Validator[Any]
    ) -> None:
        assert validator(valid_value, validate_only=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("valid_value", "type_hint"), [(x, str) for x in ("1", "", "Value")]
    )
    def test_should_return_valid_strings(
        valid_value: Any, validator: Validator[Any], validated_value: Any
    ) -> None:
        assert validator(valid_value, validate_only=False) == validated_value

    @staticmethod
    @pytest.mark.parametrize(
        ("valid_value", "type_hint"),
        product(("1", "-1", "0"), [int, float]),
    )
    def test_should_return_true_for_valid_numbers(
        valid_value: Any, validator: Validator[Any]
    ) -> None:
        assert validator(valid_value, validate_only=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("valid_value", "type_hint"),
        product(("1", "-1", "0"), [int, float]),
    )
    def test_should_return_valid_numbers(
        valid_value: Any, validator: Validator[Any], validated_value: Any
    ) -> None:
        assert validator(valid_value, validate_only=False) == validated_value

    @staticmethod
    @pytest.mark.parametrize(
        ("valid_value", "type_hint"),
        product(("True", "False"), [bool]),
    )
    def test_should_return_true_for_valid_booleans(
        valid_value: Any, validator: Validator[Any]
    ) -> None:
        assert validator(valid_value, validate_only=True)

    @staticmethod
    @pytest.mark.parametrize(
        ("valid_value", "type_hint"),
        product(("True", "False"), [bool]),
    )
    def test_should_return_valid_booleans(
        valid_value: Any, validator: Validator[Any], validated_value: Any
    ) -> None:
        assert validator(valid_value, validate_only=False) == validated_value


_T = TypeVar("_T", list, tuple)


class TestSequenceValidation:
    @staticmethod
    @pytest.fixture(name="valid_value", params=("1,2", "1"))
    def fixture_valid_value(request: pytest.FixtureRequest) -> Any:
        return request.param

    @staticmethod
    @pytest.fixture(name="sequence_type", params=(tuple, list))
    def fixture_sequence_type(request: pytest.FixtureRequest) -> Any:
        return request.param

    @staticmethod
    @pytest.fixture(name="element_type", params=(float, int))
    def fixture_element_type(request: pytest.FixtureRequest) -> Any:
        return request.param

    @staticmethod
    @pytest.fixture(name="type_hint")
    def fixture_type_hint(element_type: type, sequence_type: type[_T]) -> _T:
        return sequence_type[element_type, ...]

    @staticmethod
    @pytest.fixture(name="validated_value")
    def fixture_validated_value(
        element_type: type,
        sequence_type: type[_T],
        valid_value: Any,
    ) -> _T:
        return sequence_type(element_type(x) for x in valid_value.split(","))

    @staticmethod
    def test_should_return_true_for_valid_sequence(
        valid_value: Any, validator: Validator[Any]
    ) -> None:
        assert validator(valid_value, validate_only=True)

    @staticmethod
    def test_should_return_valid_sequence(
        valid_value: Any, validator: Validator[Any], validated_value: Any
    ) -> None:
        assert validator(valid_value, validate_only=False) == validated_value


class TestUnionValidationSimple:
    @staticmethod
    @pytest.mark.parametrize(
        "type_hint",
        [
            (int | str),
            (int | None),
            (int | tuple[str]),
            (int | tuple[float]),
            (int | tuple[int]),
            (int | float),
            (None | int),
        ],
    )
    def test_should_valid_int_in_union(validator: Validator[Any]) -> None:
        valid_value = "1"
        validated_value = 1
        assert validator(valid_value, validate_only=False) == validated_value

    @staticmethod
    @pytest.mark.parametrize(
        "type_hint",
        [
            (float | str),
            (float | None),
            (float | tuple[str]),
            (float | tuple[float]),
            (float | tuple[int]),
            (float | int),
            (None | float),
        ],
    )
    def test_should_valid_float_in_union(validator: Validator[Any]) -> None:
        valid_value = "1"
        validated_value = 1.0
        assert validator(valid_value, validate_only=False) == validated_value

    @staticmethod
    @pytest.mark.parametrize(
        "type_hint",
        [
            (str | int),
            (str | float),
            (str | None),
            (str | tuple[str]),
            (str | tuple[float]),
            (str | tuple[int]),
            (None | str),
        ],
    )
    def test_should_valid_string_in_union(validator: Validator[Any]) -> None:
        valid_value = "1"
        validated_value = "1"
        assert validator(valid_value, validate_only=False) == validated_value

    @staticmethod
    @pytest.mark.parametrize(
        "type_hint",
        [
            (tuple[float] | int),
            (tuple[float] | float),
            (tuple[float] | str),
            (tuple[float] | None),
            (None | tuple[float]),
        ],
    )
    def test_should_valid_tuple_of_floats_in_union(
        validator: Validator[Any],
    ) -> None:
        valid_value = "1"
        validated_value = (1.0,)
        assert validator(valid_value, validate_only=False) == validated_value

    @staticmethod
    @pytest.mark.parametrize(
        "type_hint",
        [
            (None | str),
            (None | tuple[str]),
            (None | tuple[float]),
            (None | tuple[int]),
            (None | int),
            (None | float),
            (float | None),
            (int | None),
        ],
    )
    def test_should_valid_none_in_union(validator: Validator[Any]) -> None:
        valid_value = ""
        validated_value = None
        assert validator(valid_value, validate_only=False) == validated_value
