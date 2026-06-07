"""
单相电机正反转电气原理图 — Improved version
Single-phase motor forward/reverse control circuit
Principle: swap start winding polarity vs main winding to reverse direction.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, (ax_main, ax_ctrl) = plt.subplots(1, 2, figsize=(22, 30))
fig.suptitle('单相电机正反转电气原理图', fontsize=20, fontweight='bold', y=0.985)

for ax in [ax_main, ax_ctrl]:
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 32)
    ax.set_aspect('equal')
    ax.axis('off')

# ── Drawing helpers ──
def h(ax, x1, x2, y, lw=2.0, color='black'):
    ax.plot([x1, x2], [y, y], color=color, lw=lw, solid_capstyle='round')

def v(ax, x, y1, y2, lw=2.0, color='black'):
    ax.plot([x, x], [y1, y2], color=color, lw=lw, solid_capstyle='round')

def jdot(ax, x, y, r=0.1):
    ax.add_patch(plt.Circle((x, y), r, fc='k', ec='none', zorder=10))

def breaker(ax, x, y):
    """QF — circuit breaker with overload trip"""
    h(ax, x-0.3, x+0.3, y+0.2)
    h(ax, x-0.3, x+0.3, y-0.2)
    ax.plot([x-0.12, x+0.12], [y-0.15, y+0.15], 'k-', lw=1.5)
    ax.plot([x+0.12, x-0.12], [y-0.15, y+0.15], 'k-', lw=1.5)
    h(ax, x-0.4, x+0.4, y)
    ax.text(x-0.55, y, 'QF', ha='right', va='center', fontsize=11, fontweight='bold')

def fuse(ax, x, y, label='FU'):
    r = plt.Rectangle((x-0.3, y-0.12), 0.6, 0.24, fc='white', ec='k', lw=1.5)
    ax.add_patch(r)
    v(ax, x, y+0.12, y+0.35)
    v(ax, x, y-0.12, y-0.35)
    ax.text(x-0.45, y, label, ha='right', va='center', fontsize=9)

def main_contact(ax, x, y, closed=True):
    """3-phase style main contact (NO)"""
    h(ax, x-0.25, x+0.25, y, lw=2.5)
    if closed:
        h(ax, x-0.2, x-0.03, y+0.2)
        v(ax, x, y+0.2, y-0.2, lw=1.5)
        h(ax, x+0.03, x+0.2, y-0.2)
    else:
        h(ax, x-0.25, x-0.05, y+0.25)
        v(ax, x-0.05, y+0.25, y+0.05, lw=1.5)
        v(ax, x+0.05, y-0.05, y-0.25, lw=1.5)
        h(ax, x+0.05, x+0.25, y-0.25)

def coil(ax, x, y, label, w=0.7, h=1.0):
    """Contactor/relay coil with label"""
    r = plt.Rectangle((x-w/2, y-h/2), w, h, fc='#fffde7', ec='k', lw=2)
    ax.add_patch(r)
    for i in range(4):
        x0 = x - w/2 + 0.08 + i*(w-0.16)/3
        ax.plot([x0, x0+0.1], [y+h/2-0.08, y-h/2+0.08], 'k-', lw=1.2)
    ax.text(x, y-h/2-0.4, label, ha='center', va='top', fontsize=10, fontweight='bold')

def thermal(ax, x, y):
    """Thermal overload element FR"""
    r = plt.Rectangle((x-0.4, y-0.35), 0.8, 0.7, fc='#ffcdd2', ec='k', lw=2)
    ax.add_patch(r)
    for i in range(2):
        x0 = x - 0.15 + i*0.3
        ax.plot([x0, x0+0.12], [y+0.25, y-0.25], 'k-', lw=1.2)
    ax.text(x, y-0.6, 'FR', ha='center', va='top', fontsize=10, fontweight='bold')

def nc_aux(ax, x, y, label=''):
    """NC auxiliary contact (interlock)"""
    h(ax, x-0.35, x+0.35, y, lw=2)
    h(ax, x-0.25, x-0.04, y-0.22)
    v(ax, x-0.04, y-0.22, y-0.04, lw=1.5)
    v(ax, x+0.04, y+0.04, y+0.22, lw=1.5)
    h(ax, x+0.04, x+0.25, y+0.22)
    if label:
        ax.text(x, y+0.4, label, ha='center', va='bottom', fontsize=9, fontweight='bold')

def no_aux(ax, x, y, label=''):
    """NO auxiliary contact (self-hold)"""
    h(ax, x-0.35, x+0.35, y, lw=2)
    h(ax, x-0.25, x-0.04, y+0.22)
    v(ax, x-0.04, y+0.22, y+0.04, lw=1.5)
    v(ax, x+0.04, y-0.04, y-0.22, lw=1.5)
    h(ax, x+0.04, x+0.25, y-0.22)
    if label:
        ax.text(x, y+0.4, label, ha='center', va='bottom', fontsize=9, fontweight='bold')

def nc_button(ax, x, y, label=''):
    """NC pushbutton (stop)"""
    h(ax, x-0.4, x+0.4, y, lw=2)
    h(ax, x-0.28, x-0.04, y-0.2)
    v(ax, x-0.04, y-0.2, y-0.04, lw=1.5)
    v(ax, x+0.04, y+0.04, y+0.2, lw=1.5)
    h(ax, x+0.04, x+0.28, y+0.2)
    if label:
        ax.text(x, y+0.4, label, ha='center', va='bottom', fontsize=9, fontweight='bold')

def no_button(ax, x, y, label=''):
    """NO pushbutton (start)"""
    h(ax, x-0.4, x+0.4, y, lw=2)
    h(ax, x-0.28, x-0.04, y+0.2)
    v(ax, x-0.04, y+0.2, y+0.04, lw=1.5)
    v(ax, x+0.04, y-0.04, y-0.2, lw=1.5)
    h(ax, x+0.04, x+0.28, y-0.2)
    if label:
        ax.text(x, y+0.4, label, ha='center', va='bottom', fontsize=9, fontweight='bold')

def capacitor(ax, x, y):
    h(ax, x-0.3, x+0.3, y+0.25, lw=2.5)
    h(ax, x-0.3, x+0.3, y-0.25, lw=2.5)
    v(ax, x, y-0.25, y+0.25, lw=2)
    ax.text(x+0.5, y, 'C', ha='left', va='center', fontsize=11, fontweight='bold')

def centrifugal(ax, x, y):
    """Centrifugal switch (normally closed)"""
    # base bar
    h(ax, x-0.4, x+0.4, y, lw=2.5)
    # NC contact
    h(ax, x-0.22, x-0.04, y+0.22)
    v(ax, x-0.04, y+0.22, y+0.04, lw=1.5)
    v(ax, x+0.04, y-0.04, y-0.22, lw=1.5)
    h(ax, x+0.04, x+0.22, y-0.22)
    ax.text(x+0.55, y, 'S\n(离心开关)', ha='left', va='center', fontsize=8)

def motor_circle(ax, x, y, r=1.0):
    c = plt.Circle((x, y), r, fc='#e3f2fd', ec='k', lw=2.5)
    ax.add_patch(c)
    ax.text(x, y, 'M\n1~', ha='center', va='center', fontsize=13, fontweight='bold')

def winding(ax, x, y_top, y_bot, label=''):
    """Winding symbol — 4 loops"""
    mid = (y_top + y_bot) / 2
    h_span = (y_top - y_bot) / 8
    for i in range(4):
        yi = y_top - i*2*h_span - h_span
        r = plt.Rectangle((x-0.3, yi), 0.6, h_span*1.5, fc='white', ec='k', lw=1.5)
        ax.add_patch(r)
    if label:
        ax.text(x+0.5, mid, label, ha='left', va='center', fontsize=8)

def ground(ax, x, y):
    h(ax, x-0.5, x+0.5, y, lw=2)
    h(ax, x-0.35, x+0.35, y-0.2, lw=2)
    h(ax, x-0.2, x+0.2, y-0.4, lw=2)
    v(ax, x, y, y+0.5, lw=2)
    ax.text(x+0.6, y-0.2, 'PE', ha='left', va='center', fontsize=10)

def wire_label(ax, x, y, text, dx=-0.6, dy=0):
    ax.text(x+dx, y+dy, text, ha='right', va='center', fontsize=9)

# ═══════════════════════════════════════════════
#  主电路 MAIN CIRCUIT  (left panel)
# ═══════════════════════════════════════════════
ax_main.set_title('主电路 (Main Circuit)', fontsize=15, fontweight='bold', pad=8)

# Bus positions
LX, NX = 2.5, 9.5
YM = 30   # top
YB = 3    # bottom

# L and N bus labels
ax_main.text(LX, YM+0.5, 'L', ha='center', va='bottom', fontsize=14, fontweight='bold')
ax_main.text(NX, YM+0.5, 'N', ha='center', va='bottom', fontsize=14, fontweight='bold')

# ── Draw L bus segments ──
v(ax_main, LX, YM, 28.5)
# QF breaker
breaker(ax_main, LX, 28)
v(ax_main, LX, 27.3, 25)
# KM1 main contact on L
main_contact(ax_main, LX, 24.2)
ax_main.text(LX+0.55, 24.2, 'KM1', ha='left', va='center', fontsize=9)
v(ax_main, LX, 23.5, 21.5)
# KM2 main contact on L (crossover to start winding)
main_contact(ax_main, LX, 20.8)
ax_main.text(LX+0.55, 20.8, 'KM2', ha='left', va='center', fontsize=9)
v(ax_main, LX, 20, 18)

# FR thermal on L
thermal(ax_main, LX, 17)
v(ax_main, LX, 16.3, 14.5)

# Main winding on L side
winding(ax_main, LX, 14.5, 11.5, '主绕组\n(运行)')
v(ax_main, LX, 11.5, 9)

# ── Draw N bus segments ──
v(ax_main, NX, YM, 25)
# KM1 main contact on N
main_contact(ax_main, NX, 24.2)
ax_main.text(NX+0.55, 24.2, 'KM1', ha='left', va='center', fontsize=9)
v(ax_main, NX, 23.5, 21.5)
# KM2 main contact on N (crossover to main winding)
main_contact(ax_main, NX, 20.8)
ax_main.text(NX+0.55, 20.8, 'KM2', ha='left', va='center', fontsize=9)
v(ax_main, NX, 20, 18)

# FR thermal on N
thermal(ax_main, NX, 17)
v(ax_main, NX, 16.3, 14.5)

# Start winding branch (from N side after KM1 / from L side after KM2)
# After KM1 on N side → capacitor + centrifugal switch → start winding
# After KM2 on L side → capacitor + centrifugal switch → start winding
# These join through capacitor branch

# Junction node after KM1-N
h(ax_main, NX, 6.5, 21)
jdot(ax_main, 6.5, 21)
v(ax_main, 6.5, 21, 19.5)

# Capacitor on the start winding branch
capacitor(ax_main, 6.5, 18.5)
v(ax_main, 6.5, 17.7, 16.5)

# Centrifugal switch in parallel with capacitor
v(ax_main, NX, 21, 18)
centrifugal(ax_main, NX, 17.3)
v(ax_main, NX, 16.5, 14.5)

# Start winding
winding(ax_main, 6.5, 14.5, 11.5, '启动绕组\n(启动)')

# KM2 crossover from L side: after KM2-L, go to start winding branch
v(ax_main, LX, 20, 19.5)
h(ax_main, LX, 6.5, 19.5)
jdot(ax_main, 6.5, 19.5)

# KM2 crossover from N side: after KM2-N, go to main winding branch
v(ax_main, NX, 20, 14.5)
# Actually N after KM2 should join the main winding path
# Let me simplify: after KM2-N, it goes to LX side (main winding)
h(ax_main, NX, LX, 14.5)
jdot(ax_main, LX, 14.5)

# Winding bottom junction - both windings join
v(ax_main, 6.5, 11.5, 9)
h(ax_main, LX, 6.5, 9)
jdot(ax_main, LX, 9)
jdot(ax_main, 6.5, 9)

# Motor
motor_circle(ax_main, (LX+6.5)/2, 7)
v(ax_main, (LX+6.5)/2, 9, 8.2)

# PE ground
v(ax_main, (LX+NX)/2, 6, YB+1)
ground(ax_main, (LX+NX)/2, YB+1)

# ── Crossover legend ──
ax_main.text(1, 21.5, 'KM1闭合:\nL→主绕组\nN→启动绕组\n(正转)', fontsize=8, ha='center',
             bbox=dict(boxstyle='round', fc='#e8f5e9', ec='gray', alpha=0.8))
ax_main.text(1, 18.5, 'KM2闭合:\nL→启动绕组\nN→主绕组\n(反转)', fontsize=8, ha='center',
             bbox=dict(boxstyle='round', fc='#fce4ec', ec='gray', alpha=0.8))

# ═══════════════════════════════════════════════
#  控制电路 CONTROL CIRCUIT  (right panel)
# ═══════════════════════════════════════════════
ax_ctrl.set_title('控制电路 (Control Circuit)', fontsize=15, fontweight='bold', pad=8)

CL, CN = 3, 10  # control L, N bus x
CT, CB = 30, 3  # control top, bottom

# Bus labels
ax_ctrl.text(CL, CT+0.5, 'L', ha='center', va='bottom', fontsize=14, fontweight='bold')
ax_ctrl.text(CN, CT+0.5, 'N', ha='center', va='bottom', fontsize=14, fontweight='bold')

# Control power buses
v(ax_ctrl, CL, CT, CB)
v(ax_ctrl, CN, CT, CB)

# Fuse FU on L
fuse(ax_ctrl, CL, CT-1, 'FU')

# ── Rungs from L to N (left to right) ──

# --- Rung Y=27.5 : FR-NC (overload) + SB1 (stop) ---
RY0 = 27.5
h(ax_ctrl, CL, CL+1.2, RY0)
nc_aux(ax_ctrl, CL+1.7, RY0, 'FR')
h(ax_ctrl, CL+2.2, CL+3, RY0)
nc_button(ax_ctrl, CL+3.6, RY0, 'SB1')
h(ax_ctrl, CL+4.2, CL+5, RY0)
jdot(ax_ctrl, CL+5, RY0)  # T-junction to forward/reverse branches

# --- FORWARD BRANCH (upper) ---
# Horizontal from T to SB2
h(ax_ctrl, CL+5, CL+5.8, RY0)
no_button(ax_ctrl, CL+6.4, RY0, 'SB2')
h(ax_ctrl, CL+7, CL+7.5, RY0)
# KM2 NC interlock
nc_aux(ax_ctrl, CL+8, RY0, 'KM2')
h(ax_ctrl, CL+8.5, CL+9, RY0)
# KM1 coil
coil(ax_ctrl, CL+9.5, RY0, 'KM1')
h(ax_ctrl, CL+10, CN, RY0)

# --- KM1 self-holding contact (parallel with SB2, drawn below) ---
RY_HOLD1 = 25
v(ax_ctrl, CL+5.5, RY0, RY_HOLD1)
h(ax_ctrl, CL+5.5, CL+7.2, RY_HOLD1)
no_aux(ax_ctrl, CL+7.7, RY_HOLD1, 'KM1')
v(ax_ctrl, CL+8.3, RY_HOLD1, RY0)
jdot(ax_ctrl, CL+8.3, RY0)
jdot(ax_ctrl, CL+5.5, RY0)

# --- REVERSE BRANCH (lower) ---
RY_REV = 22
v(ax_ctrl, CL+5, RY0, RY_REV)
jdot(ax_ctrl, CL+5, RY_REV)
h(ax_ctrl, CL+5, CL+5.8, RY_REV)
no_button(ax_ctrl, CL+6.4, RY_REV, 'SB3')
h(ax_ctrl, CL+7, CL+7.5, RY_REV)
# KM1 NC interlock
nc_aux(ax_ctrl, CL+8, RY_REV, 'KM1')
h(ax_ctrl, CL+8.5, CL+9, RY_REV)
# KM2 coil
coil(ax_ctrl, CL+9.5, RY_REV, 'KM2')
h(ax_ctrl, CL+10, CN, RY_REV)

# --- KM2 self-holding contact (parallel with SB3) ---
RY_HOLD2 = 20
v(ax_ctrl, CL+5.5, RY_REV, RY_HOLD2)
h(ax_ctrl, CL+5.5, CL+7.2, RY_HOLD2)
no_aux(ax_ctrl, CL+7.7, RY_HOLD2, 'KM2')
v(ax_ctrl, CL+8.3, RY_HOLD2, RY_REV)
jdot(ax_ctrl, CL+8.3, RY_REV)
jdot(ax_ctrl, CL+5.5, RY_REV)

# ── Operation notes ──
ax_ctrl.text(6, 17, '动作原理:', fontsize=10, fontweight='bold')
ax_ctrl.text(6, 15.5, '正转: 按SB2 → KM1吸合', fontsize=9)
ax_ctrl.text(6, 14.5, '  KM1主触点闭合 → 电机正转', fontsize=9)
ax_ctrl.text(6, 13.5, '  KM1自锁触点闭合 → 保持', fontsize=9)
ax_ctrl.text(6, 12.5, '  KM1常闭互锁断开 → 防止KM2动作', fontsize=9)
ax_ctrl.text(6, 11, '反转: 按SB3 → KM2吸合', fontsize=9)
ax_ctrl.text(6, 10, '  KM2主触点闭合 → 电机反转', fontsize=9)
ax_ctrl.text(6, 9, '  KM2自锁触点闭合 → 保持', fontsize=9)
ax_ctrl.text(6, 8, '  KM2常闭互锁断开 → 防止KM1动作', fontsize=9)
ax_ctrl.text(6, 6.5, '停止: 按SB1 / FR过载保护', fontsize=9)
ax_ctrl.text(6, 5.5, '换向必须先按停止!', fontsize=9, fontweight='bold', color='red')

# ── Legend ──
legend_items = [
    ('QF', '断路器'),
    ('FU', '熔断器'),
    ('KM1', '正转接触器'),
    ('KM2', '反转接触器'),
    ('FR', '热继电器'),
    ('SB1', '停止按钮'),
    ('SB2', '正转按钮'),
    ('SB3', '反转按钮'),
    ('C', '启动电容'),
    ('S', '离心开关'),
]
y_leg = 4
for i, (sym, desc) in enumerate(legend_items):
    ax_ctrl.text(1.5, y_leg - i*0.6, f'{sym}: {desc}', fontsize=8)

# ── Footer ──
fig.text(0.5, 0.005, '单相电机正反转控制电路 | 电气互锁 + 机械互锁 | KM1/KM2 不允许同时吸合',
         ha='center', fontsize=10, style='italic', color='gray')

plt.tight_layout(rect=[0, 0.02, 1, 0.98])
plt.savefig('C:/Users/32539/Desktop/code/single_phase_motor_fwd_rev.png',
            dpi=180, bbox_inches='tight', facecolor='white', edgecolor='none')
plt.close()
print("Done: single_phase_motor_fwd_rev.png")
