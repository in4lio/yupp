"""Small build hook for the interpreter-startup codec bootstrap.

All distribution metadata is static in ``pyproject.toml``.  Setuptools' normal
``build_py`` command owns the pure-Python wheel payload, so copying the tracked
bootstrap input into ``build_lib`` puts it at the purelib root and records it
in the wheel's RECORD file.
"""

from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        super().run()
        source = Path(__file__).with_name("yupp.pth")
        self.copy_file(str(source), str(Path(self.build_lib) / source.name))


setup(cmdclass={"build_py": build_py})
