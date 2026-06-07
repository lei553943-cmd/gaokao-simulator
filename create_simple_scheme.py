"""
经济型数控铣床十字工作台 - 传动方案简图 (简化版)
"""
import win32com.client, pythoncom, os

acad = win32com.client.Dispatch("AutoCAD.Application.25")
doc = acad.ActiveDocument
ms = doc.ModelSpace

def V(*args):
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, list(args))

def line(x1, y1, x2, y2):
    return ms.AddLine(V(x1,y1,0), V(x2,y2,0))

def rect(x1, y1, x2, y2):
    pl = ms.AddLightWeightPolyline(V(x1,y1,0, x2,y1,0, x2,y2,0, x1,y2,0))
    pl.Closed = True
    return pl

def text(x, y, s, h=5):
    return ms.AddText(s, V(x,y,0), h)

def circle(cx, cy, r):
    return ms.AddCircle(V(cx,cy,0), r)

def arrow(x1, y1, x2, y2):
    line(x1, y1, x2, y2)
    import math
    dx, dy = x2-x1, y2-y1
    L = math.sqrt(dx*dx+dy*dy)
    if L > 0:
        ux, uy = dx/L, dy/L
        h = 8
        line(x2, y2, x2 - h*ux*2 + h*uy, y2 - h*uy*2 - h*ux)
        line(x2, y2, x2 - h*ux*2 - h*uy, y2 - h*uy*2 + h*ux)

# ==========================================
# 传动方案简图 (水平排列,一个视图)
# ==========================================
Y = 0
CX = 0   # centerline Y

# --- 设计参数 ---
MOTOR_W, MOTOR_H = 130, 60
COUP_W = 35
BEAR_W = 22
SCREW_W, SCREW_D = 450, 16
NUT_W = 62
TABLE_W, TABLE_H = 250, 35
BASE_W, BASE_H = 620, 20
SADDLE_H = 20
RAIL_H = 15

X = 0

# === [1] 伺服电机 ===
rect(X, Y - MOTOR_H/2, X + MOTOR_W, Y + MOTOR_H/2)
circle(X + MOTOR_W - 15, Y, 12)
circle(X + MOTOR_W - 15, Y, 6)
text(X + MOTOR_W/2 - 30, Y + MOTOR_H/2 + 10, "伺服电机", 4.5)
text(X + MOTOR_W/2 - 30, Y + MOTOR_H/2 + 4, "60ST-M01330", 3.5)
text(X + MOTOR_W/2 - 30, Y + MOTOR_H/2 - 2, "0.4kW 3000rpm", 3)

# === [2] 联轴器 ===
X += MOTOR_W
rect(X, Y - 16, X + COUP_W, Y + 16)
for i in range(3):
    line(X + 5 + i*10, Y - 12, X + 5 + i*10, Y + 12)
text(X + COUP_W/2 - 18, Y + 22, "膜片联轴器", 3.5)
text(X + COUP_W/2 - 18, Y + 16, "DBM22-D32", 3)

# === [3] 固定端支座 ===
X += COUP_W
rect(X, Y - 22, X + BEAR_W, Y + 22)
circle(X + BEAR_W/2, Y, 10)
text(X + BEAR_W/2 - 20, Y + 28, "固定端", 3.5)
text(X + BEAR_W/2 - 22, Y + 22, "SET-LEC21-12", 3)
text(X + BEAR_W/2 - 18, Y + 16, "7001AC", 2.5)

# === [4] 滚珠丝杠 ===
X += BEAR_W
line(X, Y, X + SCREW_W, Y)  # centerline
rect(X, Y - SCREW_D/2, X + SCREW_W, Y + SCREW_D/2)
# 螺纹示意
for i in range(0, int(SCREW_W - 20), 15):
    line(X + 10 + i, Y - SCREW_D/2 - 1, X + 16 + i, Y + SCREW_D/2 + 1)
text(X + SCREW_W/2 - 60, Y - 18, "滚珠丝杠 LCP02-16-5", 4)
text(X + SCREW_W/2 - 45, Y - 24, "公称直径16mm 导程5mm 4圈", 3)

# === [5] 螺母座 ===
NUT_X = X + (SCREW_W - NUT_W) / 2
rect(NUT_X, Y - 14, NUT_X + NUT_W, Y + 14)
text(NUT_X + NUT_W/2 - 18, Y + 22, "螺母座", 3.5)

# === [6] 支承端支座 ===
rect(X + SCREW_W, Y - 14, X + SCREW_W + BEAR_W, Y + 14)
circle(X + SCREW_W + BEAR_W/2, Y, 7)
text(X + SCREW_W, Y + 22, "支承端", 3.5)
text(X + SCREW_W, Y + 16, "SET-LEC21-12", 3)

X += SCREW_W + BEAR_W

# === [7] 导轨 & 工作台 ===
RAIL_Y1 = Y + 35
RAIL_W = SCREW_W + 60
rect(COUP_W + BEAR_W + 30, RAIL_Y1, COUP_W + BEAR_W + 30 + RAIL_W, RAIL_Y1 + RAIL_H)
rect(COUP_W + BEAR_W + 30, RAIL_Y1 + RAIL_H + SADDLE_H, COUP_W + BEAR_W + 30 + RAIL_W, RAIL_Y1 + RAIL_H*2 + SADDLE_H)
text(X - 480, RAIL_Y1 + RAIL_H/2, "直线导轨 IBJ23-H24 (双导轨四滑块)", 3.5)

# 工作台
TABLE_X1 = COUP_W + BEAR_W + 30 + (RAIL_W - TABLE_W) / 2
TABLE_Y = RAIL_Y1 + RAIL_H*2 + SADDLE_H + 12
rect(TABLE_X1, TABLE_Y, TABLE_X1 + TABLE_W, TABLE_Y + TABLE_H)
text(TABLE_X1 + TABLE_W/2 - 40, TABLE_Y + TABLE_H/2, "工作台 250×250×35", 4.5)
text(TABLE_X1 + TABLE_W/2 - 35, TABLE_Y + TABLE_H/2 - 7, "HT200铸铁", 3)

# 螺母座到工作台连接线
line(NUT_X + NUT_W/2, Y + 14, NUT_X + NUT_W/2, TABLE_Y)

# === 底板 ===
BASE_Y = RAIL_Y1 - 5
rect(0, BASE_Y, BASE_W, BASE_Y + BASE_H)
text(BASE_W/2 - 30, BASE_Y - 10, "底板 620×240 HT200", 3.5)

# === 传动方向箭头 (底部) ===
ARROW_Y = BASE_Y - 25
arrow(10, ARROW_Y, SCREW_W + BEAR_W, ARROW_Y)
text(MOTOR_W + COUP_W + BEAR_W + SCREW_W/2 - 60, ARROW_Y + 8, "传动方向: 旋转运动 → 直线运动", 4)

# === 标题 ===
TITLE_Y = TABLE_Y + TABLE_H + 25
text(0, TITLE_Y + 10, "经济型数控铣床十字工作台 传动方案简图", 7)
line(-20, TITLE_Y, SCREW_W + 80, TITLE_Y)
text(50, TITLE_Y - 10, "伺服电机→联轴器→固定端支座→滚珠丝杠→螺母座(工作台)→支承端  |  河南工学院 机械工程学院", 3.5)

# 保存
try:
    acad.ZoomExtents()
except:
    pass

filename = r"C:\Users\32539\Desktop\code\经济型数控铣床十字工作台_传动方案图.dwg"
doc.SaveAs(filename)
print("传动方案简图已保存:", filename)
print("Done.")
