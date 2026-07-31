#!/bin/zsh
# 双击启动: 本地服务器 + 打开计算器
# (直接 file:// 打开也能用, 但 Chrome 下地球贴图会被 CORS 拦截, 退化为纯色地球)
cd "$(dirname "$0")"
( /usr/bin/python3 -m http.server 8642 >/dev/null 2>&1 & )
sleep 1
open "http://localhost:8642/index.html"
