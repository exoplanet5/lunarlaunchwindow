# Lunar Direct Transfer Launch Window Calculator

**月球直接转移轨道发射窗口计算器**

Interactive 3D visualization tool for computing and exploring lunar direct transfer mission launch windows. Built as a single-page web application with Three.js.

![Three.js](https://img.shields.io/badge/Three.js-0.160.0-black)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- **Launch window computation** -- calculates daily launch opportunities (ascending/descending node crossings of the lunar orbital plane) for any date and launch site
- **3D orbital visualization** -- interactive scene showing Earth, Moon, transfer orbit, parking orbit, and the lunar orbital plane (白道面)
- **Real-time lunar ephemeris** -- simplified Meeus algorithm for Moon/Sun positions with coordinate transforms (ecliptic / equatorial / scene)
- **Transfer orbit design** -- Hohmann-like ellipse from parking orbit to Moon, with TLI and LOI delta-v calculations
- **Moon phase display** -- canvas-rendered phase icon with illumination percentage and elongation
- **Shadow cones** -- Earth and Moon umbral shadow cone visualization
- **Texture mapping** -- NASA Blue Marble Earth texture (CDN, with fallback) and procedural Moon texture
- **Multiple launch sites** -- Wenchang (文昌), Xichang (西昌), KSC Kennedy

## Quick Start

No build step required. Open `index.html` directly in a modern browser, or serve it locally:

```bash
# Python
python3 -m http.server 8000

# Node.js
npx serve .
```

Then navigate to `http://localhost:8000`.

> **Note**: An internet connection is needed on first load to fetch Three.js (v0.160.0) from [unpkg](https://unpkg.com) CDN and the Earth texture.

## Usage

1. Select a **launch site** from the dropdown
2. Choose a **launch date**
3. Adjust **parking orbit altitude** (default 200 km) and **transfer time** (default 4.5 days)
4. Click **计算发射窗口** or change any parameter to update

The right panel displays:
- Moon phase and illumination
- Two daily launch windows (ascending/descending node) with local times
- Window width estimate (based on 200 m/s plane-change budget)
- Transfer orbit parameters (a, e, delta-v, C3)
- Moon position (ecliptic and equatorial coordinates)

The 3D viewport supports:
- **Left drag** -- rotate
- **Scroll** -- zoom
- **Right drag** -- pan
- **View presets** -- 默认 / 俯视 / 侧视 / 近地
- **Toggle layers** -- ecliptic plane, equatorial plane, lunar orbital plane, transfer orbit, labels, shadow cones
- **Click a launch window button** -- rotates Earth to show the launch site at that window time

## Physics Model

### Coordinate Systems

| System | Axes | Usage |
|--------|------|-------|
| Ecliptic | x: vernal equinox, y: 90deg ecl. lon, z: ecliptic north | Astronomical reference |
| Equatorial | x: vernal equinox, y: RA 90deg, z: celestial north | Launch window solving |
| Scene | x = x_ecl, y = z_ecl, z = -y_ecl | Three.js rendering |
| earthGroup | x: RA 0h, y: north pole, z: -RA 6h (right-handed) | Earth-fixed features |

### Launch Window Algorithm

1. Compute the **lunar orbital plane normal** (白道面法向量) in equatorial coordinates via ecliptic-to-equatorial rotation
2. Solve for **Local Sidereal Time** when the launch site position vector is perpendicular to the normal: `r_site . n_eq = 0`
3. Convert LST to UTC using Greenwich Sidereal Time at epoch
4. **Window width**: `W = 2 * dV_budget / (V_TLI * omega_E * sqrt(sin^2(i_eq) - sin^2(phi)))`

### Transfer Orbit

- Hohmann-like ellipse in the lunar orbital plane
- Perigee at parking orbit altitude, apogee at Moon distance
- Visual orbit uses adjusted (a, e) so perigee matches the visual parking orbit radius, ensuring smooth tangency at the TLI point

### Lunar Ephemeris

Simplified Meeus algorithm with principal perturbation terms:
- 8 terms for ecliptic longitude
- 6 terms for ecliptic latitude  
- 5 terms for distance
- Accuracy: ~0.5deg in longitude, ~0.3deg in latitude

## Project Structure

```
launch_lunar/
  index.html       -- Complete application (HTML + CSS + JS, ~1700 lines)
  study_notes.md   -- Detailed study notes in Chinese (理论推导与实现文档)
  README.md        -- This file
```

## Technical Notes

- **Zero build dependencies** -- pure ES modules loaded from CDN via `<script type="importmap">`
- **Visual scale**: Moon orbit radius = 20 units; Earth and Moon radii enlarged ~3x for visibility
- **Parking orbit / transfer orbit tangency**: both orbits share the same in-plane basis vectors, guaranteeing the TLI point lies exactly on the parking orbit circle with continuous velocity direction
- **Shadow cones**: Earth umbra ~60 units (physical ~1.38M km), Moon umbra ~19 units (physical ~374K km), oriented anti-sunward
- **Stars at r = 8000-12000** and **Sun marker at r = 2000** to eliminate parallax when zoomed to 2x Moon orbit distance

## References

1. Meeus, J. *Astronomical Algorithms*, 2nd ed., Willmann-Bell, 1998
2. Bate, Mueller, White. *Fundamentals of Astrodynamics*, Dover, 1971
3. 刘林, 侯锡云.《深空探测器轨道力学》, 电子工业出版社
4. NASA Apollo Mission Reports
5. 中国探月工程中心公开技术资料

## License

MIT

---

## 2026-08 更新: coast_tool/ 停泊轨道滑行方案计算器

原 index.html 假设"直接入白道面", 经嫦娥五号/六号、鹊桥二号实测数据验证不成立
(LTO 面 ≠ 白道面, 见 study_notes.md §11)。新版 `coast_tool/` 实现真实方案:
落区约束射向走廊 → 停泊轨道滑行 → 共面相位点 TLI ("窄窗口多轨道")。
运行: 双击 `coast_tool/启动.command`。验证脚本: `verify_scenario.py`。
