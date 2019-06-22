"""Find and display dependencies between files in our project.
Standard library imports and  3rd party library imports are ignored.

TODO Handle relative imports like: `import .package.obj`"""

import argparse
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

IMPORT_PATTERN = re.compile(r'^(from ([.\w]+) )?import ([.\w]+).*')


log = logging.getLogger(__name__)


def _parse_args():
    parser = argparse.ArgumentParser()

    return parser.parse_args()


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

    with open(file, 'r') as f:
        for line in f.readlines():
            imported = _read_import_line(line, file)
            if imported:
                dependency_map[dotted_filepath].append(imported)


def _read_import_line(line: str, file) -> Optional[str]:
    match = re.match(IMPORT_PATTERN, line)
    if match:
        log.debug(match)
        imported_from = match.group(2) or ''
        if imported_from:
            imported_from = f'{imported_from}.'
        return f'{imported_from}{match.group(3)}'


def _convert_path_filesystem_to_python(absolute_path, cwd=os.getcwd()):
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


if __name__ == '__main__':
    dependencies = {}

    _read_imports(os.getcwd(), dependencies)
    _remove_external_imports(dependencies)
    _remove_empty_imports(dependencies)

    import json

    log.debug(json.dumps(dependencies, indent=2))
