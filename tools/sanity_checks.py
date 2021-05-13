#!/usr/bin/env python3

import unittest
import json
import subprocess
import collections
import configparser

from pathlib import Path
from utils import Version


class TestReleases(unittest.TestCase):
    def test_releases(self):
        # Take list of git tags
        stdout = subprocess.check_output(['git', 'tag'])
        tags = [t.strip() for t in stdout.decode().splitlines()]

        with open('releases.json', 'r') as f:
            releases = json.load(f)
        for name, info in releases.items():
            # Make sure we can load wrap file
            config = configparser.ConfigParser()
            config.read(f'subprojects/{name}.wrap')
            self.assertEqual(config.sections()[0], 'wrap-file')

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

            # Verify versions are sorted, first must be newest
            versions = [Version(v) for v in info['versions']]
            self.assertEqual(sorted(versions, reverse=True), versions)

            # Verify all previous versions have a corresponding tag already.
            versions = info['versions']
            self.assertGreater(len(versions), 0)
            for v in versions[1:]:
                self.assertIn(f'{name}_{v}', tags)

        # All tags must be in the releases file
        for t in tags:
            name, version = t.rsplit('_', 1)
            self.assertIn(name, releases)
            self.assertIn(version, releases[name]['versions'])

        # Verify keys are sorted
        self.assertEqual(sorted(releases.keys()), list(releases.keys()))

if __name__ == '__main__':
    unittest.main()
