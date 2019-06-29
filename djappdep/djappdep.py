"""Find and display dependencies between files in our project.
Standard library imports and  3rd party library imports are ignored.
"""
import sys

__version__ = '0.2'


import argparse
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import (
    Dict,
    Optional,
    List,
    Tuple,
)

DIR_BLACKLIST = [
    '__pycache__',
    '.git',
    '.idea',
    'env',
    'migrations',
]

IMPORT_PATTERN = re.compile(r'^(from ([.\w]+) )?import ([,.*\w]+).*')
IMPORT_PATTERN_SINGLELINE = re.compile(r'^(from ([.\w]+) )?import ([,.* \w]+)$', flags=re.MULTILINE)
IMPORT_PATTERN_MULTILINE = re.compile(r'^(from ([.\w]+) )?import \(([,.* \n\w]+)\)', flags=re.MULTILINE)

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
        '-i',
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

    parser.add_argument(
        '--version',
        '-v',
        action='store_true',
        default=False,
        help='Show installed version')

    args = parser.parse_args()
    if args.all:
        args.maxdepth = 1000
    if args.debug:
        log.setLevel(logging.DEBUG)

    return args


@dataclass
class Import:
    context_dir: str  # Used to convert relative imports to global
    from_package: Optional[str]  # from <from_package> ...
    item: str  # import <item> | from from_package import <item>

    def _global_path(self):

        if self.from_package.startswith('.'):
            return f'{self.context_dir}{self.from_package}.'
        elif self.from_package:
            return f'{self.from_package}.'
        elif self.item.startswith('.'):
            return f'{self.context_dir}'
        else:
            return ''

    def __str__(self):
        return f'{self._global_path()}{self.item}'


def _read_file_imports(file, dependency_map: Dict):
    """Add an entry in `dependency_map` using its dotted path as the key.
    The entry value is a list of dotted paths representing everything
    that was imported in that file.
    """
    dotted_cwd = _convert_path_filesystem_to_python(os.path.dirname(file))
    dotted_filepath = _convert_path_filesystem_to_python(file)

    dependency_map[dotted_filepath] = []

    with open(file, 'r') as f:
        text = f.read()
        dependency_map[dotted_filepath] += _read_imports(text, dotted_cwd)


def _read_imports(text, dotted_dir: str) -> List[str]:
    results = []

    for line in _find_import_lines(text):
        results += _read_import_match(line, dotted_dir)

    for block in _find_import_blocks(text):
        results += _read_import_match(block, dotted_dir)

    return results


def _find_import_lines(text):
    """Find single-line import statements e.g.
    import somepackage
    from somepackage import some_function
    from some.package import some_function, SomeClass
    """
    return re.findall(IMPORT_PATTERN_SINGLELINE, text)


def _find_import_blocks(text):
    """Find multiline import blocks e.g:
    from somepackage import (
        some_function,
        SomeClass,
    )"""
    return re.findall(IMPORT_PATTERN_MULTILINE, text)


def _read_import_match(line_match: Tuple, dotted_dir: str) -> List[str]:
    """Parse imports from a regex match tuple"""
    items = [x.strip().split(' ')[0] for x in line_match[2].split(',')]

    return [
        Import(
            context_dir=dotted_dir,
            from_package=line_match[1],
            item=item).__str__()
        for item in items
        if item  # Handle any trailing comma
    ]


def _convert_path_filesystem_to_python(absolute_path, cwd=os.getcwd()):
    """Convert Windows or *nix filepath to dotted.path."""
    dotted_path = os.path.relpath(absolute_path, cwd)
    dotted_path = re.sub(r'[(\\\\)/]', r'.', dotted_path)
    dotted_path = re.sub(r'\.py$', '', dotted_path)
    return dotted_path


def _read_imports_in_filetree(rootdir, dependency_map: Dict):
    """Read imports from any .py file found in any the given root directory
    or any decedent"""
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
    keys_pending_removal = []
    for key, value in dependency_map.items():
        if not value:
            keys_pending_removal.append(key)

    for key in keys_pending_removal:
        del dependency_map[key]


def _remove_external_imports(dependency_map):
    """Trim any imports that are not defined in the project. We are not
    interested in standard library packages or 3rd party libraries for our
    purposes."""

    internal_apps = [path.split('.')[0] for path in dependency_map.keys()]

    for key, value in dependency_map.items():
        dependency_map[key] = [x for x in value if x.split('.')[0] in internal_apps]


def _remove_tests(dependency_map: Dict):
    removals = []
    for key in dependency_map:
        if re.match(r'.*(test|tests|_test|test_).*', key):
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
    """Remove imports from within the same app, leaving only imports
    that involve other apps"""
    for key, value in dependency_map.items():
        removals = []
        for item in value:
            if item.startswith(f'{key}.'):
                removals.append(item)
        for item in removals:
            value.remove(item)


def _sort_imports(dependency_map: Dict):
    for key, value in dependency_map.items():
        value.sort()


def main():
    args = _parse_args()
    if args.version:
        log.info(f'djdep version: {__version__}')
        sys.exit()
    dependencies = {}

    _read_imports_in_filetree(os.getcwd(), dependencies)
    all_keys = sorted(dependencies.keys())
    _remove_external_imports(dependencies)
    if args.ignore_tests:
        _remove_tests(dependencies)
    _set_granularity(dependencies, level=args.maxdepth)
    if not args.allow_internal:
        _remove_internal_app_imports(dependencies)
    _remove_empty_imports(dependencies)
    _sort_imports(dependencies)
    pruned_keys = sorted(dependencies.keys())

    log.info(json.dumps(dependencies, indent=2, sort_keys=True))
    if args.debug:
        removed_keys = [k for k in all_keys if k not in pruned_keys]
        log.debug(
            f'Removed keys [{len(removed_keys)}]:')
        for k in removed_keys:
            log.debug(f'  {k}')


if __name__ == '__main__':
    main()
