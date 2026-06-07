"""
经济型数控铣床十字工作台 - 传动方案图
AutoCAD COM API 自动绘图
"""

import win32com.client
import pythoncom
import math
import os

# Connect to running AutoCAD
acad = win32com.client.Dispatch("AutoCAD.Application.25")
acad.Visible = True
doc = acad.ActiveDocument
ms = doc.ModelSpace

# ============= Helper Functions =============
def V(*args):
    """Create a VARIANT array of doubles"""
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, list(args))

def add_line(x1, y1, x2, y2):
    """Add a line"""
    return ms.AddLine(V(x1, y1, 0), V(x2, y2, 0))

def add_circle(cx, cy, r):
    return ms.AddCircle(V(cx, cy, 0), r)

def add_rect(x1, y1, x2, y2):
    """Draw rectangle as polyline"""
    pts = V(x1, y1, 0, x2, y1, 0, x2, y2, 0, x1, y2, 0)
    pl = ms.AddLightWeightPolyline(pts)
    pl.Closed = True
    return pl

def add_filled_rect(x1, y1, x2, y2, color_idx=8):
    """Draw solid-filled rectangle using hatch"""
    try:
        pts = V(x1, y1, 0, x2, y1, 0, x2, y2, 0, x1, y2, 0)
        pl = ms.AddLightWeightPolyline(pts)
        pl.Closed = True
        hatch = ms.AddHatch(0, "SOLID", True)
        # For SOLID pattern, don't need AppendOuterLoop - different approach
        # Just color the polyline and use it as boundary
        outer = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_DISPATCH, [pl])
        hatch.AppendOuterLoop(outer)
        hatch.Evaluate()
        hatch.color = color_idx
        return hatch
    except:
        # Fallback: just draw colored outline
        pl.color = color_idx
        return pl

def add_text(x, y, text, height=4, rotation=0):
    """Add text"""
    t = ms.AddText(text, V(x, y, 0), height)
    return t

def add_dim_rotated(x1, y1, x2, y2, text_y):
    """Add aligned dimension"""
    try:
        dim = ms.AddDimAligned(V(x1, y1, 0), V(x2, y2, 0), V((x1+x2)/2, text_y, 0))
        return dim
    except:
        pass

def add_arrow(x1, y1, x2, y2):
    """Draw arrow using leader"""
    try:
        pts = V(x1, y1, 0, x2, y2, 0)
        leader = ms.AddLeader(pts, None, 0)
        return leader
    except:
        return add_line(x1, y1, x2, y2)

# ============================================================================
#                     传动方案图 - TRANSMISSION SCHEME DIAGRAM
# ============================================================================

BASE_X, BASE_Y = 0, 0
SCALE = 1.0

# --- Overall dimensions from design doc ---
TABLE_W, TABLE_H = 250, 35       # Worktable
SCREW_L_X, SCREW_D = 450, 16     # X-axis ball screw
RAIL_L_X = 580                    # X-axis rail total length
MOTOR_L, MOTOR_H = 130, 60       # Servo motor 60ST frame
COUPLING_L = 35                   # Diaphragm coupling length
BEARING_L = 22                    # Bearing housing width
NUT_L = 62                        # Nut length
BASE_L, BASE_W, BASE_H = 620, 240, 20  # Base plate
SADDLE_L, SADDLE_W, SADDLE_H = 450, 240, 20  # Saddle
TRAVEL_X = 310
TRAVEL_Y = 240
WR = 15  # rail width

# ========================================================================
#  VIEW 1: 传动方案主视图 (Side elevation - X-axis cross section)
# ========================================================================

SV_Y = 0  # Side view Y baseline

# --- Base Plate (底板) ---
add_filled_rect(BASE_X, SV_Y, BASE_X + BASE_L, SV_Y + BASE_H, 253)  # light gray
add_rect(BASE_X, SV_Y, BASE_X + BASE_L, SV_Y + BASE_H)
add_text(BASE_X + BASE_L/2 - 30, SV_Y + BASE_H + 5, "底板 620x240 HT200", 3.5)

# --- Y-axis bottom structure ---
# Y-axis rails on base (side view shows rail cross-section)
RAIL_BOT = SV_Y + BASE_H
RAIL_H = 15
# Rail blocks seen from side
add_rect(BASE_X + 20, RAIL_BOT, BASE_X + 40, RAIL_BOT + RAIL_H)   # left rail
add_rect(BASE_X + BASE_L - 40, RAIL_BOT, BASE_X + BASE_L - 20, RAIL_BOT + RAIL_H)  # right rail
add_text(BASE_X + 200, RAIL_BOT + RAIL_H + 3, "Y轴直线导轨 (IBJ23-H24-L500)", 3.0)

# --- Saddle (Y-axis carriage / 拖板) ---
SADDLE_Y = RAIL_BOT + RAIL_H + 12  # slider block height
add_filled_rect(BASE_X + 30, SADDLE_Y, BASE_X + 30 + SADDLE_L, SADDLE_Y + SADDLE_H, 254)
add_rect(BASE_X + 30, SADDLE_Y, BASE_X + 30 + SADDLE_L, SADDLE_Y + SADDLE_H)
add_text(BASE_X + 250, SADDLE_Y + SADDLE_H/2, "拖板 (Y轴滑鞍) HT200", 3.5)

# Y-axis ball screw (side view, behind saddle, drawn as dashed/small)
Y_SCREW_Y = RAIL_BOT + RAIL_H/2
add_line(BASE_X + 50, Y_SCREW_Y, BASE_X + BASE_L - 50, Y_SCREW_Y)
add_text(BASE_X + 200, Y_SCREW_Y - 5, "Y轴丝杠 (LCP02-16-5-L380)", 2.5)

# --- X-axis rails on saddle ---
XRAIL_BOT = SADDLE_Y + SADDLE_H
XRAIL_H = 15
add_rect(BASE_X + 80, XRAIL_BOT, BASE_X + 100, XRAIL_BOT + XRAIL_H)
add_rect(BASE_X + 330, XRAIL_BOT, BASE_X + 350, XRAIL_BOT + XRAIL_H)
add_text(BASE_X + 200, XRAIL_BOT + XRAIL_H + 3, "X轴直线导轨 (IBJ23-H24-L580, 间距250mm)", 3.0)

# Slider blocks on X rails
SLIDER_Y = XRAIL_BOT + XRAIL_H
for sx in [BASE_X + 80 - 10, BASE_X + 80 - 10 + 59, BASE_X + 330 - 10, BASE_X + 330 - 10 + 59]:
    add_rect(sx, SLIDER_Y, sx + 80, SLIDER_Y + 12)

# --- Worktable (工作台) ---
TABLE_Y = SLIDER_Y + 12
add_filled_rect(BASE_X + 120, TABLE_Y, BASE_X + 120 + TABLE_W, TABLE_Y + TABLE_H, 255)
add_rect(BASE_X + 120, TABLE_Y, BASE_X + 120 + TABLE_W, TABLE_Y + TABLE_H)
add_text(BASE_X + 200, TABLE_Y + TABLE_H/2, "工作台 250x250x35", 4.0)

# T-slots (side view - dotted lines on top)
for tx in [BASE_X + 180, BASE_X + 240]:
    add_line(tx, TABLE_Y + TABLE_H, tx, TABLE_Y + TABLE_H - 10)

# --- X-axis BALL SCREW (main focus of side view) ---
SCREW_Y = XRAIL_BOT + XRAIL_H/2
SCREW_X_START = BASE_X + 80
SCREW_X_END = SCREW_X_START + SCREW_L_X

# Centerline
add_line(SCREW_X_START - 30, SCREW_Y, SCREW_X_END + 30, SCREW_Y)

# Screw shaft body
add_filled_rect(SCREW_X_START, SCREW_Y - SCREW_D/2, SCREW_X_END, SCREW_Y + SCREW_D/2, 8)

# Screw thread indication
for i in range(int(SCREW_L_X / 10)):
    sx = SCREW_X_START + 10 + i * 10
    if sx < SCREW_X_END - 10:
        add_line(sx, SCREW_Y - SCREW_D/2 - 1, sx + 3, SCREW_Y + SCREW_D/2 + 1)

add_text(SCREW_X_START + SCREW_L_X/2 - 50, SCREW_Y - 18, "X轴滚珠丝杠 LCP02-16-5-L450", 3.5)
add_text(SCREW_X_START + SCREW_L_X/2 - 35, SCREW_Y - 23, "公称直径16 导程5 4圈", 2.5)

# --- Nut + Nut bracket (螺母座) ---
NUT_X = SCREW_X_START + (SCREW_L_X - NUT_L) / 2
add_filled_rect(NUT_X, SCREW_Y - 16, NUT_X + NUT_L, SCREW_Y + 16, 252)
add_rect(NUT_X, SCREW_Y - 16, NUT_X + NUT_L, SCREW_Y + 16)
# Nut bracket connecting to worktable
add_line(NUT_X + NUT_L/2, SCREW_Y + 16, NUT_X + NUT_L/2, TABLE_Y)
add_text(NUT_X + NUT_L/2 - 15, SCREW_Y + 25, "螺母座", 3.0)

# --- Fixed-end bearing support (固定端) ---
BF_X = SCREW_X_START - BEARING_L
add_filled_rect(BF_X, SCREW_Y - 22, BF_X + BEARING_L, SCREW_Y + 22, 251)
add_rect(BF_X, SCREW_Y - 22, BF_X + BEARING_L, SCREW_Y + 22)
add_text(BF_X - 25, SCREW_Y + 28, "固定端支座 SET-LEC21-12", 3.0)
add_text(BF_X - 10, SCREW_Y + 22, "7001AC角接触球轴承", 2.5)
add_circle(BF_X + BEARING_L/2, SCREW_Y, 9)

# --- Supported-end bearing (支承端) ---
BS_X = SCREW_X_END
add_filled_rect(BS_X, SCREW_Y - 14, BS_X + BEARING_L, SCREW_Y + 14, 251)
add_rect(BS_X, SCREW_Y - 14, BS_X + BEARING_L, SCREW_Y + 14)
add_text(BS_X - 5, SCREW_Y + 20, "支承端 SET-LEC21-12", 3.0)
add_circle(BS_X + BEARING_L/2, SCREW_Y, 6)

# --- Coupling (联轴器) ---
CP_X = BF_X - COUPLING_L
add_filled_rect(CP_X, SCREW_Y - 18, CP_X + COUPLING_L, SCREW_Y + 18, 254)
add_rect(CP_X, SCREW_Y - 18, CP_X + COUPLING_L, SCREW_Y + 18)
# Diaphragm plates
for i in range(3):
    cx = CP_X + 5 + i * 10
    add_line(cx, SCREW_Y - 14, cx, SCREW_Y + 14)
add_text(CP_X + 3, SCREW_Y - 24, "膜片联轴器", 3.0)
add_text(CP_X + 3, SCREW_Y - 29, "DBM22-D32-d8-e14", 2.5)

# --- Servo Motor (伺服电机) ---
MOT_X = CP_X - MOTOR_L
add_filled_rect(MOT_X, SCREW_Y - MOTOR_H/2, MOT_X + MOTOR_L, SCREW_Y + MOTOR_H/2, 255)
add_rect(MOT_X, SCREW_Y - MOTOR_H/2, MOT_X + MOTOR_L, SCREW_Y + MOTOR_H/2)
# Motor flange
add_rect(MOT_X + MOTOR_L - 8, SCREW_Y - MOTOR_H/2 - 5, MOT_X + MOTOR_L + 5, SCREW_Y + MOTOR_H/2 + 5)
add_text(MOT_X + MOTOR_L/2 - 28, SCREW_Y + 5, "伺服电机", 4.0)
add_text(MOT_X + MOTOR_L/2 - 28, SCREW_Y - 2, "60ST-M01330", 3.5)
add_text(MOT_X + MOTOR_L/2 - 28, SCREW_Y - 9, "0.4kW 3000rpm", 2.5)

# --- Motor-to-coupling shaft line ---
add_line(MOT_X + MOTOR_L, SCREW_Y, CP_X, SCREW_Y)

# --- Power Flow Arrows at bottom ---
FLOW_Y = SV_Y - 25
flow_stops = [
    (MOT_X + 20, "伺服电机"),
    (CP_X + COUPLING_L/2, "联轴器"),
    (BF_X + BEARING_L/2, "固定端\n支座"),
    (SCREW_X_START + SCREW_L_X/3, "滚珠丝杠副"),
    (NUT_X + NUT_L/2, "螺母座"),
    (NUT_X + NUT_L/2 + 30, "工作台\n(直线运动)"),
]

# Main power flow arrow
add_arrow(MOT_X + 40, FLOW_Y, SCREW_X_END + 20, FLOW_Y)

for fx, fname in flow_stops:
    add_text(fx - 10, FLOW_Y - 8, "↑", 3)
    add_text(fx - len(fname.split('\n')[0])*2, FLOW_Y - 16, fname, 2.8)

add_text(MOT_X + (SCREW_X_END - MOT_X)/2 - 40, FLOW_Y + 8, "动力传递方向: 旋转运动 → 直线运动", 3.5)

# --- Key dimensions (侧视图关键尺寸) ---
DIM_Y = SV_Y - 55
# Overall length
add_dim_rotated(MOT_X, DIM_Y, MOT_X + MOTOR_L, DIM_Y, DIM_Y - 10)
add_text(MOT_X + MOTOR_L/2 - 10, DIM_Y - 18, "130", 2.5)

add_dim_rotated(SCREW_X_START, DIM_Y, SCREW_X_END, DIM_Y, DIM_Y - 10)
add_text(SCREW_X_START + SCREW_L_X/2 - 8, DIM_Y - 18, "450/310(行程)", 2.5)

# ========================================================================
#  VIEW 2: 俯视图 (Top View)
# ========================================================================

TV_Y = SV_Y - 80
TV_OFFSET_X = 0

# --- Base plate top view ---
add_rect(BASE_X, TV_Y, BASE_X + BASE_L, TV_Y - BASE_W)
add_text(BASE_X + BASE_L/2 - 30, TV_Y - BASE_W - 5, "底板 620x240", 3.0)

# --- Y-axis guide rails (horizontal in top view) ---
RY1_TOP = TV_Y - 20
RY2_BOT = TV_Y - BASE_W + 20
# Rail bodies
add_filled_rect(BASE_X + 20, RY1_TOP, BASE_X + 20 + 500, RY1_TOP - WR, 254)
add_filled_rect(BASE_X + 20, RY2_BOT + WR, BASE_X + 20 + 500, RY2_BOT, 254)
add_text(BASE_X + 270, RY1_TOP + 5, "Y轴导轨 IBJ23-H24-L500", 2.5)
add_text(BASE_X + 270, RY2_BOT - 5, "导轨间距 170mm", 2.5)

# Y-axis screw centerline
YSCREW_TY = (RY1_TOP + RY2_BOT) / 2
add_line(BASE_X + 10, YSCREW_TY, BASE_X + BASE_L - 10, YSCREW_TY)
add_text(BASE_X + 250, YSCREW_TY + 3, "Y轴丝杠 LCP02-16-5-L380 (F15-P8)", 2.5)

# Y-axis motor (left side)
add_rect(BASE_X - 40, YSCREW_TY - MOTOR_H/2, BASE_X + 10, YSCREW_TY + MOTOR_H/2)
add_text(BASE_X - 40, YSCREW_TY + MOTOR_H/2 + 5, "Y轴电机\n60ST-M01330", 2.5)

# Y-axis fixed/supported bearings
add_rect(BASE_X + 10, YSCREW_TY - 12, BASE_X + 32, YSCREW_TY + 12)
add_rect(BASE_X + BASE_L - 42, YSCREW_TY - 8, BASE_X + BASE_L - 20, YSCREW_TY + 8)

# --- Saddle outline (拖板) ---
add_rect(BASE_X + 30, RY1_TOP - 30, BASE_X + 30 + SADDLE_L, RY2_BOT + 30)
add_text(BASE_X + 250, (RY1_TOP + RY2_BOT)/2, "拖板 450x240", 3.0)

# --- X-axis guide rails (vertical bars in top view, on saddle) ---
XR1_LEFT = BASE_X + 120
XR2_RIGHT = BASE_X + 120 + 250
# Rail bodies
add_filled_rect(XR1_LEFT, RY1_TOP - 30, XR1_LEFT - WR, RY2_BOT + 30, 253)
add_filled_rect(XR2_RIGHT, RY1_TOP - 30, XR2_RIGHT + WR, RY2_BOT + 30, 253)
add_text(XR1_LEFT - WR, RY1_TOP - 25, "X轴导轨\nIBJ23-H24-L580", 2.5)
add_text(XR1_LEFT - WR, RY2_BOT + 35, "导轨间距250mm", 2.5)

# Slider blocks
for sy in [RY1_TOP - 20, RY2_BOT + 20]:
    add_rect(XR1_LEFT - WR, sy, XR1_LEFT - WR + 60, sy + 12)
    add_rect(XR2_RIGHT, sy, XR2_RIGHT + 60, sy + 12)

# --- X-axis screw centerline ---
XSCREW_TX = (XR1_LEFT + XR2_RIGHT) / 2
add_line(XSCREW_TX, RY1_TOP - 50, XSCREW_TX, RY2_BOT + 50)
add_text(XSCREW_TX - 15, RY1_TOP - 55, "X轴丝杠中心", 2.5)
add_text(XSCREW_TX - 15, RY2_BOT + 60, "LCP02-16-5-L450", 2.5)

# X-axis motor (front, on saddle)
add_rect(XSCREW_TX - MOTOR_H/2, RY1_TOP - 50 - MOTOR_L, XSCREW_TX + MOTOR_H/2, RY1_TOP - 50)
add_text(XSCREW_TX - 45, RY1_TOP - 50 - MOTOR_L/2, "X轴电机\n60ST-M01330", 2.5)

# X-axis bearing supports
add_rect(XSCREW_TX - 12, RY1_TOP - 72, XSCREW_TX + 12, RY1_TOP - 50)
add_rect(XSCREW_TX - 8, RY2_BOT + 50, XSCREW_TX + 8, RY2_BOT + 72)

# --- Worktable (工作台面) ---
WT_TOP = RY1_TOP - 65
WT_BOT = RY2_BOT + 65
WT_LEFT = XR1_LEFT - WR - 30
WT_RIGHT = XR2_RIGHT + WR + 30
add_rect(WT_LEFT, WT_TOP, WT_RIGHT, WT_BOT)
add_text((WT_LEFT + WT_RIGHT)/2 - 30, (WT_TOP + WT_BOT)/2, "工作台 250x250", 4.0)

# T-slots
TS1 = WT_LEFT + (WT_RIGHT - WT_LEFT)/3
TS2 = WT_LEFT + 2*(WT_RIGHT - WT_LEFT)/3
add_rect(TS1, WT_TOP + 5, TS1 + 6, WT_BOT - 5)
add_rect(TS2, WT_TOP + 5, TS2 + 6, WT_BOT - 5)
add_text(TS1 + 3, WT_TOP + 10, "T型槽A=6", 2.5)

# --- X/Y travel range indicators ---
# X direction
DIM_XY = SV_Y - 140
add_text(BASE_X + 120 + TRAVEL_X/2 - 25, DIM_XY + 5, "X行程 310mm →", 3.5)

# ========================================================================
#  TECHNICAL SPECS TABLE (技术参数表)
# ========================================================================

SPEC_X = BASE_X + BASE_L + 80
SPEC_Y = SV_Y + 50

specs = [
    ("══════ 技术参数表 ══════", None, True),
    ("工作台尺寸", "250×250×35 mm (HT200铸铁)", False),
    ("X轴有效行程", "310 mm", False),
    ("Y轴有效行程", "240 mm", False),
    ("导轨型号", "IBJ23-H24 直线滚动导轨", False),
    ("X轴导轨长度", "580 mm (双导轨四滑块)", False),
    ("Y轴导轨长度", "500 mm (双导轨四滑块)", False),
    ("滚珠丝杠", "LCP02-16-5 (公称直径16,导程5)", False),
    ("X轴丝杠长度", "450 mm (F15-P8)", False),
    ("Y轴丝杠长度", "380 mm (F15-P8)", False),
    ("伺服电机", "60ST-M01330 (0.4kW,3000rpm,1.27Nm)", False),
    ("联轴器", "DBM22-D32-d8-e14 双膜片式", False),
    ("轴承支座", "SET-LEC21-12 (7001AC角接触)", False),
    ("支承方式", "一端固定·一端支承", False),
    ("空载快移速度", "2000 mm/min", False),
    ("最大进给速度", "1000 mm/min", False),
    ("设计寿命", "15000 小时", False),
    ("加工材料示例", "45钢, Φ15三刃立铣刀", False),
    ("铣削宽度", "ae = 15 mm", False),
    ("背吃刀量", "ap = 6 mm", False),
    ("控制系统", "西门子S7-1200 PLC (博图V15)", False),
]

for i, (label, val, is_header) in enumerate(specs):
    y_pos = SPEC_Y - i * 9
    if is_header:
        t = add_text(SPEC_X, y_pos, label, 5)
    else:
        txt = f"{label}:  {val}" if val else label
        add_text(SPEC_X, y_pos, txt, 3.0)

# ========================================================================
#  TITLE BLOCK
# ========================================================================

TITLE_X = BASE_X
TITLE_Y = TV_Y - BASE_W - 50

add_text(TITLE_X + 50, TITLE_Y + 15, "经济型数控铣床十字工作台  传动方案图", 8)
add_text(TITLE_X + 150, TITLE_Y, "Transmission Scheme — Cross Worktable for Economic CNC Milling Machine", 3.5)

add_line(TITLE_X - 50, TITLE_Y - 6, BASE_X + BASE_L + 100, TITLE_Y - 6)
add_line(TITLE_X - 50, TITLE_Y - 8, BASE_X + BASE_L + 100, TITLE_Y - 8)

add_text(TITLE_X + 50, TITLE_Y - 16, "设计依据: 毕业设计《经济型数控铣床十字工作台设计》  |  河南工学院 机械工程学院 智能制造工程  |  学生: 雷和市  |  指导教师: 王珂", 3.0)

# ========================================================================
#  ZOOM EXTENTS AND SAVE
# ========================================================================

try:
    acad.ZoomExtents()
except:
    pass

# Save
save_dir = r"C:\Users\32539\Desktop\code"
filename = os.path.join(save_dir, "经济型数控铣床十字工作台_传动方案图.dwg")
try:
    doc.SaveAs(filename)
    print(f"DWG saved: {filename}")
except Exception as e:
    print(f"Save to C failed ({e}), trying F drive...")
    save_dir = r"F:\ai-tools\cad-output"
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, "经济型数控铣床十字工作台_传动方案图.dwg")
    doc.SaveAs(filename)
    print(f"DWG saved: {filename}")

print("=" * 60)
print("传动方案图 生成完毕!")
print("=" * 60)
print("图纸内容:")
print("  [侧视图] 电机→联轴器→固定端→丝杠→螺母座→支承端 传动链")
print("  [俯视图] 底板→Y轴导轨/丝杠→拖板→X轴导轨/丝杠→工作台 叠置结构")
print("  [参数表] 20项主要技术参数")
print("  [标注]   动力传递方向、关键尺寸、部件名称")
print(f"\n文件: {filename}")
