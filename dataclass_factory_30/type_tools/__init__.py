from .basic_utils import (
    create_union,
    is_annotated,
    is_named_tuple_class,
    is_new_type,
    is_protocol,
    is_subclass_soft,
    is_typed_dict_class,
    is_user_defined_generic,
    strip_alias
)
from .norm_utils import is_generic, strip_tags
from .normalize_type import BaseNormType, NormTV, NormType, normalize_type
