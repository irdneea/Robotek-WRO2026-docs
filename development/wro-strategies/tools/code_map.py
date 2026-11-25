#!/usr/bin/env python3
"""One line per class and function (line, signature, first docstring line): read this before
opening a source file, then open only the lines you need (Read with offset/limit, or sed -n).

    python3 tools/code_map.py src/robotek_obstacle/robotek_obstacle/v2/*.py
    python3 tools/code_map.py src/robotek_obstacle/robotek_obstacle/v2/mission.py --constants
"""
import argparse
import ast


def _signature(node):
    args = [a.arg for a in node.args.args if a.arg not in ('self', 'cls')]
    if node.args.vararg:
        args.append('*' + node.args.vararg.arg)
    return f"{node.name}({', '.join(args)})"


def _doc(node):
    doc = ast.get_docstring(node)
    return doc.strip().split('\n')[0] if doc else ''


def entries(tree, depth=0):
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            yield node.lineno, depth, f'class {node.name}', _doc(node)
            yield from entries(node, depth + 1)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.lineno, depth, _signature(node), _doc(node)


def constants(tree, source):
    lines = source.split('\n')
    for node in tree.body:
        if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) and t.id.isupper() for t in node.targets):
            yield node.lineno, lines[node.lineno - 1].strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('files', nargs='+')
    parser.add_argument('--constants', action='store_true', help='also list module constants with their comment')
    args = parser.parse_args()
    for path in args.files:
        source = open(path).read()
        tree = ast.parse(source)
        print(f"{path} ({source.count(chr(10))} lines): {_doc(tree)}")
        if args.constants:
            for line, text in constants(tree, source):
                print(f'  {line:4d}  {text[:110]}')
        for line, depth, name, doc in entries(tree):
            print(f"  {line:4d}  {'  ' * depth}{name}" + (f' - {doc[:90]}' if doc else ''))


if __name__ == '__main__':
    main()
