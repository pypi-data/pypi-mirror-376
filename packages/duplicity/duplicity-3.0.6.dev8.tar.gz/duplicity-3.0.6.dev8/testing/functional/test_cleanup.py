# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto
# Copyright 2007 Kenneth Loafman
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


import unittest

import pytest

from testing import _runtest_dir
from . import FunctionalTestCase


class CleanupTest(FunctionalTestCase):
    """
    Test cleanup using duplicity binary
    """

    @pytest.mark.slow
    def test_cleanup_after_partial(self):
        """
        Regression test for https://bugs.launchpad.net/bugs/409593
        where duplicity deletes all the signatures during a cleanup
        after a failed backup.
        """
        self.make_largefiles()
        good_files = self.backup("full", f"{_runtest_dir}/testfiles/largefiles")
        good_files |= self.backup("inc", f"{_runtest_dir}/testfiles/largefiles")
        good_files |= self.backup("inc", f"{_runtest_dir}/testfiles/largefiles")
        print("Trigger failing backup.", flush=True)
        self.backup("full", f"{_runtest_dir}/testfiles/largefiles", fail=2)
        bad_files = self.get_backend_files()
        bad_files -= good_files
        self.assertNotEqual(bad_files, set())
        # the cleanup should go OK
        self.run_duplicity(options=["cleanup", self.backend_url, "--force"])
        leftovers = self.get_backend_files()
        self.assertEqual(good_files, leftovers)
        self.backup("inc", f"{_runtest_dir}/testfiles/largefiles")
        self.verify(f"{_runtest_dir}/testfiles/largefiles")

    def test_remove_all_but_n_full(self):
        """
        Test that remove-all-but-n works in the simple case.
        """
        full1_files = self.backup("full", f"{_runtest_dir}/testfiles/empty_dir")
        full2_files = self.backup("full", f"{_runtest_dir}/testfiles/empty_dir")
        self.run_duplicity(options=["remove-all-but-n-full", "1", self.backend_url, "--force"])
        leftovers = self.get_backend_files()
        self.assertEqual(full2_files, leftovers)

    def test_remove_all_but_n_incl_jsonstat(self):
        """
        Test that remove-all-but-n works in the simple case.
        """
        full1_files = self.backup("full", f"{_runtest_dir}/testfiles/empty_dir", options=["--jsonstat"])
        full2_files = self.backup("full", f"{_runtest_dir}/testfiles/empty_dir", options=["--jsonstat"])
        self.run_duplicity(options=["remove-all-but-n-full", "1", self.backend_url, "--force"])
        leftovers = self.get_backend_files()
        self.assertEqual(full2_files, leftovers)

    def test_remove_all_inc_of_but_n_full(self):
        """
        Test that remove-all-inc-of-but-n-full works in the simple case.
        """
        full1_files = self.backup("full", f"{_runtest_dir}/testfiles/empty_dir")
        inc1_files = self.backup("inc", f"{_runtest_dir}/testfiles/empty_dir")
        full2_files = self.backup("full", f"{_runtest_dir}/testfiles/empty_dir")
        self.run_duplicity(options=["remove-all-inc-of-but-n-full", "1", self.backend_url, "--force"])
        leftovers = self.get_backend_files()
        self.assertEqual(full1_files | full2_files, leftovers)


if __name__ == "__main__":
    unittest.main()
