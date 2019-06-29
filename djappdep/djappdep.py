"""Find and display dependencies between files in our project.
Standard library imports and  3rd party library imports are ignored.
"""

import argparse
import json
import logging
import os
import re
from typing import (
    Dict,
    Optional,
)

DIR_BLACKLIST = [
    '__pycache__',
    '.git',
    '.idea',
    'env',
    'migrations',
]

IMPORT_PATTERN = re.compile(r'^(from ([.\w]+) )?import ([.*\w]+).*')
GRANULARITY_PATTERN = r'((\w+)\.?)'


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


def _parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--maxdepth',
        '-d',
        type=int,
        default=1,
        help='Dependency granularity. e.g:\n'
             '1 -> app: [dependencies]\n'
             '2 -> app.submodule: [dependencies]\n'
             '3 -> app.submodule.file: [dependencies]')

    parser.add_argument(
        '-allow_internal',
        action='store_true',
        default=False,
        help='If set, imports within an app/module will be displayed')

    parser.add_argument(
        '-all',
        '-a',
        action='store_true',
        default=False,
        help='Maximum granularity, equivalent to --maxdepth=1000')

    parser.add_argument(
        '-ignore_tests',
        '-t',
        action='store_true',
        default=False,
        help='If set, remove imports that only appear in test modules.')

    parser.add_argument(
        '-debug',
        action='store_true',
        default=False,
        help='Enable debug log output.')

    args = parser.parse_args()
    if args.all:
        args.maxdepth = 1000
    if args.debug:
        log.setLevel(logging.DEBUG)

    return args


def _traverse_dict(obj: Dict, callback):
    pending_keys = []
    for key, value in obj.items():
        pending_keys.append(key)
        if isinstance(value, dict):
            _traverse_dict(value)

    for key in pending_keys:
        callback(obj, key)


def _read_file_imports(file, dependency_map: Dict):
    """Add an entry in `dependency_map` using its dotted path as the key.
    The entry value is a list of dotted paths representing everything
    that was imported in that file.
    """
    dotted_filepath = _convert_path_filesystem_to_python(file)
    dependency_map[dotted_filepath] = []

    with open(file, 'r') as f:
        for line in f.readlines():
            imported = _read_import_line(line, dotted_filepath)
            if imported:
                dependency_map[dotted_filepath].append(imported)


def _read_import_line(line: str, dotted_filepath: str) -> Optional[str]:
    def local_to_abs(local):
        return f'{dotted_filepath}{local}'

    match = re.match(IMPORT_PATTERN, line)
    if match:
        imported_from = match.group(2) or ''
        if imported_from:
            if imported_from[0] == r'.':
                imported_from = local_to_abs(imported_from)
            imported_from = f'{imported_from}.'

        imported = match.group(3)
        if imported[0] == r'.':
            imported = local_to_abs(imported)

        result = f'{imported_from}{imported}'
        log.debug(f'{dotted_filepath} -> {result}')
        return result
    else:
        if line.startswith('import') or line.startswith('from'):
            log.debug(f'MISSED IMPORT: {line}')


def _convert_path_filesystem_to_python(absolute_path, cwd=os.getcwd()):
    """Convert Windows or *nix filepath to dotted.path."""
    dotted_path = os.path.relpath(absolute_path, cwd)
    dotted_path = re.sub(r'[(\\\\)/]', r'.', dotted_path)
    dotted_path = re.sub(r'\.py$', '', dotted_path)
    return dotted_path


def _read_imports(rootdir, dependency_map: Dict):
    for cwd, dirs, files in os.walk(rootdir):
        for d in dirs:
            if d in DIR_BLACKLIST:
                dirs.remove(d)
                continue

        if '__init__.py' not in files:
            # Not a python package
            continue

        for f in files:
            if os.path.splitext(f)[1] == '.py':
                path = os.path.join(cwd, f)
                _read_file_imports(path, dependency_map)


def _remove_empty_imports(dependency_map):
    def _del(obj, key):
        if not obj[key]:
            del obj[key]

    _traverse_dict(dependency_map, _del)


def _remove_external_imports(dependency_map):
    """Trim any imports that are not defined in the project. We are not
    interested in standard library packages or 3rd party libraries for our
    purposes."""

    internal_imports = dependency_map.keys()

    for key, value in dependency_map.items():
        dependency_map[key] = [x for x in value if x in internal_imports]


def _remove_tests(dependency_map: Dict):
    removals = []
    for key in dependency_map:
        if re.match(r'.*(tests\.|_test|test_).*', key):
            removals.append(key)

    for key in removals:
        del dependency_map[key]


def _set_granularity(dependency_map: Dict, level: int):
    outmap = {}
    for key, value in dependency_map.items():
        matches = re.findall(GRANULARITY_PATTERN, key)
        granular_key = '.'.join([m[1] for m in matches][0:level])
        if granular_key in outmap:
            outmap[granular_key] += value
        else:
            outmap[granular_key] = value

    for key, value in outmap.items():
        outmap[key] = list(set(value))
    dependency_map.clear()
    dependency_map.update(**outmap)


def _remove_internal_app_imports(dependency_map: Dict):
    for key, value in dependency_map.items():
        removals = []
        for item in value:
            if item.startswith(key):
                removals.append(item)
        for item in removals:
            value.remove(item)


def main():
    args = _parse_args()
    dependencies = {}

    _read_imports(os.getcwd(), dependencies)
    _remove_external_imports(dependencies)
    if args.ignore_tests:
        _remove_tests(dependencies)
    _set_granularity(dependencies, level=args.maxdepth)
    if not args.allow_internal:
        _remove_internal_app_imports(dependencies)
    _remove_empty_imports(dependencies)

    print(json.dumps(dependencies, indent=2))


if __name__ == '__main__':
    main()
