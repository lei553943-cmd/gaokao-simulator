"""SolidWorks bearing generator — 深沟球轴承."""
import math
import pythoncom
import win32com.client as win32

# ── 轴承参数 (mm, 6004 近似) ──
R1, R2 = 10.0, 14.0   # 内圈: 内径→外径
R3, R4 = 18.0, 24.0   # 外圈: 内径→外径
W = 14.0              # 宽度
BALL_R = 3.0          # 滚珠半径
BALL_C = (R2 + R3) / 2  # 滚珠中心距轴线距离
PI2 = 2 * math.pi

TEMPLATE = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2025\templates\gb_part.prtdot"


def connect():
    try:
        pythoncom.CoInitialize()
    except Exception:
        pass
    sw = win32.Dispatch("SldWorks.Application")
    sw.Visible = True
    return sw


def make_revolve(part, centerline_x, lines, merge):
    """Create a revolve feature from a rectangle profile.
    All coordinates are relative to the sketch origin.
    centerline_x: X position of the vertical centerline
    lines: list of (x1,y1,x2,y2) tuples for the closed profile
    merge: True to merge with existing bodies
    """
    sm = part.SketchManager
    sm.CreateCenterLine(centerline_x, -12.0, 0.0, centerline_x, 12.0, 0.0)
    for x1, y1, x2, y2 in lines:
        sm.CreateLine(x1, y1, 0.0, x2, y2, 0.0)
    return part.FeatureManager.FeatureRevolve(
        PI2, False, False, 0.0, False, merge, True, False,
    )


def main():
    sw = connect()
    part = sw.NewDocument(TEMPLATE, 0, 0, 0)
    half = W / 2

    # ═══════════ 1. 外圈 ═══════════
    part.InsertSketch2(False)
    make_revolve(part, 0.0, [
        (R3,  half,  R4,  half),
        (R4,  half,  R4, -half),
        (R4, -half,  R3, -half),
        (R3, -half,  R3,  half),
    ], True)
    part.ClearSelection2(True)
    print("外圈 OK")

    # ═══════════ 2. 内圈 ═══════════
    part.InsertSketch2(False)
    make_revolve(part, 0.0, [
        (R1,  half,  R2,  half),
        (R2,  half,  R2, -half),
        (R2, -half,  R1, -half),
        (R1, -half,  R1,  half),
    ], False)
    part.ClearSelection2(True)
    print("内圈 OK")

    # ═══════════ 3. 滚珠滚道（圆环体） ═══════════
    # 圆形截面绕主轴(x=0)旋转 = 圆环体
    part.InsertSketch2(False)
    sm = part.SketchManager
    sm.CreateCenterLine(0.0, -BALL_R - 5, 0.0, 0.0, BALL_R + 5, 0.0)
    sm.CreateCircle(BALL_C, 0.0, 0.0, BALL_C + BALL_R, 0.0, 0.0)
    part.FeatureManager.FeatureRevolve(PI2, False, False, 0.0, False, True, True, False)
    part.ClearSelection2(True)
    print("滚珠滚道 OK")

    part.ViewZoomtofit2()
    print(f"\n深沟球轴承完成")
    print(f"  内径 O{R1*2:.0f}  外径 O{R4*2:.0f}  宽度 {W:.0f}")
    print(f"  滚珠截面 R{BALL_R}  滚道中心 O{BALL_C*2:.1f}")
    print("  注: 滚珠为整体圆环 (FeatureCircularPattern COM 接口不可用)")


if __name__ == "__main__":
    main()
