#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证文昌探月发射的"停泊轨道滑行"方案 (Chang'e 5, Chang'e 6, QueQiao-2).

两个模型对比:
  Model A (旧工具假设): 转移轨道位于白道面内, 发射窗口 = 发射场随地球自转
           穿越白道面的时刻.
  Model B (用户假设):   射向受落区约束 (东南向, 方位角走廊), 上面级先入低停泊
           轨道滑行, 滑行至与"到达时刻月球位置"共面的 TLI 点后再点火进入 LTO.
           LTO 平面 = 包含 发射场位置(发射时刻) 与 月球位置(到达时刻) 的平面,
           不必与白道面重合.

对每个任务:
  1. 用 DE440s 计算发射时刻发射场 GCRS 位置、到达时刻月球位置 (真赤道系).
  2. Model B 隐含的 LTO 轨道面 → 倾角、发射方位角 (应落在文昌射向走廊内).
  3. LTO 面与白道面夹角 (应明显非零 → 证明不是"直接入白道面").
  4. Model A 预测的当日窗口 (发射场穿白道面时刻) vs 实际发射时刻 (应差数小时).
  5. 切向 TLI 闭合解: 假设 TLI 在近地点 (200 km), 解滑行时间使 Kepler 飞行
     时间与相位角同时闭合 → 得到滑行时长、远地点、TLI ΔV, 与公开数据对比.
"""
import numpy as np
from skyfield.api import Loader, wgs84
from skyfield.framelib import true_equator_and_equinox_of_date as tete

load = Loader('~/JPLDE')
ts = load.timescale()
eph = load('de440s.bsp')
earth, moon = eph['earth'], eph['moon']

MU = 398600.4418          # km^3/s^2
R_EQ = 6378.137
DEG = np.pi / 180

WENCHANG = wgs84.latlon(19.6145, 110.9510, elevation_m=20)

# 上升段假设 (CZ-5/CZ-8 量级, 入轨点相对发射场的航程角与耗时)
T_ASCENT = 800.0          # s, 起飞到停泊轨道入轨
TH_ASCENT = 20.0          # deg, 上升段航程角
RP_ALT = 200.0            # km, 停泊轨道/LTO 近地点高度

# 发射时刻: CNSA/新华社; 实测倾角: Bill Gray Find_Orb 光学定轨 (J2000 赤道系)
MISSIONS = [
    dict(name="嫦娥五号 Chang'e 5 (CZ-5, 2020)",
         launch=(2020, 11, 23, 20, 30, 22), loi=(2020, 11, 28, 12, 58, 0),
         i_meas=21.298,
         note="公开: 器箭分离 ~T+2200s, 二级滑行设计值1000s; LTO 200x410000 km; "
              "窗口 3天x50min; 实测 i=21.298° q=6489 Q=400484 km"),
    dict(name="鹊桥二号 QueQiao-2 (CZ-8, 2024)",
         launch=(2024, 3, 20, 0, 31, 28), loi=(2024, 3, 24, 16, 46, 0),
         i_meas=21.976,
         note="公开: 器箭分离 T+24min; LTO 200x420000 km; 窗口 3天x2轨道; "
              "实测 i=21.976° q=6603 Q=409537 km (3-20 历元)"),
    dict(name="嫦娥六号 Chang'e 6 (CZ-5, 2024)",
         launch=(2024, 5, 3, 9, 27, 29), loi=(2024, 5, 8, 2, 12, 0),
         i_meas=None,
         note="公开: 器箭分离 ~T+37min; LTO 200x~380000 km; 窗口 2天x50min(10条轨道); "
              "倾角无实测 (火箭末级TLE为月球借力后)"),
]


def unit(v):
    return v / np.linalg.norm(v)


def tete_vec(pos, t):
    """GCRS position -> true equator & equinox of date frame."""
    return tete.rotation_at(t) @ pos


def site_pos_tete(t):
    return tete_vec(WENCHANG.at(t).position.km, t)


def moon_geo_tete(t):
    """Geocentric Moon position & velocity in true-of-date frame (km, km/s)."""
    bm = moon.at(t)
    be = earth.at(t)
    r = tete_vec(bm.position.km - be.position.km, t)
    v = tete_vec(bm.velocity.km_per_s - be.velocity.km_per_s, t)
    return r, v


def kepler_tof(rp, e, nu_deg):
    """近地点(ν=0)到 ν 的飞行时间, 椭圆."""
    a = rp / (1 - e)
    nu = nu_deg * DEG
    E = 2 * np.arctan2(np.sqrt(1 - e) * np.sin(nu / 2),
                       np.sqrt(1 + e) * np.cos(nu / 2))
    M = E - e * np.sin(E)
    if M < 0:
        M += 2 * np.pi
    return M / np.sqrt(MU / a**3)


def analyze(m):
    tL = ts.utc(*m['launch'])
    tA = ts.utc(*m['loi'])
    tof_total = (tA.tt - tL.tt) * 86400.0

    r_site = site_pos_tete(tL)
    r_moon, v_moon = moon_geo_tete(tA)
    d_moon = np.linalg.norm(r_moon)
    dec_moon = np.degrees(np.arcsin(unit(r_moon)[2]))

    # 白道面 (到达时刻)
    n_moon = unit(np.cross(r_moon, v_moon))
    i_moon = np.degrees(np.arccos(np.clip(n_moon[2], -1, 1)))

    # ---- Model B: LTO 平面 = span{r_site(tL), r_moon(tA)} ----
    u1, u2 = unit(r_site), unit(r_moon)
    n = np.cross(u1, u2)
    theta = np.degrees(np.arctan2(np.linalg.norm(n), np.dot(u1, u2)))
    n = unit(n)
    if n[2] < 0:          # 顺行
        n = -n
        theta = 360.0 - theta
    i_lto = np.degrees(np.arccos(np.clip(n[2], -1, 1)))

    # 发射方位角 (球面关系 cos i = cos φ sin Az, 用地心纬度)
    phi_gc = np.arcsin(u1[2])
    s = np.cos(i_lto * DEG) / np.cos(phi_gc)
    az_ne = np.degrees(np.arcsin(np.clip(s, -1, 1)))
    az_se = 180.0 - az_ne
    # 唯一方位角: 顺行切向速度方向在当地地平系的分解
    v_dir = np.cross(n, u1)
    east = unit(np.array([-u1[1], u1[0], 0.0]))
    north = np.cross(u1, east)
    az_true = np.degrees(np.arctan2(np.dot(v_dir, east), np.dot(v_dir, north))) % 360

    # LTO 面 vs 白道面
    plane_gap = np.degrees(np.arccos(np.clip(np.dot(n, n_moon), -1, 1)))

    # 发射时刻发射场偏离白道面的角度 (直接入白道面模型要求 ~0)
    off_plane = np.degrees(np.arcsin(np.clip(np.dot(u1, n_moon), -1, 1)))

    # ---- Model A: 当日发射场穿越白道面的时刻 ----
    day0 = ts.utc(m['launch'][0], m['launch'][1], m['launch'][2])
    tt_grid = ts.tt_jd(day0.tt + np.arange(0, 24 * 60 + 1) / (24 * 60.0))
    dots = np.array([np.dot(unit(site_pos_tete(t)), n_moon) for t in tt_grid])
    crossings = []
    for k in range(len(dots) - 1):
        if dots[k] * dots[k + 1] < 0:
            f = dots[k] / (dots[k] - dots[k + 1])
            crossings.append((k + f) / 60.0)   # hours UTC

    # ---- Model B 滑行时间闭合解 ----
    rp = R_EQ - 6.9 + RP_ALT   # 用平均半径量级即可; 取 6378-7+200
    om_park = np.degrees(np.sqrt(MU / rp**3))  # deg/s
    sols = []
    coasts = np.arange(0.0, 2 * 5400.0, 5.0)

    def f_close(tc):
        dnu = (theta - TH_ASCENT - om_park * tc) % 360.0
        # 允许略过远地点到达 (ν>180°, 月球近地点月份的长飞行时间方案)
        if not (95.0 < dnu < 250.0):
            return None
        e = (d_moon - rp) / (rp - d_moon * np.cos(dnu * DEG))
        if not (0 < e < 1):
            return None
        tof_c = kepler_tof(rp, e, dnu)
        tof_req = tof_total - T_ASCENT - tc
        return tof_c - tof_req, dnu, e

    prev = None
    for tc in coasts:
        cur = f_close(tc)
        if cur is not None:
            if prev is not None and prev[0] is not None and prev[0] * cur[0] < 0:
                # 线性内插求根
                tc_root = prev[2] + (tc - prev[2]) * prev[0] / (prev[0] - cur[0])
                res = f_close(tc_root)
                if res is not None:
                    _, dnu, e = res
                    a = rp / (1 - e)
                    ra = a * (1 + e) - R_EQ + 6.9   # 远地点高度
                    v_per = np.sqrt(MU * (2 / rp - 1 / a))
                    dv = v_per - np.sqrt(MU / rp)
                    sols.append(dict(coast=tc_root, dnu=dnu, e=e,
                                     apo=a * (1 + e), apo_alt=ra, dv=dv))
            prev = (cur[0], None, tc)
        else:
            prev = None

    # ---- 输出 ----
    print("=" * 78)
    print(m['name'])
    print(f"  发射 {tL.utc_strftime('%Y-%m-%d %H:%M:%S')} UTC  |  "
          f"近月 {tA.utc_strftime('%Y-%m-%d %H:%M:%S')} UTC  "
          f"(总飞行 {tof_total/3600:.1f} h)")
    print(f"  [{m['note']}]")
    print(f"  月球@到达: 距离 {d_moon:,.0f} km, 赤纬 {dec_moon:+.2f}°, "
          f"白道倾角(真赤道) {i_moon:.2f}°")
    print()
    print(f"  Model B — LTO 平面 (发射场@发射 × 月球@到达):")
    meas = (f"  ← 实测 {m['i_meas']:.2f}° (Find_Orb), 差 {abs(i_lto-m['i_meas']):.2f}°"
            if m.get('i_meas') else "")
    print(f"    LTO 倾角 i = {i_lto:.2f}°   (白道倾角 {i_moon:.2f}°){meas}")
    print(f"    发射方位角(唯一解) = {az_true:.1f}°  "
          f"[两支参考: NE {az_ne:.1f}° / SE {az_se:.1f}°] (文昌落区走廊 ~90–110°)")
    print(f"    LTO面 与 白道面 夹角 = {plane_gap:.2f}°  ← 若'直接入白道面'应≈0")
    print(f"    发射场→月球 惯性系航程角 θ = {theta:.1f}°")
    print()
    print(f"  Model A — 发射场穿白道面时刻 (旧工具的窗口):")
    hL = (m['launch'][3] + m['launch'][4] / 60 + m['launch'][5] / 3600)
    if crossings:
        for c in crossings:
            print(f"    {int(c):02d}:{int(c % 1 * 60):02d} UTC   "
                  f"(与实际发射差 {abs(c - hL):.1f} h)")
    else:
        print("    当日无穿越 (纬度/几何超限)")
    print(f"    实际发射 {int(hL):02d}:{int(hL % 1 * 60):02d} UTC")
    print(f"    发射时刻发射场偏离白道面 {off_plane:+.2f}° (以月心方向为正)")
    print()
    print(f"  Model B — 切向TLI闭合解 (近地点 {RP_ALT:.0f} km, "
          f"上升段 {T_ASCENT:.0f}s/{TH_ASCENT:.0f}°):")
    if sols:
        for s_ in sols:
            print(f"    滑行 {s_['coast']/60:6.1f} min → TLI后转移角 {s_['dnu']:6.1f}°, "
                  f"e={s_['e']:.5f}, 远地点高度 {s_['apo_alt']:,.0f} km, "
                  f"TLI ΔV={s_['dv']:.3f} km/s")
        print(f"    (对比公开: 器箭分离 ~T+37min ⇒ 滑行 ~10–20 min; "
              f"远地点 ~380000–420000 km)")
    else:
        print("    未找到闭合解 (检查假设)")
    print()


for mm in MISSIONS:
    analyze(mm)

print("=" * 78)
print("结论判据: 若 Model B 的东南支方位角落在 90–110° 走廊内、滑行解为 10–25 min、")
print("远地点接近公开值, 而 Model A 窗口与实际发射时刻差数小时、LTO面≠白道面,")
print("则证实: 采用受落区约束的固定射向 + 低停泊轨道滑行至共面 TLI 点的方案。")
