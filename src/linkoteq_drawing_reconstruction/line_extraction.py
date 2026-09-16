"""Real-file line extraction adapters for Stage C."""
from dataclasses import dataclass
from hashlib import sha1
from importlib import import_module
from pathlib import Path
from .grid_geometry import LineSegmentEvidence
from .source_normalization import SourcePageMetadata
from .transforms import Affine2D, Point2D

class LineExtractionError(RuntimeError): pass

@dataclass(frozen=True)
class RasterLineSettings:
    canny_threshold1: float=50.0
    canny_threshold2: float=150.0
    hough_rho: float=1.0
    hough_theta_deg: float=1.0
    hough_threshold: int=80
    min_line_length: float=50.0
    max_line_gap: float=10.0
    render_dpi: float=150.0
    def __post_init__(self):
        if not 0 < self.canny_threshold1 < self.canny_threshold2: raise LineExtractionError("Canny thresholds must satisfy 0 < t1 < t2.")
        if self.hough_rho<=0 or self.hough_theta_deg<=0: raise LineExtractionError("Hough rho/theta must be positive.")
        if self.hough_threshold<=0 or self.min_line_length<=0 or self.max_line_gap<0: raise LineExtractionError("Invalid Hough settings.")
        if self.render_dpi<=0: raise LineExtractionError("render_dpi must be positive.")

def _mod(name, label):
    try: return import_module(name)
    except ImportError as e: raise LineExtractionError(f"{label} is required for line extraction.") from e
def _fitz(): return _mod("fitz","PyMuPDF")
def _cv2(): return _mod("cv2","OpenCV")
def _numpy(): return _mod("numpy","NumPy")
def _ordered(a,b): return (a,b) if (a.x,a.y)<=(b.x,b.y) else (b,a)

def _make_evidence(*,source,method,start,end,source_to_normalized,confidence=1.0):
    a,b=_ordered(source_to_normalized.apply(start),source_to_normalized.apply(end))
    if a==b: raise LineExtractionError("A transformed line segment collapsed to zero length.")
    payload=f"{source.source_id}|{source.page_id}|{method}|{a.x:.6f},{a.y:.6f}|{b.x:.6f},{b.y:.6f}".encode()
    return LineSegmentEvidence(id=f"line-{sha1(payload).hexdigest()[:16]}",source_id=source.source_id,page_id=source.page_id,start=a,end=b,method=method,confidence=confidence)

def _dedupe(items):
    return tuple(sorted({x.id:x for x in items}.values(),key=lambda x:(x.start.x,x.start.y,x.end.x,x.end.y,x.id)))

def extract_vector_lines_from_pdf(pdf_path,*,page_index,source,source_to_normalized):
    if page_index!=source.page_index: raise LineExtractionError("page_index must match source metadata.")
    if not source.has_vector_geometry or source.source_space!="vector": raise LineExtractionError("Native PDF vector extraction requires vector source metadata.")
    fitz=_fitz(); doc=fitz.open(str(pdf_path))
    try:
        if page_index<0 or page_index>=len(doc): raise LineExtractionError("PDF page_index is out of range.")
        page=doc[page_index]; r=page.rect
        if abs(float(r.width)-source.width)>1e-6 or abs(float(r.height)-source.height)>1e-6: raise LineExtractionError("PDF page dimensions do not match vector source metadata.")
        out=[]
        for d in page.get_drawings():
            for it in d.get("items",()):
                if it and it[0]=="l":
                    p,q=it[1],it[2]
                    if p.x!=q.x or p.y!=q.y: out.append(_make_evidence(source=source,method="vector",start=Point2D(float(p.x),float(p.y)),end=Point2D(float(q.x),float(q.y)),source_to_normalized=source_to_normalized))
        return _dedupe(out)
    finally: doc.close()

def _hough_lines(frame,settings):
    cv2=_cv2(); np=_numpy()
    if len(frame.shape)==3: gray=cv2.cvtColor(frame,cv2.COLOR_BGRA2GRAY if frame.shape[2]==4 else cv2.COLOR_BGR2GRAY)
    else: gray=frame
    edges=cv2.Canny(gray,settings.canny_threshold1,settings.canny_threshold2)
    lines=cv2.HoughLinesP(edges,settings.hough_rho,np.deg2rad(settings.hough_theta_deg),settings.hough_threshold,minLineLength=settings.min_line_length,maxLineGap=settings.max_line_gap)
    if lines is None: return ()
    result=[]
    for x1,y1,x2,y2 in np.asarray(lines).reshape(-1,4):
        result.append((float(x1),float(y1),float(x2),float(y2)))
    return tuple(sorted(result))

def _raster_evidence(frame,source,pixel_to_normalized,settings):
    return _dedupe(_make_evidence(source=source,method="hough",start=Point2D(x1,y1),end=Point2D(x2,y2),source_to_normalized=pixel_to_normalized) for x1,y1,x2,y2 in _hough_lines(frame,settings))

def extract_raster_lines_from_image(image_path,*,source,source_to_normalized,settings=RasterLineSettings()):
    if source.source_space!="pixel" or not source.has_raster_content: raise LineExtractionError("Raster image extraction requires pixel source space and raster content.")
    cv2=_cv2(); frame=cv2.imread(str(image_path),cv2.IMREAD_COLOR)
    if frame is None: raise LineExtractionError(f"Could not read raster image: {image_path!s}")
    h,w=frame.shape[:2]
    if w!=int(round(source.width)) or h!=int(round(source.height)): raise LineExtractionError("Image dimensions do not match pixel source metadata.")
    return _raster_evidence(frame,source,source_to_normalized,settings)

def extract_raster_lines_from_pdf(pdf_path,*,page_index,source,source_to_normalized,settings=RasterLineSettings()):
    if page_index!=source.page_index: raise LineExtractionError("page_index must match source metadata.")
    fitz=_fitz(); np=_numpy(); cv2=_cv2(); doc=fitz.open(str(pdf_path))
    try:
        if page_index<0 or page_index>=len(doc): raise LineExtractionError("PDF page_index is out of range.")
        page=doc[page_index]; r=page.rect
        if source.source_space=="vector":
            if abs(float(r.width)-source.width)>1e-6 or abs(float(r.height)-source.height)>1e-6: raise LineExtractionError("PDF page dimensions do not match vector source metadata.")
            z=settings.render_dpi/72.0; pix=page.get_pixmap(matrix=fitz.Matrix(z,z),alpha=False)
            p2s=Affine2D.from_rows(((float(r.width)/pix.width,0,0),(0,float(r.height)/pix.height,0),(0,0,1)))
            p2n=p2s.then(source_to_normalized)
        else:
            tw,th=int(round(source.width)),int(round(source.height))
            pix=page.get_pixmap(matrix=fitz.Matrix(tw/float(r.width),th/float(r.height)),alpha=False)
            if pix.width!=tw or pix.height!=th: raise LineExtractionError("PDF rasterization did not match declared pixel source dimensions.")
            p2n=source_to_normalized
        frame=np.frombuffer(pix.samples,dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
        frame=cv2.cvtColor(frame,cv2.COLOR_RGBA2BGRA if pix.n==4 else cv2.COLOR_RGB2BGR)
        return _raster_evidence(frame,source,p2n,settings)
    finally: doc.close()

def extract_lines_from_pdf(pdf_path,*,page_index,source,source_to_normalized,settings=RasterLineSettings()):
    if source.has_vector_geometry: return extract_vector_lines_from_pdf(pdf_path,page_index=page_index,source=source,source_to_normalized=source_to_normalized)
    if source.has_raster_content: return extract_raster_lines_from_pdf(pdf_path,page_index=page_index,source=source,source_to_normalized=source_to_normalized,settings=settings)
    raise LineExtractionError("PDF source metadata has neither vector nor raster content.")
