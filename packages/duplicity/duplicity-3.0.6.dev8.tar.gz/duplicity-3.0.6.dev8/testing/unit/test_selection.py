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


import io
import platform
import unittest
from unittest.mock import patch

from duplicity.lazy import *  # pylint: disable=unused-wildcard-import,redefined-builtin
from duplicity.selection import *  # pylint: disable=unused-wildcard-import,redefined-builtin
from . import UnitTestCase


class MatchingTest(UnitTestCase):
    """Test matching of file names against various selection functions"""

    def setUp(self):
        super().setUp()
        self.unpack_testfiles()
        self.root = Path("testfiles/select")
        self.Select = Select(self.root)

    def makeext(self, path):
        return self.root.new_index(tuple(path.encode().split(b"/")))

    def testRegexp(self):
        """Test regular expression selection func"""
        sf1 = self.Select.regexp_get_sf(".*\\.py", 1)
        assert sf1(self.makeext("1.py")) == 1
        assert sf1(self.makeext("usr/foo.py")) == 1
        assert sf1(self.root.append("1.doc")) is None

        sf2 = self.Select.regexp_get_sf("hello", 0)
        assert sf2(Path("hello")) == 0
        assert sf2(Path("foohello_there")) == 0
        assert sf2(Path("foo")) is None

    def test_tuple_include(self):
        """Test include selection function made from a regular filename"""
        self.assertRaises(FilePrefixError, self.Select.glob_get_sf, "foo", 1)

        sf2 = self.Select.general_get_sf("testfiles/select/usr/local/bin/", 1)

        with patch("duplicity.path.ROPath.isdir") as mock_isdir:
            mock_isdir.return_value = True
            # Can't pass the return_value as an argument to patch, i.e.:
            # with patch("duplicity.path.ROPath.isdir", return_value=True):
            # as build system's mock is too old to support it.

            self.assertEqual(sf2(self.makeext("usr")), 2)
            self.assertEqual(sf2(self.makeext("usr/local")), 2)
            self.assertEqual(sf2(self.makeext("usr/local/bin")), 1)
            self.assertEqual(sf2(self.makeext("usr/local/doc")), None)
            self.assertEqual(sf2(self.makeext("usr/local/bin/gzip")), 1)
            self.assertEqual(sf2(self.makeext("usr/local/bingzip")), None)

    def test_tuple_exclude(self):
        """Test exclude selection function made from a regular filename"""
        self.assertRaises(FilePrefixError, self.Select.glob_get_sf, "foo", 0)

        sf2 = self.Select.general_get_sf("testfiles/select/usr/local/bin/", 0)

        with patch("duplicity.path.ROPath.isdir") as mock_isdir:
            mock_isdir.return_value = True

            assert sf2(self.makeext("usr")) is None
            assert sf2(self.makeext("usr/local")) is None
            assert sf2(self.makeext("usr/local/bin")) == 0
            assert sf2(self.makeext("usr/local/doc")) is None
            assert sf2(self.makeext("usr/local/bin/gzip")) == 0
            assert sf2(self.makeext("usr/local/bingzip")) is None

    def test_glob_star_include(self):
        """Test a few globbing patterns, including **"""
        sf1 = self.Select.general_get_sf("**", 1)
        assert sf1(self.makeext("foo")) == 1
        assert sf1(self.makeext("")) == 1

        sf2 = self.Select.general_get_sf("**.py", 1)
        assert sf2(self.makeext("foo")) == 2
        assert sf2(self.makeext("usr/local/bin")) == 2
        assert sf2(self.makeext("what/ever.py")) == 1
        assert sf2(self.makeext("what/ever.py/foo")) == 1

    def test_glob_star_exclude(self):
        """Test a few glob excludes, including **"""
        sf1 = self.Select.general_get_sf("**", 0)
        assert sf1(self.makeext("/usr/local/bin")) == 0

        sf2 = self.Select.general_get_sf("**.py", 0)
        assert sf2(self.makeext("foo")) is None
        assert sf2(self.makeext("usr/local/bin")) is None
        assert sf2(self.makeext("what/ever.py")) == 0
        assert sf2(self.makeext("what/ever.py/foo")) == 0

    def test_simple_glob_double_asterisk(self):
        """test_simple_glob_double_asterisk - primarily to check that the defaults used by the error tests work"""
        assert self.Select.glob_get_sf("**", 1)

    def test_glob_sf_exception(self):
        """test_glob_sf_exception - see if globbing errors returned"""
        self.assertRaises(GlobbingError, self.Select.glob_get_sf, "testfiles/select/hello//there", 1)

    def test_file_prefix_sf_exception(self):
        """test_file_prefix_sf_exception - see if FilePrefix error is returned"""
        # These should raise a FilePrefixError because the root directory for the selection is "testfiles/select"
        self.assertRaises(FilePrefixError, self.Select.general_get_sf, "testfiles/whatever", 1)
        self.assertRaises(FilePrefixError, self.Select.general_get_sf, "testfiles/?hello", 0)

    def test_scan(self):
        """Tests what is returned for selection tests regarding directory scanning"""
        select = Select(Path("/"))

        assert select.general_get_sf("**.py", 1)(Path("/")) == 2
        assert select.general_get_sf("**.py", 1)(Path("foo")) == 2
        assert select.general_get_sf("**.py", 1)(Path("usr/local/bin")) == 2
        assert select.general_get_sf("/testfiles/select/**.py", 1)(Path("/testfiles/select")) == 2
        assert select.general_get_sf("/testfiles/select/test.py", 1)(Path("/testfiles/select")) == 2
        assert select.glob_get_sf("/testfiles/se?ect/test.py", 1)(Path("/testfiles/select")) == 2
        assert select.general_get_sf("/testfiles/select/test.py", 0)(Path("/testfiles/select")) is None
        assert select.glob_get_sf("/testfiles/select/test.py", 0)(Path("/testfiles/select")) is None

    def test_ignore_case(self):
        """test_ignore_case - try a few expressions with ignorecase:"""

        sf = self.Select.general_get_sf("ignorecase:testfiles/SeLect/foo/bar", 1)
        assert sf(self.makeext("FOO/BAR")) == 1
        assert sf(self.makeext("foo/bar")) == 1
        assert sf(self.makeext("fOo/BaR")) == 1
        self.assertRaises(
            FilePrefixError,
            self.Select.general_get_sf,
            "ignorecase:tesfiles/sect/foo/bar",
            1,
        )

    def test_ignore_case_prefix_override(self):
        """test_ignore_case - confirm that ignorecase: overrides default. might
        seem a bit odd as ignore_case=False is the default, but --filter-strictcase is
        implemented by explicitly setting this parameter. this test should also
        cause a stop-and-think if someone changes said default arg value for
        general_get_sf() in future.
        """

        sf = self.Select.general_get_sf("ignorecase:testfiles/SeLect/foo/bar", 1, ignore_case=False)
        assert sf(self.makeext("FOO/BAR")) == 1
        assert sf(self.makeext("foo/bar")) == 1
        assert sf(self.makeext("fOo/BaR")) == 1
        self.assertRaises(
            FilePrefixError,
            self.Select.general_get_sf,
            "ignorecase:tesfiles/sect/foo/bar",
            1,
            ignore_case=False,
        )

    def test_root(self):
        """test_root - / may be a counterexample to several of these.."""
        root = Path("/")
        select = Select(root)

        self.assertEqual(select.general_get_sf("/", 1)(root), 1)
        self.assertEqual(select.general_get_sf("/foo", 1)(root), 2)
        self.assertEqual(select.general_get_sf("/foo/bar", 1)(root), 2)
        self.assertEqual(select.general_get_sf("/", 0)(root), 0)
        self.assertEqual(select.general_get_sf("/foo", 0)(root), None)

        assert select.general_get_sf("**.py", 1)(root) == 2
        assert select.general_get_sf("**", 1)(root) == 1
        assert select.general_get_sf("ignorecase:/", 1)(root) == 1
        assert select.general_get_sf("**.py", 0)(root) is None
        assert select.general_get_sf("**", 0)(root) == 0
        assert select.general_get_sf("/foo/*", 0)(root) is None

    def test_other_filesystems(self):
        """Test to see if --exclude-other-filesystems works correctly"""
        root = Path("/")
        select = Select(root)
        sf = select.other_filesystems_get_sf(0)
        assert sf(root) is None
        if os.path.ismount("/usr/bin"):
            sfval = 0
        else:
            sfval = None
        assert sf(Path("/usr/bin")) == sfval, "Assumption: /usr/bin is on the same filesystem as /"
        if os.path.ismount("/dev"):
            sfval = 0
        else:
            sfval = None
        assert sf(Path("/dev")) == sfval, "Assumption: /dev is on a different filesystem"
        if os.path.ismount("/proc"):
            sfval = 0
        else:
            sfval = None
        assert sf(Path("/proc")) == sfval, "Assumption: /proc is on a different filesystem"

    def test_literal_special_chars(self):
        """Test literal match with globbing and regex special characters"""
        select = Select(Path("/foo"))
        assert select.literal_get_sf("/foo/b*r", 1)(Path("/foo/bar")) is None
        assert select.literal_get_sf("/foo/b*r", 1)(Path("/foo/b*r")) == 1
        assert select.literal_get_sf("/foo/b[a-b]r", 1)(Path("/foo/bar")) is None
        assert select.literal_get_sf("/foo/b[a-b]r", 1)(Path("/foo/b[a-b]r")) == 1
        assert select.literal_get_sf("/foo/b\ar", 0)(Path("/foo/bar")) is None
        assert select.literal_get_sf("/foo/b\ar", 0)(Path("/foo/b\ar")) == 0
        assert select.literal_get_sf("/foo/b?r", 0)(Path("/foo/bar")) is None
        assert select.literal_get_sf("/foo/b?r", 0)(Path("/foo/b?r")) == 0


class ParseArgsTest(UnitTestCase):
    """Test argument parsing"""

    def setUp(self):
        super().setUp()
        self.unpack_testfiles()
        self.root = None
        self.expected_restored_tree = [
            (),
            ("1",),
            ("1", "1sub1"),
            ("1", "1sub1", "1sub1sub1"),
            ("1", "1sub1", "1sub1sub1", "1sub1sub1_file.txt"),
            ("1", "1sub1", "1sub1sub3"),
            ("1", "1sub2"),
            ("1", "1sub2", "1sub2sub1"),
            ("1", "1sub3"),
            ("1", "1sub3", "1sub3sub3"),
            ("1.py",),
            ("2",),
            ("2", "2sub1"),
            ("2", "2sub1", "2sub1sub1"),
            ("2", "2sub1", "2sub1sub1", "2sub1sub1_file.txt"),
            ("3",),
            ("3", "3sub2"),
            ("3", "3sub2", "3sub2sub1"),
            ("3", "3sub2", "3sub2sub2"),
            ("3", "3sub2", "3sub2sub3"),
            ("3", "3sub3"),
            ("3", "3sub3", "3sub3sub1"),
            ("3", "3sub3", "3sub3sub2"),
            ("3", "3sub3", "3sub3sub2", "3sub3sub2_file.txt"),
            ("3", "3sub3", "3sub3sub3"),
        ]

    def uc_index_from_path(self, path):
        """Takes a path type and returns path.index, with each element converted into unicode"""
        uindex = tuple([element.decode(sys.getfilesystemencoding(), "strict") for element in path.index])
        return uindex

    def ParseTest(self, tuplelist, indicies, filelists=None):
        """No error if running select on tuple goes over indicies"""
        if filelists is None:
            filelists = []
        if not self.root:
            self.root = Path("testfiles/select")
        self.Select = Select(self.root)
        self.Select.ParseArgs(tuplelist, self.remake_filelists(filelists))
        self.Select.set_iter()

        # Create a list of the paths returned by the select function, converted
        # into path.index styled tuples
        results_as_list = list(Iter.map(self.uc_index_from_path, self.Select))
        self.assertEqual(indicies, results_as_list)

    def remake_filelists(self, filelist):
        """Turn strings in filelist into fileobjs"""
        new_filelists = []
        for f in filelist:
            if isinstance(f, str):
                new_filelists.append(io.StringIO(f))
            else:
                new_filelists.append(f)
        return new_filelists

    def test_parse(self):
        """Test just one include, all exclude"""
        self.ParseTest(
            [("--include", "testfiles/select/1/1"), ("--exclude", "**")],
            [(), ("1",), ("1", "1"), ("1", "1", "1"), ("1", "1", "2"), ("1", "1", "3")],
        )

    def test_parse2(self):
        """Test three level include/exclude"""
        self.ParseTest(
            [
                ("--exclude", "testfiles/select/1/1/1"),
                ("--include", "testfiles/select/1/1"),
                ("--exclude", "testfiles/select/1"),
                ("--exclude", "**"),
            ],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
        )

    def test_filelist(self):
        """Filelist glob test similar to above testParse2"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_files_from_no_selections(self):
        """Confirm that --files-from works in isolation"""
        self.ParseTest(
            [("--files-from", "file")],
            [
                (),
                ("1.doc",),
                ("1.py",),
                ("efools",),
                ("efools", "ping"),
                ("foobar",),
                ("foobar", "pong"),
            ],
            ["1.doc\n" "1.py\n" "efools/ping\n" "foobar/pong"],
        )

    def test_files_from_implicit_parents(self):
        """Confirm that --files-from includes parent directories implicitly"""
        self.ParseTest(
            [("--files-from", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "1"), ("2",)],
            ["1/1/1\n" "2"],
        )

    def test_files_from_with_exclusions(self):
        """Confirm that --files-from still respects the usual file selection rules"""
        self.ParseTest(
            [
                ("--files-from", "file"),
                ("--exclude", "testfiles/select/*.py"),
                ("--exclude", "testfiles/select/3/3/3"),
            ],
            [
                (),
                ("1",),
                ("1", "1"),
                ("1", "1", "1"),
                ("1.doc",),
                ("2",),
                ("2", "2"),
                ("2", "2", "2"),
                ("3",),
                ("3", "3"),
            ],
            ["1.doc\n" "1.py\n" "1/1/1\n" "2/2/2\n" "3/3/3"],
        )

    def test_files_from_with_inclusions(self):
        """Confirm that --files-from still respects the usual file selection rules"""
        self.ParseTest(
            [
                ("--files-from", "file"),
                ("--include", "testfiles/select/1.*"),
                ("--exclude", "**"),
            ],
            [(), ("1.doc",), ("1.py",)],
            ["1.doc\n" "1.py\n" "1\n" "2\n" "3"],
        )

    def test_files_from_multiple_filelists(self):
        """Check that --files-from can co-exist with other options using file lists"""
        self.ParseTest(
            [("--files-from", "file"), ("--include-filelist", "file")],
            [(), ("1",), ("1", "2"), ("1", "2", "3"), ("1.doc",)],
            [
                "1.doc\n"  # --files-from
                "1.py\n"
                "1/1/1\n"
                "1/1/2\n"
                "1/1/3\n"
                "1/2/1\n"
                "1/2/2\n"
                "1/2/3\n"
                "1/3/1\n"
                "1/3/2\n"
                "1/3/3\n"
                "2",
                "+ testfiles/select/*.doc\n" "+ testfiles/select/1/2/3\n" "- **",  # --include-filelist
            ],
        )

    def test_files_from_null_separator(self):
        """Check that --files-from works with null separators when requested"""
        self.set_config("null_separator", 1)
        self.ParseTest(
            [
                ("--files-from", "file"),
                ("--include", "testfiles/select/*.doc"),
                ("--include", "testfiles/select/1/2/3"),
                ("--exclude", "**"),
            ],
            [(), ("1",), ("1", "2"), ("1", "2", "3"), ("1.doc",)],
            [
                "1.doc\0"
                "1.py\0"
                "1/1/1\0"
                "1/1/2\0"
                "1/1/3\0"
                "1/2/1\0"
                "1/2/2\0"
                "1/2/3\0"
                "1/3/1\0"
                "1/3/2\0"
                "1/3/3\0"
                "2"
            ],
        )

    def test_include_filelist_1_trailing_whitespace(self):
        """Filelist glob test similar to globbing filelist, but with 1 trailing whitespace on include"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "testfiles/select/1/1 \n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_2_trailing_whitespaces(self):
        """Filelist glob test similar to globbing filelist, but with 2 trailing whitespaces on include"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "testfiles/select/1/1  \n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_1_leading_whitespace(self):
        """Filelist glob test similar to globbing filelist, but with 1 leading whitespace on include"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" " testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_2_leading_whitespaces(self):
        """Filelist glob test similar to globbing filelist, but with 2 leading whitespaces on include"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "  testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_1_trailing_whitespace_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 1 trailing whitespace on exclude"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1 \n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_2_trailing_whitespace_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 2 trailing whitespaces on exclude"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1  \n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_1_leading_whitespace_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 1 leading whitespace on exclude"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            [" - testfiles/select/1/1/1\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_2_leading_whitespaces_exclude(self):
        """Filelist glob test similar to globbing filelist, but with 2 leading whitespaces on exclude"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["  - testfiles/select/1/1/1\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_check_excluded_folder_included_for_contents(self):
        """Filelist glob test to check excluded folder is included if contents are"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [
                (),
                ("1",),
                ("1", "1"),
                ("1", "1", "1"),
                ("1", "1", "2"),
                ("1", "1", "3"),
                ("1", "2"),
                ("1", "2", "1"),
                ("1", "3"),
                ("1", "3", "1"),
                ("1", "3", "2"),
                ("1", "3", "3"),
            ],
            ["+ testfiles/select/1/2/1\n" "- testfiles/select/1/2\n" "testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_with_unnecessary_quotes(self):
        """Filelist glob test similar to globbing filelist, but with quotes around one of the paths."""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- 'testfiles/select/1/1/1'\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_with_unnecessary_double_quotes(self):
        """Filelist glob test similar to globbing filelist, but with double quotes around one of the paths."""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ['- "testfiles/select/1/1/1"\n' "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_with_full_line_comment(self):
        """Filelist glob test similar to globbing filelist, but with a full-line comment."""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            [
                "- testfiles/select/1/1/1\n"
                "# This is a test\n"
                "testfiles/select/1/1\n"
                "- testfiles/select/1\n"
                "- **"
            ],
        )

    def test_include_filelist_with_blank_line(self):
        """Filelist glob test similar to globbing filelist, but with a blank line."""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_with_blank_line_and_whitespace(self):
        """Filelist glob test similar to globbing filelist, but with a blank line and whitespace."""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "  \n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_asterisk(self):
        """Filelist glob test with * instead of 'testfiles'"""
        # Thank you to Elifarley Cruz for this test case
        # (https://bugs.launchpad.net/duplicity/+bug/884371).
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["*/select/1/1\n" "- **"],
        )

    def test_include_filelist_asterisk_2(self):
        """Identical to test_filelist, but with the exclude "select" replaced with '*'"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/*/1/1/1\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_asterisk_3(self):
        """Identical to test_filelist, but with the auto-include "select" replaced with '*'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "testfiles/*/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_asterisk_4(self):
        """Identical to test_filelist, but with a specific include "select" replaced with '*'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "+ testfiles/*/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_asterisk_5(self):
        """Identical to test_filelist, but with all 'select's replaced with '*'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/*/1/1/1\n" "+ testfiles/*/1/1\n" "- testfiles/*/1\n" "- **"],
        )

    def test_include_filelist_asterisk_6(self):
        """Identical to test_filelist, but with numerous excluded folders replaced with '*'"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- */*/1/1/1\n" "+ testfiles/select/1/1\n" "- */*/1\n" "- **"],
        )

    def test_include_filelist_asterisk_7(self):
        """Identical to test_filelist, but with numerous included/excluded folders replaced with '*'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- */*/1/1/1\n" "+ */*/1/1\n" "- */*/1\n" "- **"],
        )

    def test_include_filelist_double_asterisk_1(self):
        """Identical to test_filelist, but with the exclude "select' replaced with '**'"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/**/1/1/1\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_double_asterisk_2(self):
        """Identical to test_filelist, but with the include 'select' replaced with '**'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "**ct/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_double_asterisk_3(self):
        """Identical to test_filelist, but with the exclude 'testfiles/select' replaced with '**'"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- **/1/1/1\n" "testfiles/select/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_double_asterisk_4(self):
        """Identical to test_filelist, but with the include 'testfiles/select' replaced with '**'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1\n" "**t/1/1\n" "- testfiles/select/1\n" "- **"],
        )

    def test_include_filelist_double_asterisk_5(self):
        """Identical to test_filelist, but with all 'testfiles/select's replaced with '**'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- **/1/1/1\n" "**t/1/1\n" "- **t/1\n" "- **"],
        )

    def test_include_filelist_trailing_slashes(self):
        """Filelist glob test similar to globbing filelist, but with trailing slashes"""
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- testfiles/select/1/1/1/\n" "testfiles/select/1/1/\n" "- testfiles/select/1/\n" "- **"],
        )

    def test_include_filelist_trailing_slashes_and_single_asterisks(self):
        """Filelist glob test similar to globbing filelist, but with trailing slashes and single asterisks"""
        # Regression test for Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- */select/1/1/1/\n" "testfiles/select/1/1/\n" "- testfiles/*/1/\n" "- **"],
        )

    def test_include_filelist_trailing_slashes_and_double_asterisks(self):
        """Filelist glob test similar to globbing filelist, but with trailing slashes and double asterisks"""
        # Regression test for Bug #932482 (https://bugs.launchpad.net/duplicity/+bug/932482)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["- **/1/1/1/\n" "testfiles/select/1/1/\n" "- **t/1/\n" "- **"],
        )

    def test_filelist_null_separator(self):
        """test_filelist, but with null_separator set"""
        self.set_config("null_separator", 1)
        self.ParseTest(
            [("--include-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["\0- testfiles/select/1/1/1\0testfiles/select/1/1\0- testfiles/select/1\0- **\0"],
        )

    def test_exclude_filelist(self):
        """Exclude version of test_filelist"""
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["testfiles/select/1/1/1\n" "+ testfiles/select/1/1\n" "testfiles/select/1\n" "- **"],
        )

    def test_exclude_filelist_asterisk_1(self):
        """Exclude version of test_include_filelist_asterisk"""
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["+ */select/1/1\n" "- **"],
        )

    def test_exclude_filelist_asterisk_2(self):
        """Identical to test_exclude_filelist, but with the exclude "select" replaced with '*'"""
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["testfiles/*/1/1/1\n" "+ testfiles/select/1/1\n" "testfiles/select/1\n" "- **"],
        )

    def test_exclude_filelist_asterisk_3(self):
        """Identical to test_exclude_filelist, but with the include "select" replaced with '*'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["testfiles/select/1/1/1\n" "+ testfiles/*/1/1\n" "testfiles/select/1\n" "- **"],
        )

    def test_exclude_filelist_asterisk_4(self):
        """Identical to test_exclude_filelist, but with numerous excluded folders replaced with '*'"""
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["*/select/1/1/1\n" "+ testfiles/select/1/1\n" "*/*/1\n" "- **"],
        )

    def test_exclude_filelist_asterisk_5(self):
        """Identical to test_exclude_filelist, but with numerous included/excluded folders replaced with '*'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["*/select/1/1/1\n" "+ */*/1/1\n" "*/*/1\n" "- **"],
        )

    def test_exclude_filelist_double_asterisk(self):
        """Identical to test_exclude_filelist, but with all included/excluded folders replaced with '**'"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("1",), ("1", "1"), ("1", "1", "2"), ("1", "1", "3")],
            ["**/1/1/1\n" "+ **t/1/1\n" "**t/1\n" "- **"],
        )

    def test_exclude_filelist_single_asterisk_at_beginning(self):
        """Exclude filelist testing limited functionality of functional test"""
        # Regression test for Bug #884371 (https://bugs.launchpad.net/duplicity/+bug/884371)
        self.root = Path("testfiles/select/1")
        self.ParseTest(
            [("--exclude-filelist", "file")],
            [(), ("2",), ("2", "1")],
            ["+ */select/1/2/1\n" "- testfiles/select/1/2\n" "- testfiles/*/1/1\n" "- testfiles/select/1/3"],
        )

    def test_commandline_asterisks_double_both(self):
        """Unit test the functional test TestAsterisks.test_commandline_asterisks_double_both"""
        self.root = Path("testfiles/select/1")
        self.ParseTest(
            [
                ("--include", "**/1/2/1"),
                ("--exclude", "**t/1/2"),
                ("--exclude", "**t/1/1"),
                ("--exclude", "**t/1/3"),
            ],
            [(), ("2",), ("2", "1")],
        )

    def test_includes_files(self):
        """Unit test the functional test test_includes_files"""
        # Test for Bug 1624725
        # https://bugs.launchpad.net/duplicity/+bug/1624725
        self.root = Path("testfiles/select2/1/1sub1")
        self.ParseTest(
            [("--include", "testfiles/select2/1/1sub1/1sub1sub1"), ("--exclude", "**")],
            [(), ("1sub1sub1",), ("1sub1sub1", "1sub1sub1_file.txt")],
        )

    def test_includes_files_trailing_slash(self):
        """Unit test the functional test test_includes_files_trailing_slash"""
        # Test for Bug 1624725
        # https://bugs.launchpad.net/duplicity/+bug/1624725
        self.root = Path("testfiles/select2/1/1sub1")
        self.ParseTest(
            [
                ("--include", "testfiles/select2/1/1sub1/1sub1sub1/"),
                ("--exclude", "**"),
            ],
            [(), ("1sub1sub1",), ("1sub1sub1", "1sub1sub1_file.txt")],
        )

    def test_includes_files_trailing_slash_globbing_chars(self):
        """Unit test functional test_includes_files_trailing_slash_globbing_chars"""
        # Test for Bug 1624725
        # https://bugs.launchpad.net/duplicity/+bug/1624725
        self.root = Path("testfiles/select2/1/1sub1")
        self.ParseTest(
            [
                ("--include", "testfiles/s?lect2/1/1sub1/1sub1sub1/"),
                ("--exclude", "**"),
            ],
            [(), ("1sub1sub1",), ("1sub1sub1", "1sub1sub1_file.txt")],
        )

    def test_glob(self):
        """Test globbing expression"""
        self.ParseTest(
            [
                ("--exclude", "**[3-5]"),
                ("--include", "testfiles/select/1"),
                ("--exclude", "**"),
            ],
            [
                (),
                ("1",),
                ("1", "1"),
                ("1", "1", "1"),
                ("1", "1", "2"),
                ("1", "2"),
                ("1", "2", "1"),
                ("1", "2", "2"),
            ],
        )
        self.ParseTest(
            [("--include", "testfiles/select**/2"), ("--exclude", "**")],
            [
                (),
                ("1",),
                ("1", "1"),
                ("1", "1", "2"),
                ("1", "2"),
                ("1", "2", "1"),
                ("1", "2", "2"),
                ("1", "2", "3"),
                ("1", "3"),
                ("1", "3", "2"),
                ("2",),
                ("2", "1"),
                ("2", "1", "1"),
                ("2", "1", "2"),
                ("2", "1", "3"),
                ("2", "2"),
                ("2", "2", "1"),
                ("2", "2", "2"),
                ("2", "2", "3"),
                ("2", "3"),
                ("2", "3", "1"),
                ("2", "3", "2"),
                ("2", "3", "3"),
                ("3",),
                ("3", "1"),
                ("3", "1", "2"),
                ("3", "2"),
                ("3", "2", "1"),
                ("3", "2", "2"),
                ("3", "2", "3"),
                ("3", "3"),
                ("3", "3", "2"),
            ],
        )

    def test_filelist2(self):
        """Filelist glob test similar to above testGlob"""
        self.ParseTest(
            [("--exclude-filelist", "asoeuth")],
            [
                (),
                ("1",),
                ("1", "1"),
                ("1", "1", "1"),
                ("1", "1", "2"),
                ("1", "2"),
                ("1", "2", "1"),
                ("1", "2", "2"),
            ],
            [
                """
**[3-5]
+ testfiles/select/1
**
"""
            ],
        )
        self.ParseTest(
            [("--include-filelist", "file")],
            [
                (),
                ("1",),
                ("1", "1"),
                ("1", "1", "2"),
                ("1", "2"),
                ("1", "2", "1"),
                ("1", "2", "2"),
                ("1", "2", "3"),
                ("1", "3"),
                ("1", "3", "2"),
                ("2",),
                ("2", "1"),
                ("2", "1", "1"),
                ("2", "1", "2"),
                ("2", "1", "3"),
                ("2", "2"),
                ("2", "2", "1"),
                ("2", "2", "2"),
                ("2", "2", "3"),
                ("2", "3"),
                ("2", "3", "1"),
                ("2", "3", "2"),
                ("2", "3", "3"),
                ("3",),
                ("3", "1"),
                ("3", "1", "2"),
                ("3", "2"),
                ("3", "2", "1"),
                ("3", "2", "2"),
                ("3", "2", "3"),
                ("3", "3"),
                ("3", "3", "2"),
            ],
            [
                """
testfiles/select**/2
- **
"""
            ],
        )

    def test_glob2(self):
        """Test more globbing functions"""
        self.ParseTest(
            [("--include", "testfiles/select/*foo*/p*"), ("--exclude", "**")],
            [(), ("efools",), ("efools", "ping"), ("foobar",), ("foobar", "pong")],
        )
        self.ParseTest(
            [
                ("--exclude", "testfiles/select/1/1/*"),
                ("--exclude", "testfiles/select/1/2/**"),
                ("--exclude", "testfiles/select/1/3**"),
                ("--include", "testfiles/select/1"),
                ("--exclude", "**"),
            ],
            [(), ("1",), ("1", "1"), ("1", "2")],
        )

    def test_glob3(self):
        """regression test for bug 25230"""
        self.ParseTest(
            [
                ("--include", "testfiles/select/**1"),
                ("--include", "testfiles/select/**2"),
                ("--exclude", "**"),
            ],
            [
                (),
                ("1",),
                ("1", "1"),
                ("1", "1", "1"),
                ("1", "1", "2"),
                ("1", "1", "3"),
                ("1", "2"),
                ("1", "2", "1"),
                ("1", "2", "2"),
                ("1", "2", "3"),
                ("1", "3"),
                ("1", "3", "1"),
                ("1", "3", "2"),
                ("1", "3", "3"),
                ("2",),
                ("2", "1"),
                ("2", "1", "1"),
                ("2", "1", "2"),
                ("2", "1", "3"),
                ("2", "2"),
                ("2", "2", "1"),
                ("2", "2", "2"),
                ("2", "2", "3"),
                ("2", "3"),
                ("2", "3", "1"),
                ("2", "3", "2"),
                ("2", "3", "3"),
                ("3",),
                ("3", "1"),
                ("3", "1", "1"),
                ("3", "1", "2"),
                ("3", "1", "3"),
                ("3", "2"),
                ("3", "2", "1"),
                ("3", "2", "2"),
                ("3", "2", "3"),
                ("3", "3"),
                ("3", "3", "1"),
                ("3", "3", "2"),
            ],
        )

    def test_alternate_root(self):
        """Test select with different root"""
        self.root = Path("testfiles/select/1")
        self.ParseTest(
            [("--exclude", "testfiles/select/1/[23]")],
            [(), ("1",), ("1", "1"), ("1", "2"), ("1", "3")],
        )

        self.root = Path("/")
        self.ParseTest(
            [("--exclude", "/tmp/*"), ("--include", "/tmp"), ("--exclude", "/")],
            [(), ("tmp",)],
        )

    def test_exclude_after_scan(self):
        """Test select with an exclude after a pattern that would return a scan for that file"""
        self.root = Path("testfiles/select2/3")
        self.ParseTest(
            [
                ("--include", "testfiles/select2/3/**file.txt"),
                ("--exclude", "testfiles/select2/3/3sub2"),
                ("--include", "testfiles/select2/3/3sub1"),
                ("--exclude", "**"),
            ],
            [
                (),
                ("3sub1",),
                ("3sub1", "3sub1sub1"),
                ("3sub1", "3sub1sub2"),
                ("3sub1", "3sub1sub3"),
                ("3sub3",),
                ("3sub3", "3sub3sub2"),
                ("3sub3", "3sub3sub2", "3sub3sub2_file.txt"),
            ],
        )

    def test_include_exclude_basic(self):
        """Test functional test test_include_exclude_basic as a unittest"""
        self.root = Path("testfiles/select2")
        self.ParseTest(
            [
                ("--include", "testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt"),
                ("--exclude", "testfiles/select2/3/3sub3/3sub3sub2"),
                ("--include", "testfiles/select2/3/3sub2/3sub2sub2"),
                ("--include", "testfiles/select2/3/3sub3"),
                ("--exclude", "testfiles/select2/3/3sub1"),
                ("--exclude", "testfiles/select2/2/2sub1/2sub1sub3"),
                ("--exclude", "testfiles/select2/2/2sub1/2sub1sub2"),
                ("--include", "testfiles/select2/2/2sub1"),
                ("--exclude", "testfiles/select2/1/1sub3/1sub3sub2"),
                ("--exclude", "testfiles/select2/1/1sub3/1sub3sub1"),
                ("--exclude", "testfiles/select2/1/1sub2/1sub2sub3"),
                ("--include", "testfiles/select2/1/1sub2/1sub2sub1"),
                ("--exclude", "testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt"),
                ("--exclude", "testfiles/select2/1/1sub1/1sub1sub2"),
                ("--exclude", "testfiles/select2/1/1sub2"),
                ("--include", "testfiles/select2/1.py"),
                ("--include", "testfiles/select2/3"),
                ("--include", "testfiles/select2/1"),
                ("--exclude", "testfiles/select2/**"),
            ],
            self.expected_restored_tree,
        )

    def test_globbing_replacement(self):
        """Test functional test test_globbing_replacement as a unittest"""
        self.root = Path("testfiles/select2")
        self.ParseTest(
            [
                ("--include", "testfiles/select2/**/3sub3sub2/3sub3su?2_file.txt"),
                ("--exclude", "testfiles/select2/*/3s*1"),
                ("--exclude", "testfiles/select2/**/2sub1sub3"),
                ("--exclude", "ignorecase:testfiles/select2/2/2sub1/2Sub1Sub2"),
                ("--include", "ignorecase:testfiles/sel[w,u,e,q]ct2/2/2S?b1"),
                ("--exclude", "testfiles/select2/1/1sub3/1s[w,u,p,q]b3sub2"),
                ("--exclude", "testfiles/select2/1/1sub[1-4]/1sub3sub1"),
                ("--include", "testfiles/select2/1/1sub2/1sub2sub1"),
                ("--exclude", "testfiles/select2/1/1sub1/1sub1sub3/1su?1sub3_file.txt"),
                ("--exclude", "testfiles/select2/1/1*1/1sub1sub2"),
                ("--exclude", "testfiles/select2/1/1sub2"),
                ("--include", "testfiles/select[2-4]/*.py"),
                ("--include", "testfiles/*2/3"),
                ("--include", "**/select2/1"),
                ("--exclude", "testfiles/select2/**"),
            ],
            self.expected_restored_tree,
        )

    def test_globbing_replacement_filter_ignorecase(self):
        """Test functional test test_globbing_replacement as a unittest - an
        alternate implementation of the above test which uses --filter-*case
        instead of the ignorecase: prefix.
        """
        self.root = Path("testfiles/select2")
        self.ParseTest(
            [
                ("--include", "testfiles/select2/**/3sub3sub2/3sub3su?2_file.txt"),
                ("--exclude", "testfiles/select2/*/3s*1"),
                ("--exclude", "testfiles/select2/**/2sub1sub3"),
                ("--filter-ignorecase", None),
                ("--exclude", "testfiles/select2/2/2sub1/2Sub1Sub2"),
                ("--include", "testfiles/sel[w,u,e,q]ct2/2/2S?b1"),
                ("--filter-strictcase", None),
                ("--exclude", "testfiles/select2/1/1sub3/1s[w,u,p,q]b3sub2"),
                ("--exclude", "testfiles/select2/1/1sub[1-4]/1sub3sub1"),
                ("--include", "testfiles/select2/1/1sub2/1sub2sub1"),
                ("--exclude", "testfiles/select2/1/1sub1/1sub1sub3/1su?1sub3_file.txt"),
                ("--exclude", "testfiles/select2/1/1*1/1sub1sub2"),
                ("--exclude", "testfiles/select2/1/1sub2"),
                ("--include", "testfiles/select[2-4]/*.py"),
                ("--include", "testfiles/*2/3"),
                ("--include", "**/select2/1"),
                ("--exclude", "testfiles/select2/**"),
            ],
            self.expected_restored_tree,
        )

    def test_select_mode(self):
        """Test seletion function mode switching with --filter-* options"""
        self.Select = Select(Path("testfiles/select"))
        self.Select.ParseArgs(
            [
                ("--include", "testfiles/select/1"),
                ("--filter-literal", None),
                ("--include", "testfiles/select/2"),
                ("--filter-regexp", None),
                ("--include", "testfiles/select/3"),
                ("--filter-globbing", None),
                ("--filter-ignorecase", None),
                ("--include", "testfiles/select/1"),
                ("--filter-literal", None),
                ("--include", "testfiles/select/2"),
                ("--filter-regexp", None),
                ("--include", "testfiles/select/3"),
                ("--filter-globbing", None),
                ("--filter-strictcase", None),
                ("--exclude", "testfiles/select"),
            ],
            [],
        )
        assert self.Select.selection_functions[0].name.lower().startswith("shell glob include case")
        assert self.Select.selection_functions[1].name.lower().startswith("literal string include case")
        assert self.Select.selection_functions[2].name.lower().startswith("regular expression include case")
        assert self.Select.selection_functions[3].name.lower().startswith("shell glob include no-case")
        assert self.Select.selection_functions[4].name.lower().startswith("literal string include no-case")
        assert self.Select.selection_functions[5].name.lower().startswith("regular expression include no-case")
        assert self.Select.selection_functions[6].name.lower().startswith("shell glob exclude case")

    @unittest.skipUnless(platform.platform().startswith("Linux"), "Skip on non-Linux systems")
    def _paths_non_globbing(self):
        """Test functional test _paths_non_globbing as a unittest"""
        self.root = Path("testfiles/select-unicode")
        self.ParseTest(
            [
                (
                    "--exclude",
                    "testfiles/select-unicode/прыклад/пример/例/Παράδειγμα/उदाहरण.txt",
                ),
                (
                    "--exclude",
                    "testfiles/select-unicode/прыклад/пример/例/Παράδειγμα/דוגמא.txt",
                ),
                ("--exclude", "testfiles/select-unicode/прыклад/пример/例/მაგალითი/"),
                ("--include", "testfiles/select-unicode/прыклад/пример/例/"),
                ("--exclude", "testfiles/select-unicode/прыклад/пример/"),
                ("--include", "testfiles/select-unicode/прыклад/"),
                ("--include", "testfiles/select-unicode/օրինակ.txt"),
                ("--exclude", "testfiles/select-unicode/**"),
            ],
            [
                (),
                ("прыклад",),
                ("прыклад", "пример"),
                ("прыклад", "пример", "例"),
                ("прыклад", "пример", "例", "Παράδειγμα"),
                ("прыклад", "пример", "例", "Παράδειγμα", "ઉદાહરણ.log"),
                ("прыклад", "উদাহরণ"),
                ("օրինակ.txt",),
            ],
        )


class TestGlobGetSf(UnitTestCase):
    """Test glob parsing of the test_glob_get_sf function. Indirectly test behaviour of glob_to_re."""

    def glob_tester(self, path, glob_string, include_exclude, root_path, ignore_case):
        """Takes a path, glob string and include_exclude value (1 = include, 0 = exclude) and returns the output
        of the selection function.
        None - means the test has nothing to say about the related file
        0 - the file is excluded by the test
        1 - the file is included
        2 - the test says the file (must be directory) should be scanned"""
        self.unpack_testfiles()
        self.root = Path(root_path)
        self.select = Select(self.root)
        selection_function = self.select.glob_get_sf(glob_string, include_exclude, ignore_case)
        path = Path(path)
        return selection_function(path)

    def include_glob_tester(self, path, glob_string, root_path="/", ignore_case=False):
        return self.glob_tester(path, glob_string, 1, root_path, ignore_case)

    def exclude_glob_tester(self, path, glob_string, root_path="/", ignore_case=False):
        return self.glob_tester(path, glob_string, 0, root_path, ignore_case)

    def test_glob_get_sf_exclude(self):
        """Test simple exclude."""
        self.assertEqual(self.exclude_glob_tester("/testfiles/select2/3", "/testfiles/select2"), 0)
        self.assertEqual(self.exclude_glob_tester("/testfiles/.git", "/testfiles"), 0)

    def test_glob_get_sf_exclude_root(self):
        """Test simple exclude with / as the glob."""
        self.assertEqual(self.exclude_glob_tester("/.git", "/"), 0)
        self.assertEqual(self.exclude_glob_tester("/testfile", "/"), 0)

    def test_glob_get_sf_2(self):
        """Test same behaviour as the functional test test_globbing_replacement."""
        self.assertEqual(
            self.include_glob_tester(
                "/testfiles/select2/3/3sub3/3sub3sub2/3sub3sub2_file.txt",
                "/testfiles/select2/**/3sub3sub2/3sub3su?2_file.txt",
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester("/testfiles/select2/3/3sub1", "/testfiles/select2/*/3s*1"),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "/testfiles/select2/2/2sub1/2sub1sub3",
                "/testfiles/select2/**/2sub1sub3",
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester("/testfiles/select2/2/2sub1", "/testfiles/sel[w,u,e,q]ct2/2/2s?b1"),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "/testfiles/select2/1/1sub3/1sub3sub2",
                "/testfiles/select2/1/1sub3/1s[w,u,p,q]b3sub2",
            ),
            1,
        )
        self.assertEqual(
            self.exclude_glob_tester(
                "/testfiles/select2/1/1sub3/1sub3sub1",
                "/testfiles/select2/1/1sub[1-4]/1sub3sub1",
            ),
            0,
        )
        self.assertEqual(
            self.include_glob_tester(
                "/testfiles/select2/1/1sub2/1sub2sub1",
                "/testfiles/select2/*/1sub2/1s[w,u,p,q]b2sub1",
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "/testfiles/select2/1/1sub1/1sub1sub3/1sub1sub3_file.txt",
                "/testfiles/select2/1/1sub1/1sub1sub3/1su?1sub3_file.txt",
            ),
            1,
        )
        self.assertEqual(
            self.exclude_glob_tester(
                "/testfiles/select2/1/1sub1/1sub1sub2",
                "/testfiles/select2/1/1*1/1sub1sub2",
            ),
            0,
        )
        self.assertEqual(
            self.include_glob_tester("/testfiles/select2/1/1sub2", "/testfiles/select2/1/1sub2"),
            1,
        )
        self.assertEqual(
            self.include_glob_tester("/testfiles/select2/1.py", "/testfiles/select[2-4]/*.py"),
            1,
        )
        self.assertEqual(self.exclude_glob_tester("/testfiles/select2/3", "/testfiles/*2/3"), 0)
        self.assertEqual(self.include_glob_tester("/testfiles/select2/1", "**/select2/1"), 1)

    def test_glob_get_sf_negative_square_brackets_specified(self):
        """Test negative square bracket (specified) [!a,b,c] replacement in get_normal_sf."""
        # As in a normal shell, [!...] expands to any single character but those specified
        self.assertEqual(self.include_glob_tester("/test/hello1.txt", "/test/hello[!2,3,4].txt"), 1)
        self.assertEqual(self.include_glob_tester("/test/hello.txt", "/t[!w,f,h]st/hello.txt"), 1)
        self.assertEqual(
            self.exclude_glob_tester("/long/example/path/hello.txt", "/lon[!w,e,f]/e[!p]ample/path/hello.txt"),
            0,
        )
        self.assertEqual(
            self.include_glob_tester("/test/hello1.txt", "/test/hello[!2,1,3,4].txt"),
            None,
        )
        self.assertEqual(self.include_glob_tester("/test/hello.txt", "/t[!e,f,h]st/hello.txt"), None)
        self.assertEqual(
            self.exclude_glob_tester(
                "/long/example/path/hello.txt",
                "/lon[!w,e,g,f]/e[!p,x]ample/path/hello.txt",
            ),
            None,
        )

    def test_glob_get_sf_negative_square_brackets_range(self):
        """Test negative square bracket (range) [!a,b,c] replacement in get_normal_sf."""
        # As in a normal shell, [!1-5] or [!a-f] expands to any single character not in the range specified
        self.assertEqual(self.include_glob_tester("/test/hello1.txt", "/test/hello[!2-4].txt"), 1)
        self.assertEqual(self.include_glob_tester("/test/hello.txt", "/t[!f-h]st/hello.txt"), 1)
        self.assertEqual(
            self.exclude_glob_tester(
                "/long/example/path/hello.txt",
                "/lon[!w,e,f]/e[!p-s]ample/path/hello.txt",
            ),
            0,
        )
        self.assertEqual(self.include_glob_tester("/test/hello1.txt", "/test/hello[!1-4].txt"), None)
        self.assertEqual(self.include_glob_tester("/test/hello.txt", "/t[!b-h]st/hello.txt"), None)
        self.assertEqual(
            self.exclude_glob_tester("/long/example/path/hello.txt", "/lon[!f-p]/e[!p]ample/path/hello.txt"),
            None,
        )

    def test_glob_get_sf_2_ignorecase(self):
        """Test same behaviour as the functional test test_globbing_replacement, ignorecase tests."""
        self.assertEqual(
            self.include_glob_tester(
                "testfiles/select2/2/2sub1",
                "testfiles/sel[w,u,e,q]ct2/2/2S?b1",
                "testfiles/select2",
                ignore_case=True,
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "testfiles/select2/2/2sub1/2sub1sub2",
                "testfiles/select2/2/2sub1/2Sub1Sub2",
                "testfiles/select2",
                ignore_case=True,
            ),
            1,
        )

    def test_glob_get_sf_3_double_asterisks_dirs_to_scan(self):
        """Test double asterisk (**) replacement in glob_get_sf with directories that should be scanned"""
        # The new special pattern, **, expands to any string of characters whether or not it contains "/".
        self.assertEqual(self.include_glob_tester("/long/example/path", "/**/hello.txt"), 2)

    def test_glob_get_sf_3_ignorecase(self):
        """Test ignorecase in glob_get_sf"""
        # If glob_get_sf() is invoked with ignore_case=True then any character
        # in the string can be replaced with an upper- or lowercase version of
        # itself (parsing the ignorecase: prefix is tested elsewhere).
        self.assertEqual(
            self.include_glob_tester(
                "testfiles/select2/2",
                "testfiles/select2/2",
                "testfiles/select2",
                ignore_case=True,
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "testfiles/select2/2",
                "testFiles/Select2/2",
                "testfiles/select2",
                ignore_case=True,
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "tEstfiles/seLect2/2",
                "testFiles/Select2/2",
                "testfiles/select2",
                ignore_case=True,
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "TEstfiles/SeLect2/2",
                "t?stFiles/S*ect2/2",
                "testfiles/select2",
                ignore_case=True,
            ),
            1,
        )
        self.assertEqual(
            self.include_glob_tester(
                "TEstfiles/SeLect2/2",
                "t?stFil**ect2/2",
                "testfiles/select2",
                ignore_case=True,
            ),
            1,
        )
        self.assertEqual(
            self.exclude_glob_tester(
                "TEstfiles/SeLect2/2",
                "t?stFiles/S*ect2/2",
                "testfiles/select2",
                ignore_case=True,
            ),
            0,
        )
        self.assertEqual(
            self.exclude_glob_tester(
                "TEstFiles/SeLect2/2",
                "t?stFile**ect2/2",
                "testfiles/select2",
                ignore_case=True,
            ),
            0,
        )

    def test_glob_dirs_to_scan(self):
        """Test parent directories are marked as needing to be scanned"""
        with patch("duplicity.path.Path.isdir") as mock_isdir:
            mock_isdir.return_value = True
            self.assertEqual(self.glob_tester("parent", "parent/hello.txt", 1, "parent", False), 2)

    def test_glob_dirs_to_scan_glob(self):
        """Test parent directories are marked as needing to be scanned - globs"""
        with patch("duplicity.path.Path.isdir") as mock_isdir:
            mock_isdir.return_value = True
            self.assertEqual(
                self.glob_tester("testfiles/select/1", "*/select/1/1", 1, "testfiles/select", False),
                2,
            )
            self.assertEqual(
                self.glob_tester(
                    "testfiles/select/1/2",
                    "*/select/1/2/1",
                    1,
                    "testfiles/select",
                    False,
                ),
                2,
            )
            self.assertEqual(self.glob_tester("parent", "parent/hel?o.txt", 1, "parent", False), 2)
            self.assertEqual(
                self.glob_tester(
                    "test/parent/folder",
                    "test/par*t/folder/hello.txt",
                    1,
                    "test",
                    False,
                ),
                2,
            )
            self.assertEqual(
                self.glob_tester("testfiles/select/1/1", "**/1/2/1", 1, "testfiles", False),
                2,
            )
            self.assertEqual(
                self.glob_tester(
                    "testfiles/select2/3/3sub2",
                    "testfiles/select2/3/**file.txt",
                    1,
                    "testfiles",
                    False,
                ),
                2,
            )
            self.assertEqual(
                self.glob_tester("testfiles/select/1/2", "*/select/1/2/1", 1, "testfiles", False),
                2,
            )
            self.assertEqual(
                self.glob_tester("testfiles/select/1", "testfiles/select**/2", 1, "testfiles", False),
                2,
            )
            self.assertEqual(
                self.glob_tester(
                    "testfiles/select/efools",
                    "testfiles/select/*foo*/p*",
                    1,
                    "testfiles",
                    False,
                ),
                2,
            )
            self.assertEqual(
                self.glob_tester("testfiles/select/3", "testfiles/select/**2", 1, "testfiles", False),
                2,
            )
            self.assertEqual(
                self.glob_tester(
                    "testfiles/select2/1/1sub1/1sub1sub2",
                    "testfiles/select2/**/3sub3sub2/3sub3su?2_file.txt",
                    1,
                    "testfiles",
                    False,
                ),
                2,
            )
            self.assertEqual(
                self.glob_tester("testfiles/select/1", "*/select/1/1", 1, "testfiles", False),
                2,
            )


if __name__ == "__main__":
    unittest.main()
