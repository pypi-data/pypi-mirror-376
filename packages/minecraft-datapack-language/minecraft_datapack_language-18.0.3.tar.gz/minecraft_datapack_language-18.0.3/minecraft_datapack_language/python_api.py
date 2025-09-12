from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Union

from .ast_nodes import (
    Program,
    PackDeclaration,
    NamespaceDeclaration,
    TagDeclaration,
    VariableDeclaration,
    VariableAssignment,
    VariableSubstitution,
    FunctionDeclaration,
    FunctionCall,
    IfStatement,
    WhileLoop,
    RawBlock,
    SayCommand,
    BinaryExpression,
    LiteralExpression,
)
from .mdl_compiler import MDLCompiler


# ---------- Expression helpers ----------

def num(value: Union[int, float]) -> LiteralExpression:
    return LiteralExpression(value=value, type="number")


def var_read(name: str, scope: str) -> VariableSubstitution:
    # scope must look like <@s>, <@a>, <@e[...]>, or <global>
    return VariableSubstitution(name=name, scope=scope)


def binop(left, operator: str, right) -> BinaryExpression:
    # operator one of: PLUS, MINUS, MULTIPLY, DIVIDE, GREATER, LESS, GREATER_EQUAL, LESS_EQUAL, EQUAL, NOT_EQUAL
    return BinaryExpression(left=left, operator=operator, right=right)


# ---------- Python Bindings ----------


class Pack:
    def __init__(self, name: str, description: str = "", pack_format: int = 82):
        self._pack = PackDeclaration(name=name, description=description, pack_format=pack_format)
        self._namespaces: List[Namespace] = []
        self._variables: List[VariableDeclaration] = []
        self._tags: List[TagDeclaration] = []
        self._hooks: List = []  # HookDeclaration built by Namespace

    def namespace(self, name: str) -> "Namespace":
        ns = Namespace(self, name)
        self._namespaces.append(ns)
        return ns

    # Lifecycle hooks reference functions by id "ns:name"
    def on_load(self, function_id: str, scope: Optional[str] = None):
        # defer to Namespace to create HookDeclaration during build
        self._hooks.append(("on_load", function_id, scope))

    def on_tick(self, function_id: str, scope: Optional[str] = None):
        self._hooks.append(("on_tick", function_id, scope))

    def tag(self, registry: str, name: str, values: Optional[List[str]] = None, replace: bool = False):
        values = values or []
        # For namespace item tags, store values in file_path for compiler to consume
        file_path = name
        if registry == "item" and values:
            file_path = "values=" + ",".join(values)
        self._tags.append(TagDeclaration(tag_type=registry, name=name, file_path=file_path))

    def declare_var(self, name: str, scope: str, initial_value: Union[int, float]) -> None:
        self._variables.append(
            VariableDeclaration(var_type="num", name=name, scope=scope, initial_value=num(initial_value))
        )

    def build(self, output_dir: str):
        # Build Program AST
        namespace_nodes: List[NamespaceDeclaration] = []
        function_nodes: List[FunctionDeclaration] = []
        hook_nodes: List = []

        # Namespaces and functions
        for ns in self._namespaces:
            namespace_nodes.append(NamespaceDeclaration(name=ns.name))
            function_nodes.extend(ns._functions)
            hook_nodes.extend(ns._hooks)

        # Hooks added via Pack-level convenience
        for hook_type, function_id, scope in self._hooks:
            ns_name, fn_name = function_id.split(":", 1)
            from .ast_nodes import HookDeclaration

            hook_nodes.append(
                HookDeclaration(hook_type=hook_type, namespace=ns_name, name=fn_name, scope=scope)
            )

        # Determine default namespace if none explicitly added
        default_namespace = None
        if namespace_nodes:
            default_namespace = namespace_nodes[0]
        elif self._tags:
            # Derive from first tag name if namespaced (e.g., test:swords)
            first = self._tags[0].name
            if ":" in first:
                default_namespace = NamespaceDeclaration(name=first.split(":",1)[0])
            else:
                default_namespace = NamespaceDeclaration(name="mdl")

        program = Program(
            pack=self._pack,
            namespace=default_namespace,
            tags=self._tags,
            variables=self._variables,
            functions=function_nodes,
            hooks=hook_nodes,
            statements=[],
        )

        MDLCompiler(output_dir).compile(program, output_dir)


class Namespace:
    def __init__(self, pack: Pack, name: str):
        self._pack = pack
        self.name = name
        self._functions: List[FunctionDeclaration] = []
        self._hooks: List = []

    def function(self, name: str, *commands_or_builder: Union[str, Callable["FunctionBuilder"], None]):
        # Case 1: builder callable - use FunctionBuilder API directly
        if len(commands_or_builder) == 1 and callable(commands_or_builder[0]):
            builder = FunctionBuilder(self._pack, self, name)
            commands_or_builder[0](builder)
            func_node = FunctionDeclaration(namespace=self.name, name=name, scope=None, body=builder._body)
            self._functions.append(func_node)
            return func_node

        # Case 2: string-based function body - try parsing as MDL source to build real AST
        body_lines: List[str] = []
        for cmd in commands_or_builder:
            if isinstance(cmd, str):
                body_lines.append(cmd)

        if body_lines:
            try:
                from .mdl_parser import MDLParser
                pack_decl = self._pack._pack

                # Heuristic: attempt MDL parse only if there are control structures or var declarations
                looks_like_mdl = any(
                    l.strip().startswith(("var ", "if ", "while ", "on_load", "on_tick")) or
                    l.strip().endswith("{") or l.strip() == "}" or "$" in l
                    for l in body_lines
                )
                if looks_like_mdl:
                    normalized: List[str] = []
                    for line in body_lines:
                        s = line.strip()
                        if not s:
                            continue
                        if s.startswith("say "):
                            msg = s[len("say ") :].strip()
                            if not (msg.startswith('"') and msg.endswith('"')):
                                msg = f'"{msg}"'
                            normalized.append(f"say {msg};")
                        elif s.startswith("exec "):
                            if not s.endswith(";"):
                                s = s + ";"
                            normalized.append(s)
                        elif s.startswith("var "):
                            if not s.endswith(";"):
                                s = s + ";"
                            normalized.append(s)
                        elif s.endswith("{") or s == "}" or s.endswith("}"):
                            normalized.append(s)
                        else:
                            # Heuristic: detect assignment like name<scope> = expr
                            try:
                                import re as _re
                                if _re.match(r'^[A-Za-z_][A-Za-z0-9_]*(<[^>]+>)?\s*=\s*', s):
                                    if not s.endswith(";"):
                                        s = s + ";"
                                    normalized.append(s)
                                else:
                                    # Unknown command; wrap as single-line raw so parser accepts it
                                    normalized.append(f"$!raw {s} raw!$")
                            except Exception:
                                normalized.append(f"$!raw {s} raw!$")

                    src_lines = [
                        f'pack "{pack_decl.name}" "{pack_decl.description}" {pack_decl.pack_format};',
                        f'namespace "{self.name}";',
                        f'function {self.name}:{name} {{'
                    ]
                    src_lines.extend(normalized)
                    src_lines.append('}')
                    source = "\n".join(src_lines)
                    parser = MDLParser("<python_api>")
                    ast = parser.parse(source)
                    if ast.variables:
                        self._pack._variables.extend(ast.variables)
                    if ast.tags:
                        self._pack._tags.extend(ast.tags)
                    if ast.hooks:
                        self._pack._hooks.extend([(h.hook_type, f"{h.namespace}:{h.name}", h.scope) for h in ast.hooks])
                    if ast.functions:
                        fn = ast.functions[0]
                        self._functions.append(fn)
                        return fn
            except Exception:
                pass

        # Fallback: interpret simple strings
        builder = FunctionBuilder(self._pack, self, name)
        for cmd in body_lines:
            stripped = cmd.strip().rstrip(";")
            if stripped.startswith("say "):
                msg = stripped[len("say ") :].strip()
                if msg.startswith('"') and msg.endswith('"'):
                    msg = msg[1:-1]
                builder.say(msg)
            elif stripped.startswith("exec "):
                target = stripped[len("exec ") :].strip()
                scope = None
                if "<" in target and target.endswith(">"):
                    scope = target[target.index("<") :]
                    target = target[: target.index("<")]
                builder.exec(target, scope)
            else:
                builder.raw(cmd)

        func_node = FunctionDeclaration(namespace=self.name, name=name, scope=None, body=builder._body)
        self._functions.append(func_node)
        return func_node

    # Convenience forwarding
    def on_load(self, function_id: str, scope: Optional[str] = None):
        from .ast_nodes import HookDeclaration

        ns_name, fn_name = function_id.split(":", 1)
        self._hooks.append(HookDeclaration(hook_type="on_load", namespace=ns_name, name=fn_name, scope=scope))

    def on_tick(self, function_id: str, scope: Optional[str] = None):
        from .ast_nodes import HookDeclaration

        ns_name, fn_name = function_id.split(":", 1)
        self._hooks.append(HookDeclaration(hook_type="on_tick", namespace=ns_name, name=fn_name, scope=scope))


class FunctionBuilder:
    def __init__(self, pack: Pack, namespace: Namespace, function_name: str):
        self._pack = pack
        self._namespace = namespace
        self._name = function_name
        self._body: List = []

    # Basics
    def say(self, message: str):
        self._body.append(SayCommand(message=message, variables=[]))

    def raw(self, content: str):
        self._body.append(RawBlock(content=content.rstrip(";")))

    def exec(self, function_id: str, scope: Optional[str] = None):
        ns, fn = function_id.split(":", 1)
        self._body.append(FunctionCall(namespace=ns, name=fn, scope=scope))

    # Variables
    def declare_var(self, name: str, scope: str, initial_value: Union[int, float]):
        self._pack.declare_var(name, scope, initial_value)
        # Also set to initial value in this function
        self.set(name, scope, num(initial_value))

    def set(self, name: str, scope: str, value_expr) -> None:
        self._body.append(VariableAssignment(name=name, scope=scope, value=value_expr))

    # Control flow
    def if_(self, condition_expr, then_builder: Callable[["FunctionBuilder"], None], else_builder: Optional[Callable[["FunctionBuilder"], None]] = None):
        then_fb = FunctionBuilder(self._pack, self._namespace, self._name)
        then_builder(then_fb)
        else_body = None
        if else_builder:
            else_fb = FunctionBuilder(self._pack, self._namespace, self._name)
            else_builder(else_fb)
            else_body = else_fb._body
        self._body.append(IfStatement(condition=condition_expr, then_body=then_fb._body, else_body=else_body))

    def while_(self, condition_expr, body_builder: Callable[["FunctionBuilder"], None]):
        body_fb = FunctionBuilder(self._pack, self._namespace, self._name)
        body_builder(body_fb)
        self._body.append(WhileLoop(condition=condition_expr, body=body_fb._body))


