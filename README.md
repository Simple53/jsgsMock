<div align="center">
  <img src="web/icon.svg" width="96" height="96" alt="jsgsMock Icon" />
  <h1>jsgsMock</h1>
  <p><strong>江苏高校教师岗前培训全真题库与精讲学习系统</strong></p>
  <p><strong>Jiangsu Higher Education Teacher Pre-service Training Quiz & Video Learning System</strong></p>
  <p>
    <a href="#中文介绍">中文介绍</a> ·
    <a href="#english-documentation">English Documentation</a> ·
    <a href="https://simple53.github.io/jsgsMock/">Online Demo</a> ·
    <a href="https://github.com/Simple53/jsgsMock/releases">Android APK</a>
  </p>
</div>

---

<h2 id="中文介绍">中文介绍</h2>

**jsgsMock** 是一款专为江苏高校教师岗前培训考试打造的纯扁平化、零广告、支持全离线运行的刷题与名师视频学习系统。内置 **2026 官网最新真题** 与 **历年题库** 双题库引擎，涵盖《高等教育学》《高等教育心理学》《高校教师职业道德修养》《高等教育法规概论》等全部统考科目，并集成 123 节官方名师视频课程与多服务商 AI 助教。

- **开源仓库**：[https://github.com/Simple53/jsgsMock](https://github.com/Simple53/jsgsMock)（欢迎点击右上角 **Star** 支持本项目）
- **在线体验**：[https://simple53.github.io/jsgsMock/](https://simple53.github.io/jsgsMock/)
- **安卓客户端**：前往 [Releases 页面](https://github.com/Simple53/jsgsMock/releases) 下载安装 `jsgsMock.apk`，支持应用内一键检查更新。

### 一、核心功能特色

#### 1. 首页与每日考点
- **双题库无缝切换**：支持在首页一键切换「2026官网最新真题」与「历年题库」，并提供新旧题库对照 Excel 总表下载。
- **每日一句全屏精读**：每日从真题解析中甄选高频考点金句，支持一键动画刷新与点击全屏沉浸式阅读考点溯源。
- **极简顶栏工具**：集成日间/护眼/深色三态主题颜色切换、GitHub 仓库直达、收藏题目专练、每日学习打卡与平滑展开式全局搜索。

#### 2. 视频课程与手势播放器
- **5 大科目 123 节精讲**：按科目完整收录统编名师视频，视频与考点大纲同屏切换，课程导航占满整排，选集卡片横向滑动。
- **专业影院级交互**：
  - 播放器内部集成**全屏切换按钮**与**横竖屏切换按钮**；
  - 保留移动端丝滑手势：左侧上下滑动调节画面亮度、右侧上下滑动调节音量大小、水平左右滑动预览并调节播放进度；
  - 支持点击打开播放源菜单（在「官方 CDN」与「国内加速」间按需切换）、多档倍速调节与毫秒级断点记忆续播。

#### 3. 刷题工作台与 AI 名师助教
- **科学刷题体验**：支持背题模式与做题模式、手写草稿画板（带单步撤销）、左右滑屏切题与 PC 全键盘/滚轮翻题；多选题采用复选框勾选并确认提交机制，杜绝提前剧透答案。
- **多模型 AI 助教体系**：
  - 支持接入 DeepSeek、Kimi、通义千问、智谱清言、ChatGPT、硅基流动、OpenRouter 及自定义 OpenAI 兼容端点；
  - AI 模型设置采用无外框极简列表展示，支持点击设为默认模型及勾选批量删除；
  - 支持题目下方一键流式生成考点精解，以及可自由拖拽位置的悬浮 AI 助教多轮追问。

#### 4. 错题抗遗忘、全真模考与多端同步
- **艾宾浩斯抗遗忘复习**：错题本与我的收藏均支持「记得 / 模糊 / 忘记」三维记忆反馈，动态计算复习临界期。
- **分科目与综合全真模考**：支持按单科目或 5 科综合随机组建标准 55 题考卷（40 单选 + 5 多选 + 10 判断），自动批阅并归档至本地试卷库。
- **全场景数据同步**：支持 GitHub Gist 免服务器跨网双向云同步、局域网直连合并、离线数据口令快照互传以及本地数据一键清空重置。

### 二、邀请码访问控制管理

系统内置纯前端 `SHA-256` 邀请码门禁（明文不入库，公开仓库仅保存哈希值，设备首次验证通过后永久记忆）。项目根目录提供管理工具 `invite_tool.py`：

```powershell
# 添加自定义简单邀请码（例如 2026、888888）
python invite_tool.py add 2026 站长邀请码

# 随机生成 6 位简短邀请码
python invite_tool.py new 5 学员批次

# 查看本地所有邀请码及有效状态
python invite_tool.py list

# 吊销指定邀请码（推送到 GitHub 后已激活该码的设备将自动重锁）
python invite_tool.py revoke 2026
```

### 三、视频构建与部署说明

若需从本地原始课程视频重新构建压缩版视频并生成目录索引，可在安装 `uv` 后执行：

```powershell
uv run --with imageio-ffmpeg python build_course_videos.py --source "本地视频目录" --output web/videos --base-url ./videos
```

---

<h2 id="english-documentation">English Documentation</h2>

**jsgsMock** is a flat, distraction-free, offline-capableProgressive Web App (PWA) and Android client designed for the **Jiangsu Higher Education Teacher Pre-service Training Examination**. It integrates dual question banks (**2026 Official Latest Questions** and **Historical Question Bank**), **123 lecture videos** across 5 core subjects, Ebbinghaus spaced-repetition review, and a multi-provider AI teaching assistant.

- **GitHub Repository**: [https://github.com/Simple53/jsgsMock](https://github.com/Simple53/jsgsMock) (If you find this project helpful, please give it a **Star**!)
- **Live Web App**: [https://simple53.github.io/jsgsMock/](https://simple53.github.io/jsgsMock/)
- **Android APK**: Download the latest `jsgsMock.apk` from [GitHub Releases](https://github.com/Simple53/jsgsMock/releases) with built-in one-click OTA update support.

### Key Features

1. **Dual Question Banks & Daily Key Points**
   - Instant switching between the *2026 Official Question Bank* and *Historical Question Bank* covering Higher Education Pedagogy, Psychology, Teacher Ethics, and Education Law.
   - Daily curated knowledge points extracted from official explanations with one-click refresh and full-screen immersive reading mode.
   - Top header quick actions: three-mode theme switcher (Light / Eye-Care / Dark), GitHub repository link, Favorites quiz entry, daily check-in calendar, and inline instant search.

2. **Lecture Video Player with Touch Gestures**
   - Streams 123 course videos organized by subject with automatic breakpoint resume.
   - Built-in **Fullscreen button** and **Portrait/Landscape orientation toggle** strictly inside the player control overlay.
   - Full mobile touch gestures: vertical swipe on the left half for brightness, vertical swipe on the right half for volume, and horizontal swipe for smooth seeking.
   - Two-step CDN source selector menu (*Official CDN* vs. *Domestic Mirror*) and multi-speed playback control.

3. **Smart Quiz Workspace & AI Teaching Assistant**
   - Supports both *Study Mode* (instant explanation) and *Exam Mode*, equipped with an undoable scratchpad canvas, touch swipe navigation, and PC keyboard/wheel shortcuts.
   - Multi-provider AI integration (DeepSeek, Kimi, Qwen, Zhipu, OpenAI, SiliconFlow, OpenRouter, and custom endpoints).
   - Clean borderless list view for AI model management with multi-select batch deletion.
   - Draggable floating AI assistant drawer for multi-turn contextual Q&A.

4. **Spaced Repetition, Mock Exams & Cross-Device Sync**
   - **Ebbinghaus Review**: Tracks wrong questions and favorites with three-level memory feedback (*Remember*, *Vague*, *Forget*).
   - **55-Question Standard Mock Exams**: Generates subject-specific or comprehensive 55-question mock papers (40 single-choice + 5 multiple-choice + 10 true/false).
   - **Serverless Cloud Sync**: Bidirectional merge across mobile and desktop via GitHub Gist API, LAN server, or offline snapshot tokens.

5. **Lightweight Invite Code Gate**
   - Protects access on static hosting using salted `SHA-256` hashes stored in `web/invite.json` and persistent `localStorage` activation.
   - Manage simple invite codes locally via `python invite_tool.py add <code>`, `new`, `list`, and `revoke`.
