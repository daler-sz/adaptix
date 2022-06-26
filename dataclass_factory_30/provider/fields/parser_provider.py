from typing import Dict, Any

from .basic_gen import (
    CodeGenHookRequest, stub_code_gen_hook,
    CodeGenHook, CodeGenHookData, DirectFieldsCollectorMixin, strip_figure, NameSanitizer
)
from .crown_definitions import (
    InputNameMappingRequest, InputNameMapping,
    InpCrown,
    InpDictCrown, ExtraCollect, InpListCrown, InpFieldCrown, InpNoneCrown
)
from .input_creation_gen import BuiltinInputCreationGen
from ...code_tools import BasicClosureCompiler, CodeBuilder, ContextNamespace
from ...common import Parser
from ...provider.essential import Mediator, CannotProvide
from ...provider.fields.definitions import (
    InputFigureRequest, InputExtractionImageRequest, InputFigure, InputExtractionImage, InputCreationImageRequest,
    InputCreationGen, InputExtractionGen, VarBinder, InputCreationImage,
)
from ...provider.fields.input_extraction_gen import BuiltinInputExtractionGen
from ...provider.provider_template import ParserProvider
from ...provider.request_cls import ParserRequest, ParserFieldRequest
from ...provider.static_provider import StaticProvider, static_provision_action


class BuiltinInputExtractionImageProvider(StaticProvider, DirectFieldsCollectorMixin):
    @static_provision_action(InputExtractionImageRequest)
    def _provide_extraction_image(
        self, mediator: Mediator, request: InputExtractionImageRequest,
    ) -> InputExtractionImage:
        name_mapping = mediator.provide(
            InputNameMappingRequest(
                type=request.initial_request.type,
                figure=request.figure,
            )
        )

        extraction_gen = self._create_extraction_gen(request, name_mapping)

        if self._has_collect_policy(name_mapping.crown) and request.figure.extra is None:
            raise CannotProvide(
                "Cannot create parser that collect extra data"
                " if InputFigure does not take extra data"
            )

        used_direct_fields = self._collect_used_direct_fields(name_mapping.crown)
        skipped_direct_fields = [
            field.name for field in request.figure.fields
            if field.name not in used_direct_fields
        ]

        return InputExtractionImage(
            extraction_gen=extraction_gen,
            skipped_fields=skipped_direct_fields + list(name_mapping.skipped_extra_targets),
        )

    def _create_extraction_gen(
        self,
        request: InputExtractionImageRequest,
        name_mapping: InputNameMapping,
    ) -> InputExtractionGen:
        return BuiltinInputExtractionGen(
            figure=request.figure,
            crown=name_mapping.crown,
            debug_path=request.initial_request.debug_path,
            strict_coercion=request.initial_request.strict_coercion,
        )

    def _has_collect_policy(self, crown: InpCrown) -> bool:
        if isinstance(crown, InpDictCrown):
            return crown.extra == ExtraCollect() or any(
                self._has_collect_policy(sub_crown)
                for sub_crown in crown.map.values()
            )
        if isinstance(crown, InpListCrown):
            return any(
                self._has_collect_policy(sub_crown)
                for sub_crown in crown.map
            )
        if isinstance(crown, (InpFieldCrown, InpNoneCrown)):
            return False
        raise TypeError


class BuiltinInputCreationImageProvider(StaticProvider):
    @static_provision_action(InputCreationImageRequest)
    def _provide_extraction_image(self, mediator: Mediator, request: InputCreationImageRequest) -> InputCreationImage:
        return InputCreationImage(
            creation_gen=BuiltinInputCreationGen(
                figure=request.figure,
            )
        )


class FieldsParserProvider(ParserProvider):
    def __init__(self, name_sanitizer: NameSanitizer):
        self._name_sanitizer = name_sanitizer

    def _process_figure(self, figure: InputFigure, extraction_image: InputExtractionImage) -> InputFigure:
        skipped_required_fields = [
            field.name
            for field in figure.fields
            if field.is_required and field.name in extraction_image.skipped_fields
        ]

        if skipped_required_fields:
            raise ValueError(
                f"Required fields {skipped_required_fields} are skipped"
            )

        return strip_figure(figure, extraction_image)

    def _provide_parser(self, mediator: Mediator, request: ParserRequest) -> Parser:
        figure: InputFigure = mediator.provide(
            InputFigureRequest(type=request.type)
        )

        extraction_image = mediator.provide(
            InputExtractionImageRequest(
                figure=figure,
                initial_request=request,
            )
        )

        processed_figure = self._process_figure(figure, extraction_image)

        creation_image = mediator.provide(
            InputCreationImageRequest(
                figure=processed_figure,
                initial_request=request,
            )
        )

        try:
            code_gen_hook = mediator.provide(CodeGenHookRequest(initial_request=request))
        except CannotProvide:
            code_gen_hook = stub_code_gen_hook

        field_parsers = {
            field.name: mediator.provide(
                ParserFieldRequest(
                    type=field.type,
                    strict_coercion=request.strict_coercion,
                    debug_path=request.debug_path,
                    default=field.default,
                    is_required=field.is_required,
                    metadata=field.metadata,
                    name=field.name,
                    param_kind=field.param_kind,
                )
            )
            for field in processed_figure.fields
        }

        return self._make_parser(
            request=request,
            creation_gen=creation_image.creation_gen,
            extraction_gen=extraction_image.extraction_gen,
            fields_parsers=field_parsers,
            code_gen_hook=code_gen_hook,
        )

    def _get_closure_name(self, request: ParserRequest) -> str:
        tp = request.type
        if isinstance(tp, type):
            name = tp.__name__
        else:
            name = str(tp)

        s_name = self._name_sanitizer.sanitize(name)
        if s_name != "":
            s_name = "_" + s_name
        return "fields_parser" + s_name

    def _get_file_name(self, request: ParserRequest) -> str:
        return self._get_closure_name(request)

    def _get_compiler(self):
        return BasicClosureCompiler()

    def _get_binder(self):
        return VarBinder()

    def _make_parser(
        self,
        request: ParserRequest,
        fields_parsers: Dict[str, Parser],
        creation_gen: InputCreationGen,
        extraction_gen: InputExtractionGen,
        code_gen_hook: CodeGenHook,
    ) -> Parser:
        compiler = self._get_compiler()
        binder = self._get_binder()

        namespace_dict: Dict[str, Any] = {}
        ctx_namespace = ContextNamespace(namespace_dict)

        extraction_code_builder = extraction_gen.generate_input_extraction(binder, ctx_namespace, fields_parsers)
        creation_code_builder = creation_gen.generate_input_creation(binder, ctx_namespace)

        closure_name = self._get_closure_name(request)
        file_name = self._get_file_name(request)

        builder = CodeBuilder()

        global_namespace_dict = {}
        for name, value in namespace_dict.items():
            global_name = f"g_{name}"
            global_namespace_dict[global_name] = value
            builder += f"{name} = {global_name}"

        builder.empty_line()

        with builder(f"def {closure_name}({binder.data}):"):
            builder.extend(extraction_code_builder)
            builder.extend(creation_code_builder)

        builder += f"return {closure_name}"

        code_gen_hook(
            CodeGenHookData(
                namespace=global_namespace_dict,
                source=builder.string(),
            )
        )

        return compiler.compile(
            builder,
            file_name,
            global_namespace_dict,
        )
