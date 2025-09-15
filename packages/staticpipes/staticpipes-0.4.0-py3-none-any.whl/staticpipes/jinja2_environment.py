from typing import Optional

import jinja2

from staticpipes.source_directory import SourceDirectory


class Jinja2Environment:

    def __init__(self, autoescape=True, filters: dict = {}):
        self._jinja2_environment: Optional[jinja2.Environment] = None
        self._autoescape = autoescape
        self._filters = filters

    def get(self, source_directory: SourceDirectory) -> jinja2.Environment:
        if not self._jinja2_environment:
            self._jinja2_environment = jinja2.Environment(
                loader=jinja2.FileSystemLoader(source_directory.dir),
                autoescape=self._autoescape,
            )
            for k, v in self._filters.items():
                self._jinja2_environment.filters[k] = v

        return self._jinja2_environment
