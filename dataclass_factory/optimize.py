import ast
import inspect
import textwrap
from copy import copy
from typing import Any

VAR_NAME = "______"


class RewriteName(ast.NodeTransformer):
    def __init__(self, kwargs):
        self.kwargs = kwargs

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        node.decorator_list = []  # remove decorators because they will be applied later
        self.generic_visit(node)
        return node

    def visit_If(self, node):
        try:
            m = ast.Module(
                body=[ast.Assign(
                    targets=[
                        ast.Name(VAR_NAME, ctx=ast.Store(), lineno=1, col_offset=0)
                    ],
                    value=node.test,
                    lineno=1, col_offset=0
                )],
                type_ignores=[],
            )
            code = compile(m, filename='dataclass_factory/stub.py', mode='exec')
            namespace = copy(self.kwargs)
            exec(code, namespace)
            res = namespace[VAR_NAME]
            if not res:
                return None
            else:
                self.generic_visit(node.body)
                return node.body
        except Exception as e:
            self.generic_visit(node)
            return node


def cut_if(locals, globals):
    def dec(func):
        freevars = func.__code__.co_freevars
        known_vars = {k: v for k, v in locals.items() if k in freevars}
        known_vars.update(globals)

        text = inspect.getsource(func)
        text = "\n" * (func.__code__.co_firstlineno - 1) + textwrap.dedent(text)
        tree = ast.parse(text)

        new_tree = RewriteName(known_vars).visit(tree)
        code = compile(new_tree, filename=inspect.getfile(func), mode='exec')
        namespace = copy(known_vars)
        exec(code, namespace)
        return namespace[func.__name__]

    return dec
