# 月球转移发射窗口计算器 · 停泊轨道滑行方案

Lunar Transfer Launch Window Calculator (parking-orbit coast TLI scheme)

单页 Three.js 应用, 实现经嫦娥五号/六号、鹊桥二号实测数据验证的真实发射方案
(验证过程见 `../study_notes.md` §11 与 `../verify_scenario.py`):

**固定射向(落区约束走廊内) → ~200 km 停泊轨道 → 滑行至共面相位点 → TLI 点火入 LTO**

即官方"窄窗口多轨道"(变射向 + 变滑行时间) 设计。LTO 轨道面 =
span{发射场@发射, 月球@到达}, 不要求与白道面重合。

## 背景

项目第一代工具 (仓库根目录 `index.html`, 保留作参考) 假设转移轨道位于白道面内、
发射窗口 = 发射场随地球自转穿越白道面的时刻 (升/降交点各一次), 并据此做了
Hohmann 型转移、TLI/LOI ΔV、月相与本影锥的完整 3D 可视化。用它计算文昌发射的
嫦娥五号/六号、鹊桥二号, 窗口时刻与实际发射差 1.4–13.7 小时 — 假设被证伪。

用 JPL DE440s 历表对三次任务做几何反演 (`verify_scenario.py`), 并与 Bill Gray
Find_Orb 光学定轨对比:

| 任务 | 预测 LTO 倾角 | 实测倾角 | 反演射向 | 滑行解 |
|---|---|---|---|---|
| 嫦娥五号 2020-11-23 | 21.51° | 21.298° | 99.3° | 21.7 min |
| 鹊桥二号 2024-03-20 | 22.93° | 21.976° | 102.3° | 11.4 min |
| 嫦娥六号 2024-05-03 | 23.54° | (无实测) | 103.5° | 23.1 min |

三次任务 LTO 面与白道面夹角分别为 4.3°/51.3°/7.8° (鹊桥二号到达时月球近赤道
节点, 51° 夹角仍正常奔月), 证实 LTO 面只需包含"月球@到达"方向; 射向全部落在
文昌落区走廊内; 滑行解与公开飞行剖面 (CZ-5 二级滑行设计值 ~1000 s, 器箭分离
~T+2200 s) 同量级。本工具即基于该验证过的几何构建。相关数据: `../data/*.tle`
(Find_Orb 密切根数; e≈0.97 时 SGP4 平根数无意义), `../verify_results.txt`。

## 运行

- 双击 `启动.command` (本地起 http 服务并打开浏览器) — 推荐;
- 或任意静态服务器: `python3 -m http.server 8642` 后开 `http://localhost:8642/index.html`;
- 直接双击 `index.html` (file://) 也能算, 但 Chrome 会拦截本地贴图, 地球退化为纯色。

完全离线可用: Three.js r144 与地球贴图 (NASA Blue Marble) 均为本地文件。

在线版 (HF Space, GitHub Actions 自动部署, 见 `../DEPLOY.md`):
https://zhuoxiaowang-lunar-launch-window.static.hf.space

## 算法

对每个候选发射时刻 tL (全天 2 min 网格):

1. `solveGeometry`: n̂ = unit(r̂_site(tL) × r̂_moon(tA)), tA = tL + 转移时间。
   由 n̂ 得倾角 i、升交点 Ω; 射向由顺行切向速度方向 v̂ = n̂ × r̂_site 在当地
   地平系分解唯一确定 (非 asin 双解);
2. 走廊筛选: Az ∈ [Az_min, Az_max] (落区约束);
3. `coastSolutions` 滑行闭合 (TLI 近地点切向点火假设):
   - 航程角闭合: θ_total = θ_ascent + ω_park·t_coast + Δν
   - 时间闭合:   T_transfer = T_ascent + t_coast + TOF_Kepler(Δν)
   联立扫根求 t_coast → Δν, e, 远地点, ΔV, C3。允许 Δν > 180°
   (月球近地点月份的近远地点到达, 如嫦娥六号);
4. 连续可行时段 = 当日窗口; 30 天扫描给出逐日可发射分钟数;
5. 月球引力修正 (默认开, 可关): 二体闭合瞄准"月球@到达"质心, 实飞会被月球
   引力拉弯加速 (典型: 提前 ~6 h 到达、直接撞月)。修正用 RK4 四体积分
   (地+月+日点质量, Meeus 历表 Catmull-Rom 插值) 在窗口中心打靶, 解
   (射向偏置 dAz, 滑行偏置 dtc) 使 近月点高度 = 目标值(默认 150 km) 且
   近月点时刻 = 设定到达时刻; 全天扫描套用该偏置 (偏置随发射时刻近似常数,
   表现为窗口整体平移 ~15 min, 宽度不变)。求解分三段: 滑行偏置二分校时刻
   (到达贴近远地点时 TOF 对 TLI 能量单边奇异, 只有滑行拱线杠杆平滑,
   ~6 h/min) → 射向偏置弦截校高度 ("近月距-侧偏"是 V 型褶皱, 需从中心
   向外找变号区间; 两侧各有一支解, "偏置侧"选项决定 LOI 轨道面取向与窗口
   平移方向) → 2×2 牛顿抛光。CE-7 复核: 2026-08-24 文昌 TOF 120 h,
   +侧偏置 +1.34°, 与 DE440s/DOP853 全数值解 (+1.36°) 一致。

月球星历为 Meeus ch.47 截断级数 (32 项经度/距离 + 20 项纬度 + A1..A3 修正),
对比 DE440s: 距离差 ~2 km, 白道倾角差 ~0.01°, 求解结果与 skyfield 版一致
(嫦娥五号历元: az 差 0.04°, i 差 0.01°, 滑行解相同)。

## 界面

- 左栏: 发射场/日期/转移时间/走廊/停泊高度/最长滑行 (默认 20 min)、
  月球引力修正开关与偏置侧、近月点目标 (默认 150 km) + 上升段假设 (高级);
- 中栏: 3D (赤道惯性系)。地球昼夜贴图随 GMST 自转, 白道面/LTO 面/赤道面/黄道面
  可切换, 地面射向走廊扇面, 上升段-停泊滑行弧-TLI 点-LTO 全链路;
  底部时间轴可播放全任务 (航天器沿真实 Kepler 相位推进, 月球走真实星历轨迹);
- 右栏: 窗口列表 (窗口内时刻滑条)、方位角-时刻图 (阴影=走廊, 橙=可发射)、
  滑行时间图、30 天扫描图、选定方案的 LTO 根数、月引力修正面板与到达月相。

## 已知简化

- 脉冲 TLI (真实为 ~6 min 有限推力弧, TLI 时刻居中等效);
- 月球引力修正为"窗口中心标定 + 全天套用"(选定时刻面板亦引用标定值);
  30 天扫描沿用最近一次当日标定偏置; 3D 场景仍绘二体 LTO 椭圆;
- 上升段用 (耗时, 航程角) 两参数概化, 默认 800 s / 20°;
- 真实任务窗口宽度 (~50 min/天) 还受载荷余量、测控、轨道条数等约束,
  本工具走廊内可行段一般更宽 — 收窄走廊 (如 96°–104°) 可复现真实量级。

## 仓库结构

```
launch_lunar/
  coast_tool/          -- 本工具 (index.html + vendor/ + assets/ + 启动.command)
  index.html           -- 第一代"直接入白道面"工具 (已被证伪, 保留作参考)
  study_notes.md       -- 研究笔记 11 章 (轨道力学推导、历史任务分析、方案验证)
  verify_scenario.py   -- DE440s 验证脚本 (skyfield), verify_results.txt 为输出
  data/*.tle           -- Bill Gray Find_Orb 光学定轨轨道
  DEPLOY.md            -- GitHub + Hugging Face 部署说明
```

## 参考文献

1. Meeus, J. *Astronomical Algorithms*, 2nd ed., Willmann-Bell, 1998
2. Bate, Mueller, White. *Fundamentals of Astrodynamics*, Dover, 1971
3. 刘林, 侯锡云.《深空探测器轨道力学》, 电子工业出版社
4. 裴照宇等, 深空探测学报 2021, 8(3); Li Dong et al., JDSE 2021, 8(4) ("窄窗口多轨道")
5. Bill Gray pseudo-MPECs (projectpluto.com); CNSA/新华社发射公告
6. NASA Apollo Mission Reports; 中国探月工程中心公开技术资料

## License

MIT
