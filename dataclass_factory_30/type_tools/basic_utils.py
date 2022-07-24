# pylint: disable=import-outside-toplevel
import types
from typing import Generic, Iterable, TypedDict, Union, get_origin

from ..common import TypeHint

TYPED_DICT_MCS = type(types.new_class("_TypedDictSample", (TypedDict,), {}))


def strip_alias(type_hint: TypeHint) -> TypeHint:
    origin = get_origin(type_hint)
    return type_hint if origin is None else origin


def is_subclass_soft(cls, classinfo) -> bool:
    """Acts like builtin issubclass,
     but returns False instead of rising TypeError
    """
    try:
        return issubclass(cls, classinfo)
    except TypeError:
        return False


def has_attrs(obj, attrs: Iterable[str]) -> bool:
    return all(
        hasattr(obj, attr_name)
        for attr_name in attrs
    )


def is_new_type(tp) -> bool:
    return has_attrs(tp, ['__supertype__', '__name__'])


def is_annotated(tp) -> bool:
    return has_attrs(tp, ['__metadata__', '__origin__'])


def is_typed_dict_class(tp) -> bool:
    return isinstance(tp, TYPED_DICT_MCS)


NAMED_TUPLE_METHODS = ('_fields', '_field_defaults', '_make', '_replace', '_asdict')


def is_named_tuple_class(tp) -> bool:
    return (
        is_subclass_soft(tp, tuple)
        and
        has_attrs(tp, NAMED_TUPLE_METHODS)
    )


def is_user_defined_generic(tp) -> bool:
    return (
        hasattr(tp, '__parameters__')
        and tp.__parameters__
        and is_subclass_soft(strip_alias(tp), Generic)  # throw away builtin generics
    )


def is_protocol(tp):
    from typing import Protocol

    if not isinstance(tp, type):
        return False

    return Protocol in tp.__bases__


def create_union(args: tuple):
    # pylint: disable=unnecessary-dunder-call
    return Union.__getitem__(args)