"""AutoCAD COM automation client."""
import win32com.client as win32
import pythoncom
from typing import Optional, Any


class AcadClient:
    """Wrapper around AutoCAD COM automation."""

    def __init__(self):
        self.acad: Optional[Any] = None
        self.doc: Optional[Any] = None
        self.ms: Optional[Any] = None  # model space

    def connect(self) -> bool:
        """Connect to running AutoCAD or launch a new instance."""
        try:
            pythoncom.CoInitialize()
        except Exception:
            pass
        # Try active object first
        try:
            self.acad = win32.GetActiveObject("AutoCAD.Application")
        except Exception:
            # Try version-specific ProgIDs (newest first)
            for progid in ["AutoCAD.Application.25.1", "AutoCAD.Application.25.0",
                           "AutoCAD.Application.24.3", "AutoCAD.Application.24.2",
                           "AutoCAD.Application.24.1", "AutoCAD.Application.24.0",
                           "AutoCAD.Application"]:
                try:
                    self.acad = win32.Dispatch(progid)
                    self.acad.Visible = True
                    break
                except Exception:
                    continue
            if self.acad is None:
                print("无法连接 AutoCAD — 请确认已安装")
                return False
        self.doc = self.acad.ActiveDocument
        self.ms = self.doc.ModelSpace
        print(f"已连接: {self.doc.Name}")
        return True

    # ── drawing primitives ──

    def add_line(self, x1, y1, z1, x2, y2, z2):
        start = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x1, y1, z1])
        end = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x2, y2, z2])
        return self.ms.AddLine(start, end)

    def add_circle(self, cx, cy, cz, radius):
        center = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [cx, cy, cz])
        return self.ms.AddCircle(center, radius)

    def add_text(self, x, y, z, text, height=2.5):
        ins = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, z])
        t = self.ms.AddText(text, ins, height)
        return t

    def add_polyline(self, points):
        """points: list of (x, y, z) tuples."""
        flat = []
        for p in points:
            flat.extend(p)
        pts = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)
        pl = self.ms.AddPolyline(pts)
        return pl

    def add_arc(self, cx, cy, cz, radius, start_angle, end_angle):
        center = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [cx, cy, cz])
        return self.ms.AddArc(center, radius, start_angle, end_angle)

    # ── selection & utils ──

    def send_command(self, cmd: str):
        self.doc.SendCommand(cmd + "\n")

    def zoom_extents(self):
        self.acad.ZoomExtents()

    def zoom_window(self, p1, p2):
        """p1, p2: (x, y) tuples in current UCS."""
        pt1 = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [p1[0], p1[1], 0])
        pt2 = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [p2[0], p2[1], 0])
        self.acad.ZoomWindow(pt1, pt2)

    def get_selection(self, prompt="选择对象"):
        """Let user select entities interactively, return selection set."""
        try:
            sel = self.doc.SelectionSets.Add("TMP_SEL")
            sel.SelectOnScreen()
            return sel
        except Exception:
            return None

    @property
    def all_entities(self):
        """Generator yielding all entities in model space."""
        for i in range(self.ms.Count):
            yield self.ms.Item(i)

    @property
    def layer(self):
        return self.doc.ActiveLayer.Name

    @layer.setter
    def layer(self, name):
        """Set active layer, create if not exists."""
        try:
            self.doc.ActiveLayer = self.doc.Layers.Item(name)
        except Exception:
            self.doc.Layers.Add(name)
            self.doc.ActiveLayer = self.doc.Layers.Item(name)

    def __del__(self):
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def connect() -> AcadClient:
    """Quick connect helper. Returns connected client or exits."""
    c = AcadClient()
    if c.connect():
        return c
    raise RuntimeError("无法连接 AutoCAD")
