#!/usr/bin/env python3

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

import os
import sys
import traceback
import unittest

_top_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, _top_dir)

try:
    from testing.manual import test_config
except ImportError as e:
    # It's OK to not have copied config.py.tmpl over yet, if user is just
    # calling us directly to test a specific backend.  If they aren't, we'll
    # fail later when config.blah is used.
    traceback.print_exc()
    pass
from testing.unit.test_backend_instance import BackendInstanceBase
import duplicity.backend

# undo the overrides support that our testing framework adds
sys.path = [x for x in sys.path if "/overrides" not in x]
os.environ["PATH"] = ":".join([x for x in os.environ["PATH"].split(":") if "/overrides" not in x])
os.environ["PYTHONPATH"] = ":".join([x for x in os.environ["PYTHONPATH"].split(":") if "/overrides" not in x])


class ManualBackendBase(BackendInstanceBase):
    url_string = None
    password = None

    def setUp(self):
        super().setUp()
        self.set_config("num_retries", 1)
        self.set_config("ssl_no_check_certificate", True)
        self.setBackendInfo()
        if self.password is not None:
            self.set_environ("FTP_PASSWORD", self.password)
        if self.url_string is not None:
            self.backend = duplicity.backend.get_backend_object(self.url_string)

        # Clear out backend first
        if self.backend is not None:
            if hasattr(self.backend, "_delete_list"):
                self.backend._delete_list(self.backend._list())
            else:
                for x in self.backend._list():
                    self.backend._delete(x)

    def setBackendInfo(self):
        pass


class sshParamikoTest(ManualBackendBase):
    def setBackendInfo(self):
        from duplicity.backends import ssh_paramiko_backend

        duplicity.backend._backends["ssh"] = ssh_paramiko_backend.SSHParamikoBackend
        self.url_string = test_config.ssh_url
        self.password = test_config.ssh_password


class sshParamikoScpTest(ManualBackendBase):
    def setBackendInfo(self):
        from duplicity.backends import ssh_paramiko_backend

        duplicity.backend._backends["scp"] = ssh_paramiko_backend.SSHParamikoBackend
        self.url_string = test_config.ssh_url
        self.password = test_config.ssh_password


class sshPexpectTest(ManualBackendBase):
    def setBackendInfo(self):
        from duplicity.backends import ssh_pexpect_backend

        duplicity.backend._backends["ssh"] = ssh_pexpect_backend.SSHPExpectBackend
        self.url_string = test_config.ssh_url
        self.password = test_config.ssh_password


class sshPexpectScpTest(ManualBackendBase):
    def setBackendInfo(self):
        from duplicity.backends import ssh_pexpect_backend

        duplicity.backend._backends["scp"] = ssh_pexpect_backend.SSHPExpectBackend
        self.url_string = test_config.ssh_url
        self.password = test_config.ssh_password


class ftpTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.ftp_url
        self.password = test_config.ftp_password


class ftpsTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.ftp_url.replace("ftp://", "ftps://") if test_config.ftp_url else None
        self.password = test_config.ftp_password


class gsTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.gs_url
        self.set_environ("GS_ACCESS_KEY_ID", test_config.gs_access_key)
        self.set_environ("GS_SECRET_ACCESS_KEY", test_config.gs_secret_key)


# class s3SingleTest(ManualBackendBase):
#     def setBackendInfo(self):
#         from duplicity.backends import _boto_single
#         duplicity.backend._backends['s3+http'] = _boto_single.BotoBackend
#         self.set_config('s3_use_new_style', True)
#         self.set_environ("AWS_ACCESS_KEY_ID", test_config.s3_access_key)
#         self.set_environ("AWS_SECRET_ACCESS_KEY", test_config.s3_secret_key)
#         self.url_string = test_config.s3_url
#
#
# class s3MultiTest(ManualBackendBase):
#     def setBackendInfo(self):
#         from duplicity.backends import _boto_multi
#         duplicity.backend._backends['s3+http'] = _boto_multi.BotoBackend
#         self.set_config('s3_use_new_style', True)
#         self.set_environ("AWS_ACCESS_KEY_ID", test_config.s3_access_key)
#         self.set_environ("AWS_SECRET_ACCESS_KEY", test_config.s3_secret_key)
#         self.url_string = test_config.s3_url
#
#
class cfCloudfilesTest(ManualBackendBase):
    def setBackendInfo(self):
        from duplicity.backends import _cf_cloudfiles

        duplicity.backend._backends["cf+http"] = _cf_cloudfiles.CloudFilesBackend
        self.set_environ("CLOUDFILES_USERNAME", test_config.cf_username)
        self.set_environ("CLOUDFILES_APIKEY", test_config.cf_api_key)
        self.url_string = test_config.cf_url


class cfPyraxTest(ManualBackendBase):
    def setBackendInfo(self):
        from duplicity.backends import _cf_pyrax

        duplicity.backend._backends["cf+http"] = _cf_pyrax.PyraxBackend
        self.set_environ("CLOUDFILES_USERNAME", test_config.cf_username)
        self.set_environ("CLOUDFILES_APIKEY", test_config.cf_api_key)
        self.url_string = test_config.cf_url


class swiftTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.swift_url
        self.set_environ("SWIFT_USERNAME", test_config.swift_username)
        self.set_environ("SWIFT_PASSWORD", test_config.swift_password)
        self.set_environ("SWIFT_TENANTNAME", test_config.swift_tenant)
        # Assumes you're just using the same storage as your cloudfiles config above
        self.set_environ("SWIFT_AUTHURL", "https://identity.api.rackspacecloud.com/v2.0/")
        self.set_environ("SWIFT_AUTHVERSION", "2")


class megaTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.mega_url
        self.password = test_config.mega_password


class webdavTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.webdav_url
        self.password = test_config.webdav_password


class webdavsTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.webdavs_url
        self.password = test_config.webdavs_password
        self.set_config("ssl_no_check_certificate", True)


class gdocsTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.gdocs_url
        self.password = test_config.gdocs_password


class dpbxTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.dpbx_url


class imapTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = test_config.imap_url
        self.set_environ("IMAP_PASSWORD", test_config.imap_password)
        self.set_config("imap_mailbox", "deja-dup-testing")


class gioSSHTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = f"gio+{test_config.ssh_url}" if test_config.ssh_url else None
        self.password = test_config.ssh_password


class gioFTPTest(ManualBackendBase):
    def setBackendInfo(self):
        self.url_string = f"gio+{test_config.ftp_url}" if test_config.ftp_url else None
        self.password = test_config.ftp_password


if __name__ == "__main__":
    defaultTest = None
    if len(sys.argv) > 1:

        class manualTest(ManualBackendBase):
            def setBackendInfo(self):
                self.url_string = sys.argv[1]

        defaultTest = "manualTest"
    unittest.main(argv=[sys.argv[0]], defaultTest=defaultTest)
