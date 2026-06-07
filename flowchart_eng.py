"""工程设计流程图 — 水草清理机器人设计流程."""
import math
import win32com.client as win32
import pythoncom
from acad_client import connect


# ═══════════ 常量 ═══════════

NODE_W, NODE_H = 60, 20
CORNER_R = 6
DIAMOND_SIZE = 28
TEXT_H = 3.5
LINE_WEIGHT = 30  # 0.30mm, hundredths of mm
ARROW_S = 4.0

# 颜色索引: 7=black/white dependent on bg, 0=black byBlock (use 7 for white bg)
COLOR_BLACK = 0

# Y 方向行距
STEP = NODE_H + 22
Y = [0, -42, -84, -126, -170, -212, -254, -296]

# 3列 X 位置
X3 = [-80, 0, 80]


# ═══════════ 工具函数 ═══════════

def _var(x, y, z=0.0):
    return win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [x, y, z])


def add_centered_text(ms, x, y, text, height):
    t = ms.AddText(text, _var(x, y), height)
    t.Alignment = 10  # acAlignmentMiddleCenter
    t.TextAlignmentPoint = _var(x, y)
    return t


def add_line(ms, x1, y1, x2, y2):
    return ms.AddLine(_var(x1, y1), _var(x2, y2))


def add_arc(ms, cx, cy, r, start_ang, end_ang):
    return ms.AddArc(_var(cx, cy), r, start_ang, end_ang)


def arrowhead(ms, x, y, angle):
    """Draw arrowhead at (x,y) pointing in `angle` (radians, direction arrow points)."""
    s = ARROW_S
    a1 = angle + math.radians(160)
    a2 = angle - math.radians(160)
    x1, y1 = x + s * math.cos(a1), y + s * math.sin(a1)
    x2, y2 = x + s * math.cos(a2), y + s * math.sin(a2)
    add_line(ms, x, y, x1, y1)
    add_line(ms, x, y, x2, y2)


def polyline(ms, pts):
    """pts: list of (x,y) tuples (z=0)."""
    flat = []
    for p in pts:
        flat.extend((p[0], p[1], 0.0))
    arr = win32.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, flat)
    return ms.AddPolyline(arr)


# ═══════════ 形状绘制 ═══════════

def draw_rounded_rect(ms, cx, cy, w, h, r):
    """Draw rounded rectangle centered at (cx, cy)."""
    hw, hh = w / 2, h / 2
    # 四角圆弧
    add_arc(ms, cx + hw - r, cy + hh - r, r, 0, math.pi / 2)           # 右上
    add_arc(ms, cx - hw + r, cy + hh - r, r, math.pi / 2, math.pi)     # 左上
    add_arc(ms, cx - hw + r, cy - hh + r, r, math.pi, math.pi * 1.5)   # 左下
    add_arc(ms, cx + hw - r, cy - hh + r, r, math.pi * 1.5, math.pi * 2)  # 右下
    # 四边直线
    add_line(ms, cx + hw - r, cy + hh, cx - hw + r, cy + hh)   # 上边
    add_line(ms, cx + hw, cy + hh - r, cx + hw, cy - hh + r)   # 右边
    add_line(ms, cx + hw - r, cy - hh, cx - hw + r, cy - hh)   # 下边
    add_line(ms, cx - hw, cy + hh - r, cx - hw, cy - hh + r)   # 左边


def draw_diamond(ms, cx, cy, size):
    """Draw diamond centered at (cx, cy)."""
    half = size / 2
    pts = [(cx, cy + half), (cx + half, cy), (cx, cy - half), (cx - half, cy), (cx, cy + half)]
    polyline(ms, pts)


# ═══════════ 连线绘制 ═══════════

def draw_straight_arrow(ms, x1, y1, x2, y2, label='', label_offset=(8, 0)):
    """Vertical or nearly-vertical arrow with arrowhead at (x2, y2)."""
    add_line(ms, x1, y1, x2, y2)
    angle = math.atan2(y2 - y1, x2 - x1)
    arrowhead(ms, x2, y2, angle)
    if label:
        mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
        add_centered_text(ms, mx, my, label, 2.8)


def draw_branch_1to3(ms, from_x, from_y, to_y, x3, label_prefix=''):
    """One source → 3 targets (same Y). Returns junction Y for reference."""
    junc_y = (from_y + to_y) / 2
    # 竖线到汇合点
    add_line(ms, from_x, from_y, from_x, junc_y)
    # 水平总线
    add_line(ms, x3[0], junc_y, x3[2], junc_y)
    # 3 条竖线到目标
    for x in x3:
        add_line(ms, x, junc_y, x, to_y)
        arrowhead(ms, x, to_y, -math.pi / 2)
    return junc_y


def draw_merge_3to1(ms, from_y, x3, to_x, to_y):
    """3 sources (same Y) → one target."""
    junc_y = (from_y + to_y) / 2
    for x in x3:
        add_line(ms, x, from_y, x, junc_y)
    add_line(ms, x3[0], junc_y, x3[2], junc_y)
    add_line(ms, to_x, junc_y, to_x, to_y)
    arrowhead(ms, to_x, to_y, -math.pi / 2)


def draw_feedback_left(ms, from_x, from_y, to_x, to_y, label):
    """Go left, up, then right. from_x,from_y=diamond left. to_x,to_y=target left edge."""
    left_x = from_x - 35
    # 左
    add_line(ms, from_x, from_y, left_x, from_y)
    arrowhead(ms, left_x, from_y, math.pi)  # points left
    # 标签
    add_centered_text(ms, (from_x + left_x) / 2, from_y - 8, label, 2.8)
    # 上
    add_line(ms, left_x, from_y, left_x, to_y)
    # 右
    add_line(ms, left_x, to_y, to_x, to_y)
    arrowhead(ms, to_x, to_y, 0)  # points right


# ═══════════ 主程序 ═══════════

def main():
    c = connect()
    doc = c.doc
    ms = c.ms

    # ── 设置文字样式（宋体）──
    try:
        style = doc.TextStyles.Item('FC_SimSun')
    except Exception:
        style = doc.TextStyles.Add('FC_SimSun')
    style.SetFont('宋体', False, False, 0, 0)  # or 'SimSun.ttf'
    style.Width = 0.85
    doc.ActiveTextStyle = style

    # ── 图层 ──
    layers = {'FC_Shape': {'color': 0, 'lw': LINE_WEIGHT},
              'FC_Text':  {'color': 0, 'lw': -1},  # -1 = default
              'FC_Line':  {'color': 0, 'lw': LINE_WEIGHT}}

    for name, props in layers.items():
        try:
            layer = doc.Layers.Item(name)
        except Exception:
            layer = doc.Layers.Add(name)
        if props['lw'] >= 0:
            layer.Lineweight = props['lw']

    old_layer = doc.ActiveLayer

    # ═══════════ 绘制连线 ═══════════
    doc.ActiveLayer = doc.Layers.Item('FC_Line')

    # 1→2: 前期调研 → 提出设计方案
    draw_straight_arrow(ms, 0, Y[0] - NODE_H / 2, 0, Y[1] + NODE_H / 2)

    # 2→3: 提出设计方案 → 3个方案（分支）
    draw_branch_1to3(ms, 0, Y[1] - NODE_H / 2, Y[2] + NODE_H / 2, X3)

    # 3→4: 3个方案 → 符合要求？（汇聚）
    draw_merge_3to1(ms, Y[2] - NODE_H / 2, X3, 0, Y[3] + DIAMOND_SIZE / 2)

    # 4→2 反馈: 菱形左侧 → 提出设计方案左边缘
    draw_feedback_left(ms, -DIAMOND_SIZE / 2, Y[3], -NODE_W / 2, Y[1], '否')

    # 4→5: 菱形下方 → 水草收割船整机设计
    draw_straight_arrow(ms, 0, Y[3] - DIAMOND_SIZE / 2, 0, Y[4] + NODE_H / 2, '是', (10, 0))

    # 5→6: 水草收割船整机设计 → 3个设计部分（分支）
    draw_branch_1to3(ms, 0, Y[4] - NODE_H / 2, Y[5] + NODE_H / 2, X3)

    # 6→7: 3个设计部分 → 完成水草清理机器人设计（汇聚）
    draw_merge_3to1(ms, Y[5] - NODE_H / 2, X3, 0, Y[6] + NODE_H / 2)

    # 7→8: 完成水草清理机器人设计 → 完成设计
    draw_straight_arrow(ms, 0, Y[6] - NODE_H / 2, 0, Y[7] + NODE_H / 2)

    # ═══════════ 绘制节点 ═══════════
    doc.ActiveLayer = doc.Layers.Item('FC_Shape')

    # Row 0
    draw_rounded_rect(ms, 0, Y[0], NODE_W, NODE_H, CORNER_R)

    # Row 1
    draw_rounded_rect(ms, 0, Y[1], NODE_W, NODE_H, CORNER_R)

    # Row 2 — 3个方案
    for x in X3:
        draw_rounded_rect(ms, x, Y[2], NODE_W, NODE_H, CORNER_R)

    # Row 3 — 菱形
    draw_diamond(ms, 0, Y[3], DIAMOND_SIZE)

    # Row 4
    draw_rounded_rect(ms, 0, Y[4], NODE_W + 10, NODE_H, CORNER_R)  # 稍宽

    # Row 5 — 3个设计部分
    for x in X3:
        draw_rounded_rect(ms, x, Y[5], NODE_W, NODE_H, CORNER_R)

    # Row 6
    draw_rounded_rect(ms, 0, Y[6], NODE_W + 10, NODE_H, CORNER_R)

    # Row 7
    draw_rounded_rect(ms, 0, Y[7], NODE_W, NODE_H, CORNER_R)

    # ═══════════ 绘制文字 ═══════════
    doc.ActiveLayer = doc.Layers.Item('FC_Text')

    add_centered_text(ms, 0, Y[0], '前期调研与需求分析', TEXT_H)
    add_centered_text(ms, 0, Y[1], '提出设计方案', TEXT_H)
    add_centered_text(ms, X3[0], Y[2], '旋转切割式收割方案', TEXT_H)
    add_centered_text(ms, X3[1], Y[2], '明轮推进式驱动方案', TEXT_H)
    add_centered_text(ms, X3[2], Y[2], '吸入式收集方案', TEXT_H)
    add_centered_text(ms, 0, Y[3], '符合要求？', TEXT_H)
    add_centered_text(ms, 0, Y[4], '水草收割船整机设计', TEXT_H)
    add_centered_text(ms, X3[0], Y[5], '收割与收集部分设计', TEXT_H)
    add_centered_text(ms, X3[1], Y[5], '动力与传动部分设计', TEXT_H)
    add_centered_text(ms, X3[2], Y[5], '其他部件设计', TEXT_H)
    add_centered_text(ms, 0, Y[6], '完成水草清理机器人设计', TEXT_H)
    add_centered_text(ms, 0, Y[7], '完成设计', TEXT_H)

    # ── 恢复 ──
    doc.ActiveLayer = old_layer
    c.zoom_extents()
    print('工程设计流程图已绘制完成')


if __name__ == '__main__':
    main()
