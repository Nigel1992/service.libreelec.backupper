#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import base64
import shlex
import subprocess
import sys

class CLISFTPClient:
    """A small SFTP-like client backed by ssh/scp for environments where
    paramiko cannot be imported (for example Kodi's addon subinterpreters)."""

    def __init__(self, host, port, username, key_file, passphrase=None):
        self.host = host
        self.port = int(port or 22)
        self.username = username or ""
        self.key_file = key_file or ""
        self.passphrase = passphrase or ""
        self.cwd = "."
        self._base_ssh = ["ssh", "-i", self.key_file, "-p", str(self.port),
                          "-o", "StrictHostKeyChecking=no",
                          "-o", "UserKnownHostsFile=/dev/null",
                          "-o", "BatchMode=yes"]
        self._base_scp = ["scp", "-i", self.key_file, "-P", str(self.port),
                          "-o", "StrictHostKeyChecking=no",
                          "-o", "UserKnownHostsFile=/dev/null",
                          "-o", "BatchMode=yes"]

    def _target(self):
        if self.username:
            return "%s@%s" % (self.username, self.host)
        return self.host

    def _full(self, path):
        if not path:
            return self.cwd or "."
        if path.startswith("/"):
            return path
        if self.cwd and self.cwd not in (".", ""):
            return self.cwd.rstrip("/") + "/" + path
        return path

    def _run_ssh(self, remote_cmd):
        cmd = list(self._base_ssh) + [self._target(), remote_cmd]
        return subprocess.run(cmd, capture_output=True, text=True)

    def _run_remote_python(self, code, *args):
        b64 = base64.b64encode(code.encode()).decode()
        remote = "python3 -c 'import base64,sys;exec(base64.b64decode(sys.argv[1]))' %s" % b64
        for a in args:
            remote += " " + shlex.quote(str(a))
        cmd = list(self._base_ssh) + [self._target(), remote]
        return subprocess.run(cmd, capture_output=True, text=True)

    def chdir(self, path):
        if path:
            self.cwd = path

    def getcwd(self):
        return self.cwd

    def listdir(self, path="."):
        target = self._full(path)
        code = "import os, json, sys; print(json.dumps(os.listdir(sys.argv[2])))"
        r = self._run_remote_python(code, target)
        if r.returncode != 0:
            raise IOError(r.stderr or "listdir failed")
        try:
            return json.loads(r.stdout.strip() or "[]")
        except Exception:
            return []

    def stat(self, path):
        target = self._full(path)
        code = ("import os, json, sys; "
                "st = os.stat(sys.argv[2]); "
                "print(json.dumps({'size': st.st_size, 'mtime': st.st_mtime, 'mode': st.st_mode}))")
        r = self._run_remote_python(code, target)
        if r.returncode != 0:
            raise IOError(r.stderr or "stat failed")
        data = json.loads(r.stdout.strip())
        # Minimal stat-like object
        class _Stat:
            pass
        st = _Stat()
        st.st_size = data.get("size", 0)
        st.st_mtime = data.get("mtime", 0)
        st.st_mode = data.get("mode", 0)
        return st

    def remove(self, path):
        target = self._full(path)
        code = "import os, sys; os.remove(sys.argv[2])"
        r = self._run_remote_python(code, target)
        if r.returncode != 0:
            raise IOError(r.stderr or "remove failed")
        return None

    def put(self, local_path, remote_path, callback=None):
        target = self._full(remote_path)
        remote = "%s:%s" % (self._target(), target)
        cmd = list(self._base_scp) + [local_path, remote]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise IOError(r.stderr or "upload failed")
        return None

    def get(self, remote_path, local_path):
        target = self._full(remote_path)
        remote = "%s:%s" % (self._target(), target)
        cmd = list(self._base_scp) + [remote, local_path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise IOError(r.stderr or "download failed")
        return None

    def close(self):
        return None

    def get_channel(self):
        class _Channel:
            def get_transport(self):
                class _Transport:
                    def close(self):
                        return None
                return _Transport()
        return _Channel()

    # Compatibility helpers
    def nlst(self):
        return self.listdir(".")

    def statvfs(self, path="."):
        class _SV:
            f_blocks = 0
            f_bfree = 0
            f_frsize = 1
            f_bsize = 1
        return _SV()
