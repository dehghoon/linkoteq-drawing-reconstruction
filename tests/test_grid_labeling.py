from linkoteq_drawing_reconstruction.grid_geometry import GridAxisCandidate
from linkoteq_drawing_reconstruction.grid_labeling import BoundingBox2D,OcrLabelEvidence,associate_grid_labels
from linkoteq_drawing_reconstruction.transforms import Point2D


def axis(aid,x1,y1,x2,y2):
    return GridAxisCandidate(aid,"f",Point2D(x1,y1),Point2D(x2,y2),("s",),100.0,1.0,0.0,0.0)

def ocr(eid,text,x,y,conf=0.95):
    return OcrLabelEvidence(eid,"src","p1",text,BoundingBox2D(Point2D(x-1,y-1),Point2D(x+1,y+1)),conf,"fixture-ocr","1.0","grid-bubble")

def test_auto_accepts_clear_near_endpoint_label():
    r=associate_grid_labels((axis("a",0,0,100,0)),(ocr("e1","1",0,0),),max_endpoint_distance=10)
    assert r[0].label=="1"
    assert r[0].status=="auto-accepted"

def test_low_confidence_requires_review():
    r=associate_grid_labels((axis("a",0,0,100,0),)(ocr("e1","A",0,0,0.4),),max_endpoint_distance=10)
    assert r[0].status=="review-required"

def test_competing_nearby_labels_require_review():
    r=associate_grid_labels((axis("a",0,0,100,0),)(ocr("e1","1",1,0),ocr("e2","I",1.1,0)),max_endpoint_distance=10)
    assert r[0].status=="review-required"
    assert r[0].competing_evidence_ids==("e2",)

def test_duplicate_label_across_axes_requires_review():
    axes=(axis("a1",0,0,100,0),axis("a2",0,10,100,10))
    evidence=(ocr("e1","A",0,0),ocr("e2","A",0,10))
    r=associate_grid_labels(axes,evidence,max_endpoint_distance=5)
    assert [x.status for x in r]==["review-required","review-required"]

def test_unmatched_axis requires_review():
    r=associate_grid_labels((axis("a",0,0,100,0),),(ocr("e1","1",50,50),),max_endpoint_distance=5)
    assert r[0].label is None
    assert r[0].status=="review-required"
