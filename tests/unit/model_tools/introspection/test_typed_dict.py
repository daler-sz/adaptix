import typing
from types import MappingProxyType
from typing import TypedDict

from adaptix._internal.feature_requirement import HAS_ANNOTATED, HAS_PY_39
from adaptix._internal.model_tools.definitions import (
    InputField,
    InputShape,
    NoDefault,
    OutputField,
    OutputShape,
    ParamKind,
    Shape,
    create_key_accessor,
)
from adaptix._internal.model_tools.introspection import get_typed_dict_shape
from tests_helpers import requires


class Foo(TypedDict, total=True):
    a: int
    b: str
    c: 'bool'


class Bar(TypedDict, total=False):
    a: int
    b: str
    c: 'bool'


def test_total():
    assert (
        get_typed_dict_shape(Foo)
        ==
        Shape(
            input=InputShape(
                constructor=Foo,
                kwargs=None,
                fields=(
                    InputField(
                        type=int,
                        id='a',
                        default=NoDefault(),
                        is_required=True,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='a',
                    ),
                    InputField(
                        type=str,
                        id='b',
                        default=NoDefault(),
                        is_required=True,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='b',
                    ),
                    InputField(
                        type=bool,
                        id='c',
                        default=NoDefault(),
                        is_required=True,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='c',
                    ),
                ),
                overriden_types=frozenset({'a', 'b', 'c'}),
            ),
            output=OutputShape(
                fields=(
                    OutputField(
                        type=int,
                        id='a',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('a', access_error=None),
                    ),
                    OutputField(
                        type=str,
                        id='b',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('b', access_error=None),
                    ),
                    OutputField(
                        type=bool,
                        id='c',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('c', access_error=None),
                    ),
                ),
                overriden_types=frozenset({'a', 'b', 'c'}),
            ),
        )
    )


def test_non_total():
    assert (
        get_typed_dict_shape(Bar)
        ==
        Shape(
            input=InputShape(
                constructor=Bar,
                kwargs=None,
                fields=(
                    InputField(
                        type=int,
                        id='a',
                        default=NoDefault(),
                        is_required=False,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='a',
                    ),
                    InputField(
                        type=str,
                        id='b',
                        default=NoDefault(),
                        is_required=False,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='b',
                    ),
                    InputField(
                        type=bool,
                        id='c',
                        default=NoDefault(),
                        is_required=False,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='c',
                    ),
                ),
                overriden_types=frozenset({'a', 'b', 'c'}),
            ),
            output=OutputShape(
                fields=(
                    OutputField(
                        type=int,
                        id='a',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('a', access_error=KeyError),
                    ),
                    OutputField(
                        type=str,
                        id='b',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('b', access_error=KeyError),
                    ),
                    OutputField(
                        type=bool,
                        id='c',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('c', access_error=KeyError),
                    ),
                ),
                overriden_types=frozenset({'a', 'b', 'c'}),
            ),
        )
    )


class ParentNotTotal(TypedDict, total=False):
    x: int


class ChildTotal(ParentNotTotal, total=True):
    y: str


class GrandChildNotTotal(ChildTotal, total=False):
    z: str


def _negate_if_not_py39(value: bool) -> bool:
    return value if HAS_PY_39 else not value


def test_inheritance_first():
    assert (
        get_typed_dict_shape(ParentNotTotal)
        ==
        Shape(
            input=InputShape(
                constructor=ParentNotTotal,
                kwargs=None,
                fields=(
                    InputField(
                        type=int,
                        id='x',
                        default=NoDefault(),
                        is_required=False,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='x',
                    ),
                ),
                overriden_types=frozenset({'x'}),
            ),
            output=OutputShape(
                fields=(
                    OutputField(
                        type=int,
                        id='x',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('x', access_error=KeyError),
                    ),
                ),
                overriden_types=frozenset({'x'}),
            ),
        )
    )


def test_inheritance_second():
    assert (
        get_typed_dict_shape(ChildTotal)
        ==
        Shape(
            input=InputShape(
                constructor=ChildTotal,
                kwargs=None,
                fields=(
                    InputField(
                        type=int,
                        id='x',
                        default=NoDefault(),
                        is_required=_negate_if_not_py39(False),
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='x',
                    ),
                    InputField(
                        type=str,
                        id='y',
                        default=NoDefault(),
                        is_required=True,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='y',
                    ),
                ),
                overriden_types=frozenset({'x', 'y'}),
            ),
            output=OutputShape(
                fields=(
                    OutputField(
                        type=int,
                        id='x',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('x', access_error=KeyError if HAS_PY_39 else None),
                    ),
                    OutputField(
                        type=str,
                        id='y',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('y', access_error=None),
                    ),
                ),
                overriden_types=frozenset({'x', 'y'}),
            )
        )
    )


def test_inheritance_third():
    assert (
        get_typed_dict_shape(GrandChildNotTotal)
        ==
        Shape(
            input=InputShape(
                constructor=GrandChildNotTotal,
                kwargs=None,
                fields=(
                    InputField(
                        type=int,
                        id='x',
                        default=NoDefault(),
                        is_required=False,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='x',
                    ),
                    InputField(
                        type=str,
                        id='y',
                        default=NoDefault(),
                        is_required=_negate_if_not_py39(True),
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='y',
                    ),
                    InputField(
                        type=str,
                        id='z',
                        default=NoDefault(),
                        is_required=False,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='z',
                    ),
                ),
                overriden_types=frozenset({'x', 'y', 'z'}),
            ),
            output=OutputShape(
                fields=(
                    OutputField(
                        type=int,
                        id='x',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('x', access_error=KeyError),
                    ),
                    OutputField(
                        type=str,
                        id='y',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('y', access_error=None if HAS_PY_39 else KeyError),
                    ),
                    OutputField(
                        type=str,
                        id='z',
                        default=NoDefault(),
                        metadata=MappingProxyType({}),
                        accessor=create_key_accessor('z', access_error=KeyError),
                    ),
                ),
                overriden_types=frozenset({'x', 'y', 'z'}),
            )
        )
    )


@requires(HAS_ANNOTATED)
def test_annotated():
    class WithAnnotatedTotal(TypedDict):
        annotated_field: typing.Annotated[int, 'metadata']

    assert (
        get_typed_dict_shape(WithAnnotatedTotal)
        ==
        Shape(
            input=InputShape(
                constructor=WithAnnotatedTotal,
                kwargs=None,
                fields=(
                    InputField(
                        type=typing.Annotated[int, 'metadata'],
                        id='annotated_field',
                        default=NoDefault(),
                        is_required=True,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='annotated_field',
                    ),
                ),
                overriden_types=frozenset({'annotated_field'}),
            ),
            output=OutputShape(
                fields=(
                    OutputField(
                        type=typing.Annotated[int, 'metadata'],
                        id='annotated_field',
                        default=NoDefault(),
                        accessor=create_key_accessor('annotated_field', access_error=None),
                        metadata=MappingProxyType({}),
                    ),
                ),
                overriden_types=frozenset({'annotated_field'}),
            )
        )
    )

    class WithAnnotatedNotTotal(TypedDict, total=False):
        annotated_field: typing.Annotated[int, 'metadata']

    assert (
        get_typed_dict_shape(WithAnnotatedNotTotal)
        ==
        Shape(
            input=InputShape(
                constructor=WithAnnotatedNotTotal,
                kwargs=None,
                fields=(
                    InputField(
                        type=typing.Annotated[int, 'metadata'],
                        id='annotated_field',
                        default=NoDefault(),
                        is_required=False,
                        metadata=MappingProxyType({}),
                        param_kind=ParamKind.KW_ONLY,
                        param_name='annotated_field',
                    ),
                ),
                overriden_types=frozenset({'annotated_field'}),
            ),
            output=OutputShape(
                fields=(
                    OutputField(
                        type=typing.Annotated[int, 'metadata'],
                        id='annotated_field',
                        default=NoDefault(),
                        accessor=create_key_accessor('annotated_field', access_error=KeyError),
                        metadata=MappingProxyType({}),
                    ),
                ),
                overriden_types=frozenset({'annotated_field'}),
            )
        )
    )