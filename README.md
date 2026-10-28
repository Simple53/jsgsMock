<div align="center">
  <img src="web/icon.svg" width="96" height="96" alt="jsgsMock Icon" />
  <h1>jsgsMock</h1>
  <p><strong>江苏高校教师岗前培训全真题库与精讲学习系统</strong></p>
  <p><strong>Jiangsu Higher Education Teacher Pre-service Training Quiz & Video Learning System</strong></p>
  <p>
    <a href="#中文介绍">中文介绍</a> ·
    <a href="#客户端下载与安装指南-android--ios">Android / iOS 安装指南</a> ·
    <a href="#english-documentation">English Documentation</a> ·
    <a href="https://simple53.github.io/jsgsMock/">Online Demo</a> ·
    <a href="https://github.com/Simple53/jsgsMock/releases">Releases (APK & IPA)</a>
  </p>
</div>

---

<h2 id="中文介绍">中文介绍</h2>

**jsgsMock** 是一款专为江苏高校教师岗前培训考试打造的纯扁平化、零广告、支持全离线刷题与联网看课的学习系统。内置 **2026 官网最新真题** 与 **历年题库** 双题库引擎，涵盖《高等教育学》《高等教育心理学》《高校教师职业道德修养》《高等教育法规概论》《习近平总书记教育重要论述》全部统考科目，并集成核心考点精要 EPUB 阅读器、123 节官方名师视频课程与多服务商 AI 助教。

- **开源仓库**：[https://github.com/Simple53/jsgsMock](https://github.com/Simple53/jsgsMock)（欢迎点击右上角 **Star** 支持本项目）
- **在线体验**：[https://simple53.github.io/jsgsMock/](https://simple53.github.io/jsgsMock/)
- **客户端下载**：前往 [Releases 页面](https://github.com/Simple53/jsgsMock/releases) 下载安卓 `jsgsMock-vX.Y.Z.apk` 或苹果 iOS `jsgsMock-vX.Y.Z-ios.ipa`。

### 一、核心功能特色

#### 1. 首页、双题库与考点精要 EPUB 预览
- **双题库无缝切换**：支持在首页一键切换「2026官网最新真题」与「历年题库」，并提供新旧题库对照 Excel 总表下载。
- **核心考点精要 EPUB 阅读器**：首页内置「考点精要」入口，直接解析统编考点 Markdown 讲义并以电子书分章排版预览，支持章节内一键跳转对应真题训练，做题页面亦支持一键调阅当前题目的核心考点。
- **每日一句全屏精读**：每日从真题解析中甄选高频考点金句，支持一键刷新与点击全屏沉浸式阅读考点溯源。

#### 2. 视频课程与多线路流式播放器
- **5 大科目 123 节精讲**：按科目完整收录统编名师视频，支持「播放」与「简介」切换、整排课程导航切换、横向选集卡片与「展开菜单」（一行一集完整预览课程标题与播放进度）。
- **离线软件联网看课**：安卓 `.apk` 与苹果 `.ipa` 离线客户端内置三条云端视频加速线路（国内加速一、国内加速二、官方 CDN），联网状态下即可直接流式观看全部 123 节课程视频，断线或缓冲异常时自动切换备用加速源，并全程自动记忆与恢复上次播放进度。
- **纯净无圆环控制与全能手势**：
  - 播放器内部采用无背景圆环的纯图标按钮，集成**无线投屏 / AirPlay**、**全屏切换**、**画中画 (PiP) 小窗播放**与**垂直音量滑块**；
  - 同时支持**手指触摸与电脑鼠标拖拽**：左侧上下拖动调节画面亮度、右侧上下拖动（或在音量按钮/音量条上上下拖动）调节音量大小、水平左右拖动预览并调节播放进度；
  - 支持点击打开播放源菜单与多档倍速菜单（点击弹出菜单，二次点击确认切换）。

#### 3. 刷题工作台与 AI 名师助教
- **科学刷题体验**：支持背题模式与做题模式、手写草稿画板（带单步撤销）、左右滑屏切题与 PC 全键盘/滚轮翻题；多选题采用复选框勾选并确认提交机制，杜绝提前剧透答案。
- **多模型 AI 助教体系**：
  - 支持接入 DeepSeek、Kimi、通义千问、智谱清言、ChatGPT、硅基流动、OpenRouter 及自定义 OpenAI 兼容端点；
  - AI 模型设置采用无外框极简列表展示，支持点击设为默认模型及勾选批量删除；
  - 支持题目下方一键流式生成考点精解，以及可自由拖拽位置的悬浮 AI 助教多轮追问。

#### 4. 错题抗遗忘、全真模考与多格式数据备份
- **艾宾浩斯抗遗忘复习**：错题本与我的收藏均支持「记得 / 模糊 / 忘记」三维记忆反馈，动态计算复习临界期。
- **分科目与综合全真模考**：支持按单科目或 5 科综合随机组建标准 55 题考卷（40 单选 + 5 多选 + 10 判断），自动批阅并归档至本地试卷库。
- **多端同步与多格式备份**：支持 GitHub Gist 跨网双向云同步、局域网直连合并、离线口令快照互传；学习记录备份支持导出 **JSON / CSV / Markdown / TXT** 四种格式，本地数据清空采用红色高风险警示与**弹窗二次确认**机制防误删。

---

<h2 id="客户端下载与安装指南-android--ios">二、客户端下载与安装指南 (Android & iOS)</h2>

本项目的离线安装包已将 **2026 最新题库、历年真题库、核心考点精要讲义** 全部内置于应用包内，**无网络环境下即可直接刷题、背考点、模考**；当设备**连接 Wi-Fi 或移动网络时，应用内可直接在线流畅观看全部 123 节名师视频课程**。

### 1. Android 安卓设备安装 (.apk)
1. 前往本仓库 [Releases 页面](https://github.com/Simple53/jsgsMock/releases) 下载最新版本的 `jsgsMock-vX.Y.Z.apk`。
2. 在安卓手机或平板上直接点击安装即可使用，支持在「设置 -> 版本与客户端下载」中一键检查更新。

### 2. Apple iOS 苹果设备安装 (iPhone / iPad)

针对 iOS / iPadOS 系统机制，提供以下**两种安装方式**（任选其一即可）：

#### 方式一：安装原生离线客户端 `jsgsMock-vX.Y.Z-ios.ipa`（侧载安装，内置全量离线题库 + 联网看视频）
由于未上架 App Store 的 `.ipa` 安装包需要通过个人 Apple ID 免费签名后安装，步骤如下：

1. **下载安装包**：前往 [Releases 页面](https://github.com/Simple53/jsgsMock/releases) 下载最新的 **`jsgsMock-vX.Y.Z-ios.ipa`** 文件到电脑或手机。
2. **使用签名工具安装**（任选一种常用工具）：
   - **Sideloadly（推荐，支持 Windows / macOS）**：
     1. 在电脑端下载并打开 [Sideloadly](https://sideloadly.io/)，用数据线将 iPhone / iPad 连接电脑；
     2. 将 `jsgsMock-vX.Y.Z-ios.ipa` 拖入 Sideloadly 左侧的 IPA 图标框；
     3. 在 `Apple ID` 栏输入您的个人 Apple 账号，点击 `Start` 并输入账号密码（仅用于向苹果官方服务器申请免费个人开发证书），等待进度条走完即安装成功。
   - **AltStore / SideStore / 爱思助手**：在手机端通过 AltStore / SideStore 的 `+` 号直接选择 `.ipa` 安装，或在电脑端使用爱思助手「工具箱 -> IPA 签名」签名后安装。
   - **TrollStore（巨魔商店）**：已安装巨魔商店的设备直接分享 `.ipa` 至 TrollStore 即可永久免签安装。
3. **首次打开信任证书**：
   - 打开 iPhone / iPad **「设置」 -> 「通用」 -> 「VPN 与设备管理」**，在「开发者 App」下点击您的 Apple ID，选择 **「信任」**；
   - **iOS 16 及以上系统额外一步**：打开 **「设置」 -> 「隐私与安全性」**，滑到底部找到 **「开发者模式 (Developer Mode)」** 并开启，重启手机后点击「打开」即可正常进入 `jsgsMock`。

#### 方式二：Safari 免签一键安装桌面版（PWA 独立客户端，无需电脑、永不掉签）
如果您不想连接电脑签名，可以直接利用 iOS 原生 Web App 机制安装到桌面：

1. 使用 iPhone 或 iPad 自带的 **Safari 浏览器** 打开在线地址：[https://simple53.github.io/jsgsMock/](https://simple53.github.io/jsgsMock/)
2. 点击浏览器底部工具栏正中间的 **「分享」按钮**（方框带向上箭头图标）。
3. 在弹出菜单中向下滑动，点击 **「添加到主屏幕 (Add to Home Screen)」**，再点击右上角 **「添加」**。
4. 手机桌面即生成独立的 **`jsgsMock`** 应用图标。从主屏幕打开时将隐藏所有浏览器地址栏，以原生全屏独立窗口运行；首次打开后 Service Worker 会自动将题库与讲义缓存至本机供离线刷题，联网时直接在线播放全部名师视频课（支持画中画与 AirPlay 投屏）。

---

### 三、邀请码访问控制管理

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

### 四、视频与多端安装包构建说明

```powershell
# 1. 从本地原始课程视频构建压缩版视频并生成目录索引
uv run --with imageio-ffmpeg python build_course_videos.py --source "本地视频目录" --output web/videos --base-url ./videos

# 2. 本地生成并编译 iOS Xcode 工程（需 macOS 环境与 XcodeGen）
cp -r web ios/JsgsMock/web
cd ios && xcodegen generate && open JsgsMock.xcodeproj
```

---

<h2 id="english-documentation">English Documentation</h2>

**jsgsMock** is a flat, distraction-free, offline-capable learning system (Web PWA, Android `.apk`, and Apple iOS `.ipa`) designed for the **Jiangsu Higher Education Teacher Pre-service Training Examination**. It integrates dual question banks (**2026 Official Latest Questions** and **Historical Question Bank**), an **EPUB Knowledge Handbook Reader**, **123 lecture videos** across 5 core subjects, Ebbinghaus spaced-repetition review, and a multi-provider AI teaching assistant.

- **GitHub Repository**: [https://github.com/Simple53/jsgsMock](https://github.com/Simple53/jsgsMock) (If you find this project helpful, please give it a **Star**!)
- **Live Web App**: [https://simple53.github.io/jsgsMock/](https://simple53.github.io/jsgsMock/)
- **Mobile Releases (Android `.apk` & iOS `.ipa`)**: [GitHub Releases](https://github.com/Simple53/jsgsMock/releases)

### Key Features

1. **Dual Question Banks & EPUB Knowledge Reader**
   - Instant switching between the *2026 Official Question Bank* and *Historical Question Bank* covering all 5 examination subjects.
   - Built-in EPUB-style Markdown Knowledge Reader on the home page with one-click deep links to corresponding practice questions.
   - Daily curated knowledge points with one-click refresh and full-screen reading view.

2. **Lecture Video Player (Online Streaming in Offline Apps)**
   - Streams 123 course videos organized by subject with automatic breakpoint resume and an expandable episode list (one full-title episode button per row).
   - **Multi-CDN Online Video Streaming**: Offline Android `.apk` and iOS `.ipa` packages include built-in multi-line CDN acceleration (*Domestic Mirror 1*, *Domestic Mirror 2*, and *Official GitHub CDN*) with automatic failover, allowing seamless online video playback whenever connected to the internet.
   - **Clean Borderless Controls & Gestures**:
     - Pure borderless icon buttons for **AirPlay / Wireless Cast**, **Fullscreen**, **Picture-in-Picture (PiP)**, and a **Vertical Volume Slider Popup**;
     - Supports both **touch and mouse drag gestures**: vertical drag on the left half for brightness, vertical drag on the right half (or on the volume icon/slider) for volume, and horizontal drag for seeking.

3. **Installation Guide for Apple iOS (iPhone / iPad) & Android**
   - **Android**: Download `jsgsMock-vX.Y.Z.apk` from [GitHub Releases](https://github.com/Simple53/jsgsMock/releases) and install directly.
   - **iOS Option 1 — Native Offline `.ipa` Sideloading**:
     1. Download `jsgsMock-vX.Y.Z-ios.ipa` from [GitHub Releases](https://github.com/Simple53/jsgsMock/releases).
     2. Sideload the `.ipa` onto your iPhone/iPad using **Sideloadly** (Windows/macOS), **AltStore / SideStore**, or **TrollStore**.
     3. On first launch, trust your developer certificate under *Settings -> General -> VPN & Device Management* (and enable *Developer Mode* under *Settings -> Privacy & Security* on iOS 16+).
     4. All question banks and study handbooks work 100% offline; connect to Wi-Fi or cellular data to stream all 123 lecture videos online.
   - **iOS Option 2 — Safari Home Screen Web App (No PC Required)**:
     1. Open `https://simple53.github.io/jsgsMock/` in **Safari** on your iPhone or iPad.
     2. Tap the **Share** button -> **Add to Home Screen** -> **Add**.
     3. Launch `jsgsMock` from your Home Screen as a standalone full-screen app with offline cached question banks and online video streaming.
