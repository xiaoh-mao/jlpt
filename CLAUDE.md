# JLPT 模考

官方《公式問題集》2012 + 2018 第二集 × N1–N5 共 10 套的桌面刷题工具；用法、功能见 `README.md`。
`JLPT模考.bat` → `lib\server.ps1`（本地 HttpListener）→ Edge `--app` 窗口，前端在 `app/`。

- **运行时零依赖**（只有 PowerShell + Edge），别引入 Python/Node。
- `scratch/` 不是草稿：生成数据的 Python 流水线在这里，别清。
  `app/data/` 的 `keys.js` `tests.js` `trans.js` 由它生成，别手改；各脚本用法写在文件开头。`levels.js` 手写。
- **跟 TOPIK 模考（另一个仓库 github.com/xiaoh-mao/topik）共用一套内核**：两个仓库克隆到同一个文件夹下，文件夹名就叫 `jlpt` 和 `topik`。
  共用文件（清单是 `lib/sync-core.ps1` 的 `$Files`）两边必须一模一样：改哪边都行，改完跑 `pwsh -File lib\sync-core.ps1`
  复制到另一边（两边都改过会报冲突），再两边各自提交。只属于 JLPT 的（读数据、算分、说明文字、导入自备卷）放
  `app/exam.*` `lib/exam.ps1`；`app/data/` 文件名两边一样、格式各管各的。两边 `README.md` 的界面说明是平行写的，改界面两边一起改。
- **外挂题包**：同级文件夹 `jlpt-历年真题\`（不在仓库、不上传，有自己的 CLAUDE.md）。挂钩只有 `lib/exam.ps1` 的 `/api/extra/`
  和 `app/exam.js` 的 `loadExtra`，它不在就当没有；它的 `pack.js` 就是 `addJlpt()` 的参数，改了这个或 `app/data/` 的格式，那边要重新生成。
- 仓库带着 `papers/` 的页面图和 mp3（做题只用这些），不带原版 PDF 和 `papers/自备/`（`.gitignore`）；
  PDF 只有流水线读，要重新生成数据先跑 `sh scratch/download.sh` 再下，再跑 `render.py`。

## Gotchas
- `.ps1` 里中文乱码或解析报错 -> 没存成 UTF-8 with BOM -> 含中文的 `.ps1` 一律带 BOM；`.bat` 反过来必须纯 ASCII 无 BOM。
  `.gitattributes` 是 `* -text`，git 原样存，不会改 BOM 和换行。
- 生成数据要用仓库外的东西（做题不用）：`pip install -r scratch\requirements.txt`；ffmpeg（环境变量 `FFMPEG` 或 PATH，
  作者本机是 LosslessCut 带的）；Git 带的 pdftotext（抄正答表）；Windows OCR 中文识别器（2012 扫描卷）。换电脑要重装。

## State
- 完成并实测，可用。2026-09-26 拆成内核 + `exam.*`，行为跟 TOPIK 做成一样（首页一套一行、听力原文对过答案才给看）。
- 2026-09-27 公开在 github.com/xiaoh-mao/jlpt（用户定的：公开、带卷子页面图和录音）。
