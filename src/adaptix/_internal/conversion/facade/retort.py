from inspect import Signature
from typing import Any, Callable, Iterable, Optional, TypeVar

from ...provider.essential import Provider
from ...provider.loc_stack_filtering import P
from ...provider.shape_provider import BUILTIN_SHAPE_PROVIDER
from ...retort.operating_retort import OperatingRetort
from ..binding_provider import SameNameBindingProvider
from ..coercer_provider import DstAnyCoercerProvider, SameTypeCoercerProvider, SubclassCoercerProvider
from ..converter_provider import BuiltinConverterProvider
from ..request_cls import ConverterRequest
from .provider import forbid_unbound_optional


class FilledConverterRetort(OperatingRetort):
    recipe = [
        BUILTIN_SHAPE_PROVIDER,

        BuiltinConverterProvider(),

        SameNameBindingProvider(is_default=True),

        SameTypeCoercerProvider(),
        DstAnyCoercerProvider(),
        SubclassCoercerProvider(),

        forbid_unbound_optional(P.ANY),
    ]


AR = TypeVar('AR', bound='AdornedConverterRetort')


class AdornedConverterRetort(OperatingRetort):
    def extend(self: AR, *, recipe: Iterable[Provider]) -> AR:
        # pylint: disable=protected-access
        with self._clone() as clone:
            clone._inc_instance_recipe = (
                tuple(recipe) + clone._inc_instance_recipe
            )

        return clone

    def produce_converter(
        self,
        signature: Signature,
        stub_function: Optional[Callable],
        function_name: Optional[str],
    ) -> Callable[..., Any]:
        return self._facade_provide(
            ConverterRequest(
                signature=signature,
                function_name=function_name,
                stub_function=stub_function,
            ),
            error_message=f'Cannot produce converter for {signature!r}',
        )


class ConverterRetort(FilledConverterRetort, AdornedConverterRetort):
    pass
