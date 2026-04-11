from __future__ import annotations

import contextlib
import os
import sys

__all__ = ("chdir",)

if sys.version_info < (3, 11):

    @contextlib.contextmanager
    def chdir(path):
        old_cwd = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(old_cwd)

else:
    from contextlib import chdir
