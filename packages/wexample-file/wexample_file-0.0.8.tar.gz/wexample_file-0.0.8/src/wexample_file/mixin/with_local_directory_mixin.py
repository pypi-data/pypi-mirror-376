from __future__ import annotations

from typing import TYPE_CHECKING

from wexample_file.mixin.with_path_mixin import WithPathMixin
from wexample_helpers.decorator.base_class import base_class

if TYPE_CHECKING:
    from wexample_file.common.local_directory import LocalDirectory


@base_class
class WithLocalDirectoryMixin(WithPathMixin):
    def get_local_directory(self) -> LocalDirectory:
        from wexample_file.common.local_directory import LocalDirectory

        return LocalDirectory(path=self.get_path())
