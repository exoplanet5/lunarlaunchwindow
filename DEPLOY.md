# 部署方案: GitHub (源码+CI) + Hugging Face Spaces (托管)

本项目是纯前端静态页面 (无后端), 适合 **GitHub 存源码 + Actions 自动同步到
HF Static Space 托管** 的组合。推送 main 分支即自动上线。

```
GitHub repo (源码/历史/CI)
   └─ push main ──▶ GitHub Action (deploy-hf.yml)
                       └─ 组装 coast_tool/ + Space 头信息 ──▶ HF Space (Static, CDN 托管)
                                    https://huggingface.co/spaces/<你>/lunar-launch-window
```

## 一次性准备 (约 10 分钟)

1. **GitHub 仓库** (本目录尚未 git 化):

   ```bash
   cd ~/launch/launch_lunar
   git init -b main
   printf '__pycache__/\n.DS_Store\n_space/\n' > .gitignore
   git add -A && git commit -m "lunar launch window: coast_tool + verification"
   gh repo create launch-lunar --public --source=. --push   # 或网页建仓后 git push
   ```

2. **HF Space**: huggingface.co → New Space → 名称 `lunar-launch-window`,
   SDK 选 **Static**, Public。(建好后内容会被 CI 覆盖, 无需手动传文件)

3. **HF 写权限 token**: HF → Settings → Access Tokens → New token,
   类型选 Fine-grained, 勾选该 Space 的 **Write** 权限 (或直接用 Write 类型)。

4. **GitHub Secret**: GitHub 仓库 → Settings → Secrets and variables →
   Actions → New repository secret, 名称 `HF_TOKEN`, 值为上一步的 token。

5. 编辑 `.github/workflows/deploy-hf.yml` 顶部 `HF_SPACE:` 为 `你的HF用户名/lunar-launch-window`。

之后每次 `git push`(涉及 coast_tool/ 的改动)自动部署; 也可在 GitHub →
Actions 页面手动触发 (workflow_dispatch)。

## 要点与说明

- **为什么可行**: coast_tool 全部资源为本地相对路径 (vendor/three.min.js,
  assets/*.jpg), 无 CDN、无后端、无 API key; HF Static Space 就是一个静态
  HTTP 服务器 + CDN, 贴图同源加载, 没有 file:// 的 CORS 问题。
- **文件大小**: 最大 earth_day.jpg 2.6 MB, 低于 HF 需要 git-lfs 的 10 MB
  阈值, hf upload 直接传即可。
- **旧版工具**: 如需一并上线, 在 workflow 的 Assemble 步骤加
  `mkdir -p _space/classic && cp index.html _space/classic/` (注意旧版
  three.js 走 unpkg CDN, 需联网)。
- **Space 头信息**: Space 根 README.md 必须含 `sdk: static` 的 YAML front
  matter, workflow 会自动生成, 项目自身的 README 不受影响 (改名 ABOUT.md 随附)。
- **备选双镜像**: 想再挂一个 GitHub Pages 镜像的话, Settings → Pages →
  Source 选 GitHub Actions, 用官方 static 模板把 `coast_tool/` 作为
  artifact 上传即可; HF 与 Pages 互不影响。
- **嵌入分享**: HF Space 可直接 iframe 嵌入:
  `https://<你>-lunar-launch-window.static.hf.space` (Embed 按钮里有现成地址)。
