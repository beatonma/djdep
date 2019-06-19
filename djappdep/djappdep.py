import argparse
import os
import re
from typing import (
    List,
    Dict,
)


def _parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'app_names',
        nargs='+',
        help='File paths for the apps you are interested in.'
    )

    return parser.parse_args()


def _read_requirements_txt() -> List[str]:
    pattern = re.compile(r'^(\w+)([<>=]*).*?$')
    with open('requirements.txt', 'r') as f:
        packages = [
            re.match(pattern, line).group(1) for line in
            f.readlines()
        ]
    return packages


def read_app_imports(appname: str, output_map: Dict):
    for root, dirs, files in os.walk(appname):
        print(root)

        for f in files:
            if os.path.splitext(f)[1] == '.py':
                _read_file_imports(os.path.join(root, f), output_map)

    return output_map


def _read_file_imports(file, dependency_map: Dict):
    dotted_filepath = re.sub(r'[\\/]', r'.', file)
    dotted_filepath = re.sub(r'\.\.', '', dotted_filepath)
    dotted_filepath = re.sub(r'\.py$', '', dotted_filepath)
    dependency_map[dotted_filepath] = []

    pattern = re.compile(r'^(from ([.\w]+) )?import ([\w]+).*')
    with open(file, 'r') as f:
        for line in f.readlines():
            match = re.match(pattern, line)
            if match:
                imported_from = match.group(2) or ''
                if imported_from:
                    imported_from = f'{imported_from}.'
                imported = f'{imported_from}{match.group(3)}'
                dependency_map[dotted_filepath].append(imported)


if __name__ == '__main__':
    args = _parse_args()

    third_party = _read_requirements_txt()
    print(f'packages: {third_party}')

    dependencies = {}

    for app in args.app_names:
        dependencies = read_app_imports(app, dependencies)

    import json
    print(json.dumps(dependencies, indent=2))
