"""Generate bearing engineering drawing in AutoCAD — 深沟球轴承 6204."""
import math
import win32com.client as win32
import pythoncom
from acad_client import AcadClient


class BearingDrawing:
    # Bearing 6204 params (mm), scale factor 5x for visibility
    SCALE = 5
    BORE_D = 20 * SCALE          # 100
    OD_D = 47 * SCALE            # 235
    WIDTH = 14 * SCALE           # 70
    BALL_D = 7.94 * SCALE        # 39.7
    PITCH_D = (BORE_D + OD_D) / 2  # 167.5
    GROOVE_R = BALL_D / 2 * 1.03  # ~20.45 (slightly larger than ball)
    SHOULDER_OUTER = PITCH_D / 2 + BALL_D / 2 * 0.25
    SHOULDER_INNER = PITCH_D / 2 - BALL_D / 2 * 0.25
    GROOVE_HALF_W = BALL_D / 2 * 0.95

    def __init__(self, cad: AcadClient):
        self.c = cad
        self.setup_layers()
        self.setup_linetypes()

    def v(self, *args):
        """Make VARIANT array from values."""
        return win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, list(args))

    def pt(self, x, y):
        return self.v(x, y, 0)

    def setup_layers(self):
        layers = {
            "轮廓线": {"color": 7, "lw": 0.5},       # white, thick
            "中心线": {"color": 1, "lw": 0.18},       # red
            "剖面线": {"color": 4, "lw": 0.13},       # cyan
            "标注": {"color": 3, "lw": 0.18},         # green
            "图框": {"color": 7, "lw": 0.3},          # white
            "文字": {"color": 7, "lw": 0.18},         # white
        }
        for name, props in layers.items():
            try:
                self.c.doc.Layers.Item(name)
            except Exception:
                layer = self.c.doc.Layers.Add(name)
                layer.color = props["color"]
                try:
                    layer.LineWeight = props["lw"]
                except Exception:
                    pass

    def setup_linetypes(self):
        for lt in ["CENTER", "DASHED"]:
            try:
                self.c.doc.Linetypes.Load(lt, "acad.lin")
            except Exception:
                pass  # already loaded

    # ── drawing primitives on specific layers ──

    def draw_line(self, x1, y1, x2, y2, layer="轮廓线"):
        self.c.layer = layer
        return self.c.add_line(x1, y1, 0, x2, y2, 0)

    def draw_circle(self, cx, cy, r, layer="轮廓线"):
        self.c.layer = layer
        return self.c.add_circle(cx, cy, 0, r)

    def draw_arc(self, cx, cy, r, start_ang, end_ang, layer="轮廓线"):
        self.c.layer = layer
        c = self.c.ms.AddArc(self.pt(cx, cy), r, start_ang, end_ang)
        return c

    def draw_polyline(self, points, closed=True, layer="轮廓线"):
        """points: list of (x,y) tuples."""
        self.c.layer = layer
        flat = []
        for x, y in points:
            flat.extend([x, y])
        pl = self.c.ms.AddLightWeightPolyline(self.v(*flat))
        pl.Closed = closed
        return pl

    def draw_text(self, x, y, text, height=3.5, layer="文字", rotation=0):
        self.c.layer = layer
        t = self.c.ms.AddText(text, self.pt(x, y), height)
        t.Rotation = rotation
        return t

    def hatch_region(self, entity, layer="剖面线"):
        """Hatch a single closed polyline."""
        self.c.layer = layer
        hatch = self.c.ms.AddHatch(0, "ANSI31", True)
        obj_array = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [entity])
        hatch.AppendOuterLoop(obj_array)
        hatch.PatternScale = self.SCALE * 2
        hatch.Evaluate()
        return hatch

    # ── geometry helpers ──

    def groove_points_outer(self, y_shoulder, y_center, r_groove, w_half, sign=1):
        """Compute points for the outer ring groove profile.
        sign=1 for top half, sign=-1 for bottom half.
        Returns list of (x,y) for the inner face of outer ring (with groove).
        """
        pts = []
        # Walk from left edge to right edge along inner face with groove
        steps = 30
        groove_hw = self.GROOVE_HALF_W
        for i in range(steps + 1):
            x = -w_half + 2 * w_half * i / steps
            if abs(x) <= groove_hw:
                # On groove: arc shape
                dx_sq = x * x
                r_sq = r_groove * r_groove
                if dx_sq < r_sq:
                    dy = math.sqrt(r_sq - dx_sq)
                    y = y_center + sign * dy
                else:
                    y = y_shoulder
            else:
                # On shoulder (or transition)
                if abs(x) <= groove_hw * 1.3:
                    # transition zone
                    frac = (abs(x) - groove_hw) / (groove_hw * 0.3)
                    dx_sq = groove_hw * groove_hw
                    r_sq = r_groove * r_groove
                    dy = math.sqrt(max(0, r_sq - dx_sq))
                    y_groove = y_center + sign * dy
                    y = y_groove + (y_shoulder - y_groove) * frac
                else:
                    y = y_shoulder
            pts.append((x, y))
        return pts

    # ── main drawing ──

    def draw_cross_section(self):
        """Draw bearing cross-section (upper half, symmetric about centerline)."""
        hw = self.WIDTH / 2
        od_r = self.OD_D / 2
        bore_r = self.BORE_D / 2
        pitch_r = self.PITCH_D / 2
        ball_r = self.BALL_D / 2
        groove_r = self.GROOVE_R
        sh_outer = self.SHOULDER_OUTER
        sh_inner = self.SHOULDER_INNER
        groove_hw = self.GROOVE_HALF_W

        # ── center lines ──
        hl = self.draw_line(-hw - 15, 0, hw + 15, 0, "中心线")
        vl = self.draw_line(0, -od_r - 15, 0, od_r + 15, "中心线")
        for ln in [hl, vl]:
            try:
                ln.Linetype = "CENTER"
            except Exception:
                pass

        # ── outer ring (upper half) ──
        outer_pts = [(-hw, od_r), (hw, od_r)]
        outer_pts.append((hw, sh_outer))
        groove_pts = self.groove_points_outer(sh_outer, pitch_r, groove_r, hw, sign=1)
        outer_pts.extend(reversed(groove_pts))
        outer_pts.append((-hw, sh_outer))
        outer_ring_top = self.draw_polyline(outer_pts, closed=True)

        # ── outer ring (lower half, mirrored) ──
        outer_pts_bot = [(-hw, -od_r), (hw, -od_r)]
        outer_pts_bot.append((hw, -sh_outer))
        groove_pts_bot = self.groove_points_outer(-sh_outer, -pitch_r, groove_r, hw, sign=-1)
        outer_pts_bot.extend(reversed(groove_pts_bot))
        outer_pts_bot.append((-hw, -sh_outer))
        outer_ring_bot = self.draw_polyline(outer_pts_bot, closed=True)

        # ── inner ring (upper half) ──
        inner_pts = [(-hw, bore_r), (hw, bore_r)]
        inner_pts.append((hw, sh_inner))
        groove_pts_inner = self.groove_points_outer(sh_inner, pitch_r, groove_r, hw, sign=-1)
        inner_pts.extend(reversed(groove_pts_inner))
        inner_pts.append((-hw, sh_inner))
        inner_ring_top = self.draw_polyline(inner_pts, closed=True)

        # ── inner ring (lower half, mirrored) ──
        inner_pts_bot = [(-hw, -bore_r), (hw, -bore_r)]
        inner_pts_bot.append((hw, -sh_inner))
        groove_pts_ib = self.groove_points_outer(-sh_inner, -pitch_r, groove_r, hw, sign=1)
        inner_pts_bot.extend(reversed(groove_pts_ib))
        inner_pts_bot.append((-hw, -sh_inner))
        inner_ring_bot = self.draw_polyline(inner_pts_bot, closed=True)

        # ── balls ──
        self.draw_circle(0, pitch_r, ball_r)
        self.draw_circle(0, -pitch_r, ball_r)

        # ── cage (simplified) ──
        cage_r_outer = pitch_r + ball_r * 0.35
        cage_r_inner = pitch_r - ball_r * 0.35
        cage_x = 2 * self.SCALE
        # Upper cage
        self.draw_line(-cage_x, cage_r_inner, -cage_x, cage_r_outer, "轮廓线")
        self.draw_line(cage_x, cage_r_inner, cage_x, cage_r_outer, "轮廓线")
        # Lower cage
        self.draw_line(-cage_x, -cage_r_inner, -cage_x, -cage_r_outer, "轮廓线")
        self.draw_line(cage_x, -cage_r_inner, cage_x, -cage_r_outer, "轮廓线")

        # ── shaft (simplified, dashed) ──
        self.draw_line(-hw - 10, bore_r, hw + 10, bore_r, "轮廓线")
        self.draw_line(-hw - 10, -bore_r, hw + 10, -bore_r, "轮廓线")

        # ── hatching ──
        for ring in [outer_ring_top, outer_ring_bot, inner_ring_top, inner_ring_bot]:
            self.hatch_region(ring)

        return outer_ring_top, outer_ring_bot, inner_ring_top, inner_ring_bot

    def draw_side_view(self, offset_x):
        """Draw simplified side view at given X offset."""
        od_r = self.OD_D / 2
        bore_r = self.BORE_D / 2
        pitch_r = self.PITCH_D / 2
        ball_r = self.BALL_D / 2 + 1  # slightly larger for visibility

        cx = offset_x

        # Outer circle
        self.draw_circle(cx, 0, od_r)
        # Bore circle
        self.draw_circle(cx, 0, bore_r)
        # Pitch circle (center line)
        pc = self.draw_circle(cx, 0, pitch_r, "中心线")
        # Ball positions (in side view, the balls appear as circles around pitch circle)
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(angle)
            bx = cx + pitch_r * math.cos(rad)
            by = pitch_r * math.sin(rad)
            self.draw_circle(bx, by, ball_r * 0.25)  # small dots for balls

        # Center cross
        self.draw_line(cx - od_r - 10, 0, cx + od_r + 10, 0, "中心线")
        self.draw_line(cx, -od_r - 10, cx, od_r + 10, "中心线")

    def draw_dimensions(self):
        """Add linear dimensions."""
        hw = self.WIDTH / 2
        od_r = self.OD_D / 2
        bore_r = self.BORE_D / 2
        pitch_r = self.PITCH_D / 2
        offset = 20

        self.c.layer = "标注"

        # Width dimension
        y_w = -od_r - offset
        self.draw_line(-hw, y_w, hw, y_w, "标注")  # dimension line
        self.draw_line(-hw, y_w - 5, -hw, y_w + 5, "标注")  # left tick
        self.draw_line(hw, y_w - 5, hw, y_w + 5, "标注")  # right tick
        txt = self.draw_text(0, y_w - 8, str(int(self.WIDTH / self.SCALE)), 4, "文字")
        txt.Alignment = 10  # acAlignmentMiddleCenter

        # OD dimension
        x_r = hw + offset
        self.draw_line(x_r, bore_r, x_r, od_r, "标注")
        self.draw_line(x_r - 3, od_r, x_r + 3, od_r, "标注")
        self.draw_line(x_r - 3, bore_r, x_r + 3, bore_r, "标注")
        txt = self.draw_text(x_r + 5, (bore_r + od_r) / 2, str(int(self.OD_D / self.SCALE)), 4, "文字")
        txt.Alignment = 10

        # Bore dimension
        x_l = -hw - offset
        self.draw_line(x_l, 0, x_l, bore_r, "标注")
        self.draw_line(x_l - 3, bore_r, x_l + 3, bore_r, "标注")
        txt = self.draw_text(x_l - 5, bore_r / 2, str(int(self.BORE_D / self.SCALE)), 4, "文字")
        txt.Alignment = 10

        # Ball diameter
        ball_r = self.BALL_D / 2
        x_b = hw + offset + 30
        self.draw_line(x_b, pitch_r - ball_r, x_b, pitch_r + ball_r, "标注")
        txt = self.draw_text(x_b + 5, pitch_r, "BALL " + str(round(self.BALL_D / self.SCALE, 1)), 3.5, "文字")
        txt.Alignment = 10

    def draw_title_block(self, offset_x, offset_y):
        """Draw a simple title block."""
        self.c.layer = "图框"
        # Border
        w, h = 180, 50
        x, y = offset_x, offset_y
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        self.draw_polyline(pts, closed=True)

        # Inner lines
        self.draw_line(x, y + 15, x + w, y + 15)
        self.draw_line(x, y + 30, x + w, y + 30)
        self.draw_line(x + 120, y, x + 120, y + 15)

        self.c.layer = "文字"
        self.draw_text(x + 5, y + 5, "深沟球轴承 6204", 4)
        self.draw_text(x + 125, y + 5, "1:1", 3)
        self.draw_text(x + 5, y + 20, "材料: GCr15", 3)
        self.draw_text(x + 5, y + 35, "制图: CAD", 3)

    def draw_border(self):
        """A3-ish border."""
        self.c.layer = "图框"
        w, h = 420, 297
        pts = [(0, 0), (w, 0), (w, h), (0, h)]
        self.draw_polyline(pts, closed=True)
        # Inner border
        pts2 = [(10, 10), (w - 10, 10), (w - 10, h - 10), (10, h - 10)]
        self.draw_polyline(pts2, closed=True)

    def generate(self):
        """Generate complete bearing engineering drawing."""
        print("绘制边框...")
        self.draw_border()

        print("绘制剖视图...")
        self.draw_cross_section()

        print("绘制侧视图...")
        self.draw_side_view(offset_x=200)

        print("添加尺寸标注...")
        self.draw_dimensions()

        print("绘制标题栏...")
        self.draw_title_block(230, 10)

        self.c.zoom_extents()
        print("完成！")


def main():
    c = AcadClient()
    if not c.connect():
        print("无法连接 AutoCAD")
        return
    bd = BearingDrawing(c)
    bd.generate()


if __name__ == "__main__":
    main()
