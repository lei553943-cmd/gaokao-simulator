# -*- coding: utf-8 -*-
"""SolidWorks classic drive shaft - automated modeling."""

import win32com.client
import pythoncom
import math


def create_drive_shaft():
    pythoncom.CoInitialize()

    sw = win32com.client.Dispatch("SldWorks.Application")
    sw.Visible = True

    template = sw.GetDocumentTemplate(1, "", 0, 0, 0)
    sw.NewDocument(template, 0, 0, 0)
    doc = sw.ActiveDoc
    mm = 0.001

    # ========== 1. Revolve base body ==========
    # Find the correct front plane name (Chinese vs English SW)
    selected = False
    for name in ["Front Plane", "前视基准面"]:
        try:
            if doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, False, 0, sw, 0):
                selected = True
                print(f"Using plane: {name}")
                break
        except:
            continue

    if not selected:
        # Last resort: traverse features to find any plane
        feat = doc.FirstFeature()
        while feat:
            n = feat.Name
            try:
                if doc.Extension.SelectByID2(n, "PLANE", 0, 0, 0, False, 0, sw, 0):
                    selected = True
                    print(f"Using plane (from traversal): {n}")
                    break
            except:
                pass
            feat = feat.GetNextFeature()

    if not selected:
        raise Exception("Could not select front plane")

    doc.SketchManager.InsertSketch(True)

    # Half-profile: (axial X, radius Y) in mm
    pts = [
        (0, 0),
        (0, 12.5),
        (50, 12.5),
        (52, 15),
        (55, 15),
        (120, 15),
        (122, 17.5),
        (125, 17.5),
        (135, 22.5),
        (195, 22.5),
        (197, 17.5),
        (200, 17.5),
        (265, 15),
        (270, 15),
        (272, 12.5),
        (320, 12.5),
        (320, 0),
    ]

    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        doc.SketchManager.CreateLine(x1 * mm, y1 * mm, 0, x2 * mm, y2 * mm, 0)
    doc.SketchManager.CreateLine(pts[-1][0] * mm, 0, 0, 0, 0, 0)
    doc.SketchManager.InsertSketch(True)

    doc.FeatureManager.FeatureRevolve2(
        True, True, False, False, False, False,
        0, 0, 2 * math.pi, False, False
    )
    print("Base body revolved.")

    # ========== 2. Keyway cut ==========
    for name in ["Top Plane", "上视基准面"]:
        try:
            if doc.Extension.SelectByID2(name, "PLANE", 0, 0, 0, False, 0, sw, 0):
                break
        except:
            continue
    doc.SketchManager.InsertSketch(True)

    kw_r = 22.5
    kw_len = 45
    kw_w = 8
    kw_x0 = 150

    doc.SketchManager.CreateCenterRectangle(
        (kw_x0 + kw_len / 2) * mm, kw_r * mm, 0,
        (kw_x0 + kw_len / 2) * mm, kw_r * mm, 0,
        kw_x0 * mm, (kw_r - kw_w / 2) * mm, 0,
        (kw_x0 + kw_len) * mm, (kw_r + kw_w / 2) * mm, 0,
    )
    doc.SketchManager.InsertSketch(True)

    doc.FeatureManager.FeatureCut3(
        True, False, False, 0, 0, 4 * mm, 0,
        False, False, False, False, 0, 0,
        False, False, False, False, False, 0, 0, 0
    )
    print("Keyway cut.")

    # ========== 3. Fillets ==========
    doc.ClearSelection2(True)
    for sx, sy in [(52, 14), (122, 16), (135, 21), (197, 21), (200, 16), (270, 14)]:
        try:
            doc.Extension.SelectByID2("", "EDGE", sx * mm, sy * mm, 0, True, 1, sw, 0)
        except:
            pass
    doc.FeatureManager.InsertFeatureRound(1.5 * mm, 0, 0, 0, 0, 0, 0)
    print("Fillets added.")

    # ========== 4. Chamfers ==========
    doc.ClearSelection2(True)
    try:
        doc.Extension.SelectByID2("", "EDGE", 0, 12.5 * mm, 0, True, 1, sw, 0)
    except:
        pass
    try:
        doc.Extension.SelectByID2("", "EDGE", 320 * mm, 12.5 * mm, 0, True, 1, sw, 0)
    except:
        pass
    doc.FeatureManager.InsertFeatureChamfer(4, 1, 1 * mm, math.radians(45), 0, 0, 0, 0)
    print("Chamfers added.")

    # ========== 5. Finish ==========
    doc.EditRebuild3()
    doc.ViewZoomtofit2()
    print("Done! Classic drive shaft created.")
    return doc


if __name__ == "__main__":
    create_drive_shaft()
