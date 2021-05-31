#!/usr/bin/env python3

import unittest
import json
import subprocess
import collections
import configparser
import re

from pathlib import Path
from utils import Version

PERMITTED_FILES = ['upstream.wrap', 'meson.build', 'readme.txt',
                   'meson_options.txt', '.gitignore', 'LICENSE.build']


class TestReleases(unittest.TestCase):
    def test_releases(self):
        # Take list of git tags
        stdout = subprocess.check_output(['git', 'tag'])
        tags = [t.strip() for t in stdout.decode().splitlines()]

        with open('releases.json', 'r') as f:
            releases = json.load(f)

        # All tags must be in the releases file
        for t in tags:
            name, version = t.rsplit('_', 1)
            self.assertIn(name, releases)
            self.assertIn(version, releases[name]['versions'])

        # Verify keys are sorted
        self.assertEqual(sorted(releases.keys()), list(releases.keys()))

        # Get the list of wraps that has modified packagefiles
        with open(Path.home() / 'files.json', 'r') as f:
            changed_files = json.load(f)
        self.changed_wraps = set()
        for f in changed_files:
            if f.startswith('subprojects/packagefiles'):
                self.changed_wraps.add(f.split('/')[2])

        for name, info in releases.items():
            # Make sure we can load wrap file
            config = configparser.ConfigParser()
            config.read(f'subprojects/{name}.wrap')
            self.assertEqual(config.sections()[0], 'wrap-file')
            wrap_section = config['wrap-file']
            self.check_has_no_path_separators(wrap_section['directory'])
            self.check_has_no_path_separators(wrap_section['source_filename'])

            # Basic checks
            self.assertTrue(re.fullmatch('[a-z][a-z0-9._-]*', name))
            patch_directory = wrap_section.get('patch_directory')
            if patch_directory:
                patch_path = Path('subprojects', 'packagefiles', patch_directory)
                self.assertTrue(patch_path.is_dir())
                # FIXME: Not all wraps currently complies, only check for wraps we modify.
                if name in self.changed_wraps:
                    self.assertTrue(Path(patch_path, 'LICENSE.build').is_file())
                    self.check_files(patch_path)

            # Make sure it has the same deps/progs provided
            progs = []
            deps = []
            if 'provide' in config.sections():
                provide = config['provide']
                progs = [i.strip() for i in provide.get('program_names', '').split(',')]
                deps = [i.strip() for i in provide.get('dependency_names', '').split(',')]
                for k in provide:
                    if k not in {'dependency_names', 'program_names'}:
                        deps.append(k.strip())
            progs = [i for i in progs if i]
            deps = [i for i in deps if i]
            self.assertEqual(sorted(progs), sorted(info['program_names']))
            self.assertEqual(sorted(deps), sorted(info['dependency_names']))

            # Verify versions are sorted
            versions = info['versions']
            self.assertGreater(len(versions), 0)
            versions_obj = [Version(v) for v in versions]
            self.assertEqual(sorted(versions_obj, reverse=True), versions_obj)

            # The first version could be a new release, all others must have
            # a corresponding tag already.
            for i, v in enumerate(versions):
                t = f'{name}_{v}'
                ver, rev = v.rsplit('-', 1)
                self.assertTrue(re.fullmatch('[a-z0-9._]+', ver))
                self.assertTrue(re.fullmatch('[0-9]+', rev))
                if i == 0:
                    self.check_source_url(name, wrap_section, ver)
                if i == 0 and t not in tags:
                    self.check_new_release(name, info, wrap_section)
                else:
                    self.assertIn(t, tags)

    def check_has_no_path_separators(self, value):
        self.assertNotIn('/', value)
        self.assertNotIn('\\', value)

    def check_source_url(self, name, wrap_section, version):
        if name == 'sqlite3':
            segs = version.split('.')
            assert(len(segs) == 3)
            version = segs[0] + segs[1] + '0' + segs[2]
        elif name == 're2':
            version = f'{version[:4]}-{version[4:6]}-{version[6:8]}'
        source_url = wrap_section['source_url']
        version_ = version.replace('.', '_')
        self.assertTrue(version in source_url or version_ in source_url,
                        f'Version {version} not found in {source_url}')

    def check_new_release(self, name, info, wrap_section):
        if not info.get('skip_ci', False):
            options = []
            for o in info.get('build_options', []):
                if ':' not in o:
                    options.append(f'-D{name}:{o}')
                else:
                    options.append(f'-D{o}')
            subprocess.check_call(['meson', 'setup', '_build', f'-Dwraps={name}'] + options)
            subprocess.check_call(['meson', 'compile', '-C', '_build'])
            subprocess.check_call(['meson', 'test', '-C', '_build'])
        else:
            subprocess.check_call(['meson', 'subprojects', 'download', name])

    def is_permitted_file(self, filename):
        if filename in PERMITTED_FILES:
            return True
        if filename.endswith('.h.meson'):
            return True
        return False

    def check_files(self, patch_path):
        tabs = []
        not_permitted = []
        for f in patch_path.rglob('*'):
            if f.is_dir():
                continue
            elif not self.is_permitted_file(f.name):
                not_permitted.append(f)
            elif f.name == 'meson.build' and '\t' in f.read_text():
                tabs.append(f)
        tabs_str = ', '.join([str(f) for f in tabs])
        not_permitted_str = ', '.join([str(f) for f in not_permitted])
        self.assertFalse(tabs_str, f'Tabs in meson.build files are not allows: ' + tabs_str)
        self.assertFalse(not_permitted_str, f'Not permitted files found: ' + not_permitted_str)


if __name__ == '__main__':
    unittest.main()
