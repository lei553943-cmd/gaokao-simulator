"""Flowchart builder for AutoCAD."""
import math
from collections import deque
from acad_client import AcadClient, connect

# ── layout constants ──

NODE_W, NODE_H = 30, 15
DECISION_SIZE = 22
V_GAP, H_GAP = 22, 18
ARROW_SIZE = 3.5
TEXT_H = 2.5

LAYERS = ['fc_shapes', 'fc_text', 'fc_lines']


class FlowNode:
    def __init__(self, nid, text, ntype='process'):
        self.id = nid
        self.text = text
        self.ntype = ntype
        self.x = self.y = 0.0
        if ntype == 'decision':
            self.w = self.h = DECISION_SIZE
        elif ntype == 'start_end':
            self.w, self.h = NODE_W, NODE_H * 0.6
        else:
            self.w, self.h = NODE_W, NODE_H

    @property
    def top(self): return self.y + self.h / 2

    @property
    def bottom(self): return self.y - self.h / 2

    @property
    def left(self): return self.x - self.w / 2

    @property
    def right(self): return self.x + self.w / 2

    def port(self, direction):
        """Return (x, y) of a port in given direction ('top'|'bottom'|'left'|'right')."""
        if direction == 'top':    return (self.x, self.top)
        if direction == 'bottom': return (self.x, self.bottom)
        if direction == 'left':   return (self.left, self.y)
        if direction == 'right':  return (self.right, self.y)


class Flowchart:
    def __init__(self, client: AcadClient):
        self.c = client
        self.nodes = {}
        self.edges = []

    def add_node(self, nid, text, ntype='process'):
        self.nodes[nid] = FlowNode(nid, text, ntype)
        return self

    def add_edge(self, src, dst, label=''):
        self.edges.append((src, dst, label))
        return self

    # ═══════════ layout ═══════════

    def auto_layout(self, root_id, direction='down'):
        """Top-down BFS layout. direction: 'down' or 'right'."""
        # Build adjacency
        children = {}
        for s, d, _ in self.edges:
            children.setdefault(s, []).append(d)

        # Assign levels via BFS (longest-path depth)
        depth = {}
        indeg = {}
        for nid in self.nodes:
            indeg[nid] = 0
        for s, d, _ in self.edges:
            indeg[d] = indeg.get(d, 0) + 1

        # Topological: find nodes with no incoming edges
        roots = [nid for nid in self.nodes if indeg[nid] == 0]
        if not roots:
            roots = [root_id]

        depth = {}
        q = deque()
        for r in roots:
            depth[r] = 0
            q.append(r)
        while q:
            nid = q.popleft()
            for cid in children.get(nid, []):
                nd = depth[nid] + 1
                if cid not in depth or nd > depth[cid]:
                    depth[cid] = nd
                q.append(cid)

        # Collect nodes by level
        levels = {}
        for nid, d in depth.items():
            levels.setdefault(d, []).append(nid)

        max_depth = max(levels.keys()) if levels else 0
        if direction == 'down':
            for d, nids in levels.items():
                total_w = len(nids) * NODE_W + (len(nids) - 1) * H_GAP
                start_x = -total_w / 2 + NODE_W / 2
                for i, nid in enumerate(nids):
                    node = self.nodes[nid]
                    node.x = start_x + i * (NODE_W + H_GAP)
                    node.y = -d * (NODE_H + V_GAP)
        else:  # right
            for d, nids in levels.items():
                total_h = len(nids) * NODE_H + (len(nids) - 1) * V_GAP
                start_y = -total_h / 2 + NODE_H / 2
                for i, nid in enumerate(nids):
                    node = self.nodes[nid]
                    node.y = start_y + i * (NODE_H + V_GAP)
                    node.x = d * (NODE_W + H_GAP)

    # ═══════════ draw ═══════════

    def draw(self):
        for name in LAYERS:
            try:
                self.c.doc.Layers.Item(name)
            except Exception:
                self.c.doc.Layers.Add(name)

        old = self.c.doc.ActiveLayer

        self.c.doc.ActiveLayer = self.c.doc.Layers.Item('fc_lines')
        for s, d, lbl in self.edges:
            if s in self.nodes and d in self.nodes:
                self._draw_connector(self.nodes[s], self.nodes[d], lbl)

        self.c.doc.ActiveLayer = self.c.doc.Layers.Item('fc_shapes')
        for node in self.nodes.values():
            self._draw_shape(node)

        self.c.doc.ActiveLayer = self.c.doc.Layers.Item('fc_text')
        for node in self.nodes.values():
            self._draw_text(node)

        self.c.doc.ActiveLayer = old
        self.c.zoom_extents()

    def _draw_shape(self, n):
        x, y, w, h = n.x, n.y, n.w, n.h

        if n.ntype == 'process':
            pts = [(x - w/2, y + h/2, 0), (x + w/2, y + h/2, 0),
                   (x + w/2, y - h/2, 0), (x - w/2, y - h/2, 0),
                   (x - w/2, y + h/2, 0)]

        elif n.ntype == 'decision':
            pts = [(x, y + h/2, 0), (x + w/2, y, 0),
                   (x, y - h/2, 0), (x - w/2, y, 0),
                   (x, y + h/2, 0)]

        elif n.ntype == 'start_end':
            r = min(w, h) * 0.3
            pts = [
                (x - w/2 + r, y + h/2, 0), (x + w/2 - r, y + h/2, 0),
                (x + w/2, y + h/2 - r, 0), (x + w/2, y - h/2 + r, 0),
                (x + w/2 - r, y - h/2, 0), (x - w/2 + r, y - h/2, 0),
                (x - w/2, y - h/2 + r, 0), (x - w/2, y + h/2 - r, 0),
                (x - w/2 + r, y + h/2, 0),
            ]

        elif n.ntype == 'io':
            skew = 6
            pts = [(x - w/2 + skew, y + h/2, 0), (x + w/2 + skew, y + h/2, 0),
                   (x + w/2 - skew, y - h/2, 0), (x - w/2 - skew, y - h/2, 0),
                   (x - w/2 + skew, y + h/2, 0)]

        else:
            pts = [(x - w/2, y + h/2, 0), (x + w/2, y + h/2, 0),
                   (x + w/2, y - h/2, 0), (x - w/2, y - h/2, 0),
                   (x - w/2, y + h/2, 0)]

        self.c.add_polyline(pts)

    def _draw_text(self, n):
        tw = len(n.text) * TEXT_H * 0.55
        self.c.add_text(n.x - tw / 2, n.y - TEXT_H / 3, 0, n.text, TEXT_H)

    def _draw_connector(self, src, dst, label):
        sx, sy = src.port('bottom')
        dx, dy = dst.port('top')

        if abs(sx - dx) < 0.5:
            self.c.add_line(sx, sy, 0, dx, dy, 0)
            self._arrowhead(dx, dy, dx, sy)
        else:
            mid_y = (sy + dy) / 2
            self.c.add_line(sx, sy, 0, sx, mid_y, 0)
            self.c.add_line(sx, mid_y, 0, dx, mid_y, 0)
            self.c.add_line(dx, mid_y, 0, dx, dy, 0)
            self._arrowhead(dx, dy, dx, mid_y)

        if label:
            self._edge_label(sx, dx, mid_y if abs(sx - dx) >= 0.5 else (sy + dy) / 2, label)

    def _arrowhead(self, x, y, fx, fy):
        angle = math.atan2(y - fy, x - fx)
        s = ARROW_SIZE
        a1 = angle + math.radians(155)
        a2 = angle - math.radians(155)
        self.c.add_line(x, y, 0, x + s * math.cos(a1), y + s * math.sin(a1), 0)
        self.c.add_line(x, y, 0, x + s * math.cos(a2), y + s * math.sin(a2), 0)

    def _edge_label(self, x1, x2, my, text):
        lx = (x1 + x2) / 2 + 4
        tw = len(text) * 2.0 * 0.55
        self.c.add_text(lx - tw / 2, my, 0, text, 2.0)


# ── demo ──

if __name__ == '__main__':
    c = connect()
    fc = Flowchart(c)

    fc.add_node('start', '开始', 'start_end') \
      .add_node('input', '输入数据', 'io') \
      .add_node('check', '数据有效?', 'decision') \
      .add_node('process', '处理数据', 'process') \
      .add_node('error', '报错退出', 'start_end') \
      .add_node('output', '输出结果', 'io') \
      .add_node('end', '结束', 'start_end')

    fc.add_edge('start', 'input') \
      .add_edge('input', 'check') \
      .add_edge('check', 'process', '是') \
      .add_edge('check', 'error', '否') \
      .add_edge('process', 'output') \
      .add_edge('output', 'end')

    fc.auto_layout('start')
    fc.draw()
    print('流程图已绘制完成')
