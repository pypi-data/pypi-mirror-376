# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto
# Copyright 2007 Kenneth Loafman
# Copyright 2014 Aaron Whitehouse
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


import sys
from unittest.mock import patch

from duplicity.globmatch import *  # pylint: disable=unused-wildcard-import,redefined-builtin
from duplicity.path import *  # pylint: disable=unused-wildcard-import,redefined-builtin
from testing import _runtest_dir
from . import UnitTestCase


def sel_file(glob_str, include, file_path):
    """Returns the selection value for file_path, given the include value,
    returning:
    0 - if the file should be excluded
    1 - if the file should be included
    2 - if the folder should be scanned for any included/excluded files
    None - if the selection function has nothing to say about the file

    Note: including a folder implicitly includes everything within it."""

    select_fn = select_fn_from_glob(glob_str, include)
    selection_value = select_fn(Path(file_path))
    return selection_value


def inc_sel_file(glob_str, file_path):
    """Returns result of sel_file with include value set to 1"""
    # Aids readability of the testing code to only have one number (the
    # result of the select function)
    return sel_file(glob_str, 1, file_path)


def exc_sel_file(glob_str, file_path):
    """Returns result of sel_file with include value set to 0"""
    return sel_file(glob_str, 0, file_path)


def sel_dir(glob_str, include, file_path):
    """As per sel_file, but mocks file_path to be a directory"""
    with patch("duplicity.path.Path.isdir") as mock_isdir:
        mock_isdir.return_value = True
        return sel_file(glob_str, include, file_path)


def inc_sel_dir(glob_str, file_path):
    """Returns result of sel_dir with include value set to 1"""
    return sel_dir(glob_str, 1, file_path)


def exc_sel_dir(glob_str, file_path):
    """Returns result of sel_dir with include value set to 0"""
    return sel_dir(glob_str, 0, file_path)


class TestGlobToRegex(UnitTestCase):
    """Test translation of glob strings into regular expressions"""

    def test_glob_to_regex(self):
        """test_glob_re - test translation of shell pattern to regular exp"""
        self.assertEqual(glob_to_regex("hello"), "hello")
        self.assertEqual(glob_to_regex(".e?ll**o"), "\\.e[^/]ll.*o")
        self.assertEqual(glob_to_regex("[abc]el[^de][!fg]h"), "[abc]el[^de][^fg]h")

        # see https://bugs.python.org/issue29995 for details
        if sys.version_info[:2] == (3, 6):
            self.assertEqual(glob_to_regex("/usr/*/bin/"), "\\/usr\\/[^/]*\\/bin\\/")
        elif sys.version_info[:2] >= (3, 7):
            self.assertEqual(glob_to_regex("/usr/*/bin/"), "/usr/[^/]*/bin/")
        else:
            pass

        self.assertEqual(glob_to_regex("[a.b/c]"), "[a.b/c]")
        self.assertEqual(glob_to_regex("[a*b-c]e[!]]"), "[a*b-c]e[^]]")


class TestSelectValuesFromGlobs(UnitTestCase):
    """Test the select values returned from various globs"""

    def test_glob_scans_parent_directories(self):
        """Test glob scans parent"""
        self.assertEqual(
            inc_sel_dir(
                f"{_runtest_dir}/testfiles/parent/sub",
                f"{_runtest_dir}/testfiles/parent",
            ),
            2,
        )  # noqa
        self.assertEqual(
            inc_sel_dir(
                f"{_runtest_dir}/testfiles/select2/3/3sub2",
                f"{_runtest_dir}/testfiles/select2/3",
            ),
            2,
        )  # noqa

    def test_double_asterisk_include(self):
        """Test a few globbing patterns, including **"""
        self.assertEqual(inc_sel_file("**", "foo.txt"), 1)
        self.assertEqual(inc_sel_dir("**", "folder"), 1)

    def test_double_asterisk_extension_include(self):
        """Test **.py"""
        self.assertEqual(inc_sel_file("**.py", "what/ever.py"), 1)
        self.assertEqual(inc_sel_file("**.py", "what/ever.py/foo"), 1)
        self.assertEqual(inc_sel_dir("**.py", "foo"), 2)
        self.assertEqual(inc_sel_dir("**.py", "usr/local/bin"), 2)
        self.assertEqual(inc_sel_dir("**.py", "/usr/local/bin"), 2)


class TestTrailingSlash(UnitTestCase):
    """Test glob matching where the glob has a trailing slash"""

    def test_trailing_slash_matches_only_dirs(self):
        """Test matching where glob includes a trailing slash"""
        # Test the folder named "folder" is included
        self.assertEqual(inc_sel_dir("fold*/", "folder"), 1)

        # Test the file (not folder) named "folder" is not included
        self.assertEqual(inc_sel_file("fold*/", "folder"), None)
        self.assertEqual(inc_sel_file("folder/", "folder"), None)

        # Test miscellaneous file/folder
        self.assertEqual(inc_sel_file("fo*/", "foo.txt"), None)

    def test_included_files_are_matched_no_slash(self):
        """Test that files within an included folder are matched"""
        self.assertEqual(inc_sel_file("fold*", "folder/file.txt"), 1)
        self.assertEqual(inc_sel_file("fold*", "folder/file.txt"), 1)
        self.assertEqual(inc_sel_file("fold*", "folder/2/file.txt"), 1)

    def test_included_files_are_matched_no_slash_2(self):
        """Test that files within an included folder are matched"""
        self.assertEqual(inc_sel_file("folder", "folder/file.txt"), 1)
        self.assertEqual(inc_sel_file("folder/2", "folder/2/file.txt"), 1)

    def test_included_files_are_matched_slash(self):
        """Test that files within an included folder are matched with /"""
        # Bug #1624725
        # https://bugs.launchpad.net/duplicity/+bug/1624725
        self.assertEqual(inc_sel_file("folder/", "folder/file.txt"), 1)

    def test_included_files_are_matched_slash_2(self):
        """Test that files within an included folder are matched with /"""
        # Bug #1624725
        # https://bugs.launchpad.net/duplicity/+bug/1624725
        self.assertEqual(
            inc_sel_file(
                f"{_runtest_dir}/testfiles/select2/1/1sub1/1sub1sub1/",
                f"{_runtest_dir}/testfiles/select2/1/1sub1/1sub1sub1/1sub1sub1_file.txt",
            ),
            1,
        )

    def test_included_files_are_matched_slash_2_parents(self):
        """Test that duplicity will scan parent of glob/"""
        # Bug #1624725
        # https://bugs.launchpad.net/duplicity/+bug/1624725
        self.assertEqual(
            inc_sel_dir(
                f"{_runtest_dir}/testfiles/select2/1/1sub1/1sub1sub1/",
                f"{_runtest_dir}/testfiles/select2/1/1sub1/1sub1sub1",
            ),
            1,
        )
        self.assertEqual(
            inc_sel_dir(
                f"{_runtest_dir}/testfiles/select2/1/1sub1/1sub1sub1/",
                f"{_runtest_dir}/testfiles/select2/1/1sub1",
            ),
            2,
        )

    def test_included_files_are_matched_slash_wildcard(self):
        """Test that files within an included folder are matched with /"""
        # Bug #1624725
        # https://bugs.launchpad.net/duplicity/+bug/1624725
        self.assertEqual(inc_sel_file("fold*/", "folder/file.txt"), 1)

    def test_slash_matches_everything(self):
        """Test / matches everything"""
        self.assertEqual(inc_sel_dir("/", f"{_runtest_dir}/testfiles/select/1/2"), 1)
        self.assertEqual(inc_sel_dir("/", "/test/random/path"), 1)
        self.assertEqual(exc_sel_dir("/", "/test/random/path"), 0)
        self.assertEqual(inc_sel_dir("/", "/"), 1)
        self.assertEqual(inc_sel_dir("/", "/var/log"), 1)
        self.assertEqual(inc_sel_file("/", "/var/log/log.txt"), 1)

    def test_slash_star_scans_folder(self):
        """Test that folder/* scans folder/"""
        # This behaviour is a bit ambiguous - either include or scan could be
        # argued as most appropriate here, but only an empty folder is at stake
        # so long as test_slash_star_includes_folder_contents passes.
        self.assertEqual(inc_sel_dir("folder/*", "folder"), 2)

    def test_slash_star_includes_folder_contents(self):
        """Test that folder/* includes folder contents"""
        self.assertEqual(inc_sel_file("folder/*", "folder/file.txt"), 1)
        self.assertEqual(inc_sel_file("folder/*", "folder/other_file.log"), 1)

    def test_slash_star_star_scans_folder(self):
        """Test that folder/** scans folder/"""
        self.assertEqual(inc_sel_dir("folder/**", "folder"), 2)

    def test_simple_trailing_slash_match(self):
        """Test that a normal folder string ending in / matches that path"""
        self.assertEqual(
            inc_sel_dir(
                f"{_runtest_dir}/testfiles/select/1/2/1/",
                f"{_runtest_dir}/testfiles/select/1/2/1",
            ),
            1,
        )

    def test_double_asterisk_string_slash(self):
        """Test string starting with ** and ending in /"""
        self.assertEqual(inc_sel_dir("**/1/2/", f"{_runtest_dir}/testfiles/select/1/2"), 1)

    def test_string_double_asterisk_string_slash(self):
        """Test string ** string /"""
        self.assertEqual(
            inc_sel_dir(f"{_runtest_dir}/testfiles**/2/", f"{_runtest_dir}/testfiles/select/1/2"),
            1,
        )


class TestDoubleAsterisk(UnitTestCase):
    """Test glob matching where the glob finishes with a **"""

    def test_double_asterisk_no_match(self):
        """Test that a folder string ending /** does not match other paths"""
        self.assertEqual(inc_sel_dir("/test/folder/**", "/test/foo"), None)

    def test_double_asterisk_match(self):
        """Test that a folder string ending in /** matches that path"""
        self.assertEqual(inc_sel_dir("/test/folder/**", "/test/folder/foo"), 1)
        self.assertEqual(inc_sel_file("/test/folder/**", "/test/folder/foo.txt"), 1)
        self.assertEqual(inc_sel_dir("/test/folder/**", "/test/folder/2/foo"), 1)
        self.assertEqual(inc_sel_file("/test/folder/**", "/test/folder/2/foo.txt"), 1)

    def test_asterisk_slash_double_asterisk(self):
        """Test folder string ending in */**"""
        self.assertEqual(inc_sel_dir("fold*/**", "folder"), 2)


class TestSimpleUnicode(UnitTestCase):
    """Test simple unicode comparison"""

    def test_simple_unicode(self):
        """Test simple unicode comparison"""
        self.assertEqual(
            inc_sel_file(
                "прыклад/пример/例/Παράδειγμα/उदाहरण.txt",
                "прыклад/пример/例/Παράδειγμα/उदाहरण.txt",
            ),
            1,
        )


class TestSquareBrackets(UnitTestCase):
    """Test glob matching where the glob includes []s and [!]s"""

    def test_square_bracket_options(self):
        """Test file including options in []s"""
        self.assertEqual(inc_sel_file("/test/f[o,s,p]lder/foo.txt", "/test/folder/foo.txt"), 1)
        self.assertEqual(inc_sel_file("/test/f[i,s,p]lder/foo.txt", "/test/folder/foo.txt"), None)
        self.assertEqual(inc_sel_file("/test/f[s,o,p]lder/foo.txt", "/test/folder/foo.txt"), 1)

    def test_square_bracket_options_unicode(self):
        """Test file including options in []s"""
        self.assertEqual(
            inc_sel_file(
                "прыклад/пр[и,j,l]мер/例/Παράδειγμα/उदाहरण.txt",
                "прыклад/пример/例/Παράδειγμα/उदाहरण.txt",
            ),
            1,
        )
        self.assertEqual(
            inc_sel_file(
                "прыклад/п[a,b,c]имер/例/Παράδειγμα/उदाहरण.txt",
                "прыклад/пример/例/Παράδειγμα/उदाहरण.txt",
            ),
            None,
        )

    def test_not_square_bracket_options(self):
        """Test file including options in [!]s"""
        self.assertEqual(inc_sel_file("/test/f[!o,s,p]lder/foo.txt", "/test/folder/foo.txt"), None)
        self.assertEqual(inc_sel_file("/test/f[!i,s,p]lder/foo.txt", "/test/folder/foo.txt"), 1)
        self.assertEqual(inc_sel_file("/test/f[!s,o,p]lder/foo.txt", "/test/folder/foo.txt"), None)

    def test_square_bracket_range(self):
        """Test file including range in []s"""
        self.assertEqual(inc_sel_file("/test/folder[1-5]/foo.txt", "/test/folder4/foo.txt"), 1)
        self.assertEqual(inc_sel_file("/test/folder[5-9]/foo.txt", "/test/folder4/foo.txt"), None)
        self.assertEqual(inc_sel_file("/test/folder[1-5]/foo.txt", "/test/folder6/foo.txt"), None)

    def test_square_bracket_not_range(self):
        """Test file including range in [!]s"""
        self.assertEqual(inc_sel_file("/test/folder[!1-5]/foo.txt", "/test/folder4/foo.txt"), None)
        self.assertEqual(inc_sel_file("/test/folder[!5-9]/foo.txt", "/test/folder4/foo.txt"), 1)
        self.assertEqual(inc_sel_file("/test/folder[!1-5]/foo.txt", "/test/folder6/foo.txt"), 1)
