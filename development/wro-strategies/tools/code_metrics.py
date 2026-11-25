#!/usr/bin/env python3
"""Size of a set of Python files: lines of code, total complexity, most complex function.

    python3 tools/code_metrics.py src/robotek_obstacle/robotek_obstacle/*.py

Same method before and after the Obstacle v2 (docs/obstacle-reimpl-plan.md §9): no comments,
no docstrings; complexity counts `if`, `for`, `while`, comprehensions, `except`, `IfExp` and
each `and`/`or`. The "most complex" value is the largest function score in the set.
"""
import ast
import sys


def complexity(fn):
    n = 1
    for x in ast.walk(fn):
        if isinstance(x, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.comprehension, ast.IfExp)):
            n += 1
        elif isinstance(x, ast.BoolOp):
            n += len(x.values) - 1
    return n


def metrics(paths):
    lines = total = worst = 0
    per_file = []
    for path in paths:
        src = open(path).read()
        tree = ast.parse(src)
        docs = set()
        for x in ast.walk(tree):
            if isinstance(x, (ast.Module, ast.ClassDef, ast.FunctionDef)) and x.body \
                    and isinstance(x.body[0], ast.Expr) \
                    and isinstance(getattr(x.body[0], 'value', None), ast.Constant) \
                    and isinstance(x.body[0].value.value, str):
                docs.update(range(x.body[0].lineno, x.body[0].end_lineno + 1))
        file_lines = sum(1 for i, line in enumerate(src.split('\n'), 1)
                         if line.strip() and not line.strip().startswith('#') and i not in docs)
        values = [complexity(x) for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]
        file_total = sum(values)
        file_worst = max(values or [0])
        per_file.append((path, file_lines, file_total, file_worst))
        lines += file_lines
        total += file_total
        worst = max(worst, file_worst)
    return lines, total, worst, per_file


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    lines, total, worst, per_file = metrics(sys.argv[1:])
    for path, n, c, w in per_file:
        print(f'{n:6d} {c:6d} {w:5d}  {path}')
    print(f'{lines:6d} {total:6d} {worst:5d}  TOTAL ({len(per_file)} files)')


if __name__ == '__main__':
    main()
