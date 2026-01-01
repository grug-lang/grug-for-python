from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from grug.grug_file import GrugFile


@dataclass
class GrugDir:
    """Represents a directory of grug files and subdirectories."""

    name: str
    files: Dict[str, GrugFile] = field(default_factory=lambda: {})
    dirs: Dict[str, GrugDir] = field(default_factory=lambda: {})
