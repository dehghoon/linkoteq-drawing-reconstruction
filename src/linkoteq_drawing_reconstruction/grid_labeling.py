"""Importer-private OCR evidence and deterministic grid-axis label association."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha1
from math import hypot
from typing import Literal, Sequence
from .grid_geometry import GridAxisCandidate
from .transforms import Point2D

ReviewStatus = Literal["auto-accepted", "review-required", "rejected"]
class GridLabelingError(ValueError): pass

@dataclass(frozen=True)
class BoundingBox2D:
    min: Point2D
    max: Point2D
    def __post_init__(self):
        if self.min.x > self.max.x or self.min.y > self.max.y:
            raise GridLabelingError("bounding box min must not exceed max")
    @property
    def center(self):
        return Point2D((self.min.x+self.max.x)/2.0,(self.min.y+self.max.y)/2.0)

@dataclass(frozen=True)
class OcrLabelEvidence:
    id: str
    source_id: str
    page_id: str
    text: str
    box: BoundingBox2D
    confidence: float
    engine: str
    engine_version: str
    region_kind: Literal["grid-bubble","grid-label"]="grid-label"
    def __post_init__(self):
        if not self.id.strip() or not self.source_id.strip() or not self.page_id.strip():
            raise GridLabelingError("OCR evidence identity and provenance must be non-empty")
        if not self.text.strip(): raise GridLabelingError("OCR text must be non-empty")
        if not self.engine.strip() or not self.engine_version.strip():
            raise GridLabelingError("OCR engine and version must be preserved")
        if not 0.0 <= self.confidence <= 1.0:
            raise GridLabelingError("OCR confidence must be between 0 and 1")

@dataclass(frozen=True)
class GridLabelAssociation:
    id: str
    axis_id: str
    label_evidence_id: str|None
    label: str|None
    status: ReviewStatus
    distance: float|None
    competing_evidence_ids: tuple[str,...]=()

def _stable_id(prefix,*parts):
    return f"{prefix}-{sha1('|'.join(parts).encode()).hexdigest()[:12]}"
def _distance(a,b): return hypot(a.x-b.x,a.y-b.y)
def _endpoint_distance(axis,evidence):
    c=evidence.box.center
    return min(_distance(c,axis.start),_distance(c,axis.end))

def associate_grid_labels(axes:Sequence[GridAxisCandidate], evidence:Sequence[OcrLabelEvidence], *,
    max_endpoint_distance:float=40.0, ambiguity_ratio:float=1.25,
    min_ocr_confidence:float=0.75)->tuple[GridLabelAssociation,...]:
    """Associate OCR evidence to axes deterministically without changing geometry.

    One OCR observation may label at most one axis. Ambiguity remains review evidence.
    """
    if max_endpoint_distance<=0 or ambiguity_ratio<=1.0 or not 0.0<=min_ocr_confidence<=1.0:
        raise GridLabelingError("invalid grid-label association thresholds")
    if not axes: return ()
    pages={(e.source_id,e.page_id) for e in evidence}
    if len(pages)>1: raise GridLabelingError("OCR evidence must belong to at most one source page")
    if len({a.id for a in axes})!=len(axes): raise GridLabelingError("grid axis ids must be unique")
    if len({e.id for e in evidence})!=len(evidence): raise GridLabelingError("OCR evidence ids must be unique")

    candidates={}
    for axis in axes:
        candidates[axis.id]=sorted(
            ((d,e) for e in evidence if (d:=_endpoint_distance(axis,e))<=max_endpoint_distance),
            key=lambda x:(x[0],x[1].id))
    pairs=sorted(((d,a.id,e.id) for a in axes for d,e in candidates[a.id]),
                 key=lambda x:(x[0],x[1],x[2]))
    assigned={}
    used=set()
    by_id={e.id:e for e in evidence}
    for d,aid,eid in pairs:
        if aid in assigned or eid in used: continue
        assigned[aid]=(d,by_id[eid]); used.add(eid)

    result=[]
    for axis in sorted(axes,key=lambda a:a.id):
        chosen=assigned.get(axis.id)
        if chosen is None:
            result.append(GridLabelAssociation(_stable_id("grid-label",axis.id,"none"),
                axis.id,None,None,"review-required",None))
            continue
        best_d,best=chosen
        competing=tuple(sorted(e.id for d,e in candidates[axis.id]
            if e.id!=best.id and d<=best_d*ambiguity_ratio))
        status="auto-accepted"
        if best.confidence<min_ocr_confidence or competing: status="review-required"
        result.append(GridLabelAssociation(_stable_id("grid-label",axis.id,best.id),
            axis.id,best.id,best.text.strip(),status,best_d,competing))
    counts={}
    for x in result:
        if x.label is not None: counts[x.label]=counts.get(x.label,0)+1
    return tuple(GridLabelAssociation(x.id,x.axis_id,x.label_evidence_id,x.label,
        "review-required" if x.label and counts[x.label]>1 else x.status,
        x.distance,x.competing_evidence_ids) for x in result)
