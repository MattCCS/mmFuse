
import os

from FUSE.backends import mmbackend, osbackend, static
from FUSE.errors import readonly, deny, notreal
from FUSE.fuse_clients.abstract import AbstractReadOnlyFuseClient
from FUSE.fuse_clients.passthough_client import (
    REQUIRED_FOR_MUSIC,
    REQUIRED_FOR_THUMBNAILS,
    REQUIRED_FOR_QUICKLOOK,
    REQUIRED_FOR_FINDER,
)


FAKE_FILE_DESCRIPTOR = 0
FAKE_FOLDER_SIZE = 96
READ_ONLY_FOLDER_MODE = 0o40444
READ_ONLY_FILE_MODE = 0o100444

QUICKLOOK_PROCESSES = {
    "QuickLookSatellite",
    "QuickLookUIService",
    "quicklookd",
}

FINDER_COPY_PASTE = {
    "Finder",
    "DesktopServicesH",
}

THUMBNAILS = {
    "com.apple.quicklook.ThumbnailsAgent",
}

QUICKTIME = {
    "QuickTime Player",
}

PREVIEW = {
    "Preview",
}

ZSH_TAB_COMPLETION = {
    "zsh",
}

ALLOW_ALL = False
ALLOWED = frozenset(["ls", "head"]) | REQUIRED_FOR_MUSIC | FINDER_COPY_PASTE | THUMBNAILS | QUICKTIME | PREVIEW | ZSH_TAB_COMPLETION

ALLOW_AFTER_FINDER_HAS_READ = {
    "QuickLookSatellite",
}


class ReadOnlyFuseClient(AbstractReadOnlyFuseClient):
    def __init__(self, root=None, mediaman=False, filesystem_image_mm_hash=None, filesystem_image=None, service_selector=None, hashes=None):
        if root:
            self.backend = osbackend.ReadOnlyOSBackend(root)
        elif mediaman:
            self.backend = mmbackend.ReadOnlyFlatMMBackend(service_selector=service_selector)
        elif filesystem_image_mm_hash:
            self.backend = mmbackend.ReadOnlyPredefinedMMBackend(filesystem_image_mm_hash=filesystem_image_mm_hash, service_selector=service_selector)
        elif filesystem_image:
            self.backend = mmbackend.ReadOnlyPredefinedMMBackend(filesystem_image=filesystem_image, service_selector=service_selector)
        # elif hashes:
        #     self.backend = mmbackend.ReadOnly
        else:
            self.backend = static.StaticFlatBackend({"a.txt": b"hi", "b.txt": b"ho!", "c.txt": b"how do you do?"})

        self.finder_has_read = set()

    def verify_procname(self, procname, path):
        if path in self.finder_has_read and procname in ALLOW_AFTER_FINDER_HAS_READ:
            print(f"[*] Allowing {procname} on {repr(path)} because Finder has already read (user is actively previewing).")
            return
        if not ALLOW_ALL and procname not in ALLOWED:
            deny()

    def access(self, path, mode):
        if not self.backend.has(path):
            notreal()

    def getattr(self, path, fh=None):
        if not self.backend.has(path):
            notreal()
        if self.backend.is_dir(path):
            return {
                "st_atime": 0,
                "st_ctime": 0,
                "st_mtime": 0,
                "st_nlink": 1,
                "st_uid": 0,  # orig 501
                "st_gid": 0,  # orig 20
                "st_mode": READ_ONLY_FOLDER_MODE,
                "st_size": FAKE_FOLDER_SIZE,
            }
        else:
            return {
                "st_atime": 0,
                "st_ctime": 0,
                "st_mtime": 0,
                "st_nlink": 1,  # 1 hard link
                "st_uid": 0,
                "st_gid": 0,
                "st_mode": READ_ONLY_FILE_MODE,
                "st_size": self.backend.size(path),
            }

    def readdir(self, path, fh):
        if not self.backend.has(path):
            notreal()
        dirents = [".", ".."]
        return dirents + self.backend.list(path)

    def readlink(self, path):
        deny()

    def statfs(self, path):
        stv = os.statvfs(path)
        out = dict((key, getattr(stv, key)) for key in (
            "f_bavail", "f_bfree", "f_blocks", "f_bsize",
            "f_favail", "f_ffree", "f_files", "f_flag",
            "f_frsize", "f_namemax"))
        out["f_flag"] |= os.ST_RDONLY  # read-only
        # out["f_frsize"] = 2**20
        return out

    def open(self, path, flags):
        if not self.backend.has(path):
            notreal()
        return FAKE_FILE_DESCRIPTOR

    def read(self, path, length, offset, fh, procname):
        """
        NOTE: OS will try to read a file created via open().
        """
        print(path, length, offset)
        if procname == "Finder":
            self.finder_has_read.add(path)
        return self.backend.read(path, length, offset)
