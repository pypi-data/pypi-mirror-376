from __future__ import annotations

from wexample_wex_core.workdir.code_base_workdir import CodeBaseWorkdir


class JavascriptWorkdir(CodeBaseWorkdir):
    def get_dependencies(self) -> list[str]:
        # TODO search in package.json
        return []
