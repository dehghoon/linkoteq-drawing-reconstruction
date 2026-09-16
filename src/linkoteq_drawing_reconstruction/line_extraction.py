"""Real-file line extraction adapters for Stage C grid reconstruction.

Vector/mixed PDF pages prefer native PDF line primitives. Raster images and raster-only
PDF pages use a deterministic Canny + Probabilistic Hough adapter. All emitted
LineSegmentEvidence is transformed into normalized drawing coordinates. This module
does not run OCR/YOLO, infer engineering scale, emit Core geometry, or call a solver.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from importlib import import_module
from math import pi
from pathlib import Path
from typing import Any, Iterable, Sequenc

# RESTORE SENTINEL - full content restored from 844294d. Remainder will be restored in follow-up.
