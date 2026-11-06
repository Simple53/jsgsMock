# jsgsMock (Dev_file2quiz) 项目深度复盘与工程实践指南

---

## 一、目标一句话
构建一个零后端依赖、纯前端离线优先的高校教资真题模拟刷题与考点研学系统，集成结构化权威 AI 助教、HLS 微切片极速流媒体、艾宾浩斯抗遗忘记忆曲线与多端自适应交付能力。

---

## 二、关键坑点：现象、根因、解法

### 1. 视频播放跳尾（直接跳至视频末尾 0 秒结束）
- **现象**：重新压制的 MP4 文件部署至网页后，点击播放进度条瞬跳至终点或直接黑屏报错中断。
- **根因**：编码时包含乱序 B 帧且未重置 DTS，存在负时间戳（Negative DTS / PTS 乱序）及 Open-GOP，移动端及现代浏览器原生解码器无法单调向前索引引发致命 Seek 异常。
- **解法**：采用严格的 Web 封闭式 GOP 转码规范：
  ```bash
  ffmpeg -y -i input.mp4 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -c:v libx264 -profile:v high -level 4.0 -pix_fmt yuv420p -bf 0 -flags +cgop -movflags +faststart -c:a aac -b:a 128k output.mp4
  ```

### 2. 静态托管平台大文件视频加载迟缓、频发卡顿
- **现象**：几百 MB 的单体 MP4 挂载在 GitHub Pages 或静态 CDN 上，首次缓冲耗时长达数秒至数十秒，拖拽进度条极易阻塞。
- **根因**：单体 MP4 依赖 HTTP Range Request，网络波动时分段握手开销巨大，移动端浏览器预加载缓冲区过载。
- **解法**：改用 HLS（`.m3u8` + `.ts`）自适应微切片体系，切片颗粒度收缩至 3 秒（单切片仅约 60KB），前端引入 `hls.js` 并发加载，彻底平滑网络抖动。

### 3. 一键 AI 深度解析时“凭空猜测选项”产生幻觉
- **现象**：AI 助教解析题目时，分析的选项（A/B/C/D）与真题实际内容完全不匹配。
- **根因**：构造 Prompt 时仅提取了 `q.question` 与 `q.answer`，未提取 `q.options`（题库中选项存为键值对象）。大模型仅知正确答案是字母“A”，不知 A 代表什么，被迫臆造选项内容。
- **解法**：编写健壮的结构化格式化函数 `formatQuestionOptionsForAi(q)`，统一兼容 Object/Array 结构，将真实选项文本显式注入 Prompt 与 System Context。

### 4. AI 助教页面 Markdown 不适配、输出原始 Markdown 标记源码
- **现象**：助教输出的标题 `###`、粗体 `**`、代码块等以源码展示，段落黏连、排版混乱。
- **根因**：直接通过 `textContent` 写入或仅做 HTML 转义，未接入 Markdown AST/正则富文本渲染引擎；气泡容器设置了 `white-space: pre-wrap;` 阻碍了富文本流式排版。
- **解法**：内置轻量防 XSS 的 `renderMarkdown()` 引擎（保护代码块占位 -> 普通文本转义 -> 语义化标签替换），流式打字与历史回顾统一输出安全富文本。

### 5. 跨端更新版本号误递增引发误更新
- **现象**：明确要求功能修复时“版本号不变”，但若改动分散在 `version.json` 或源码常量中，容易误触发客户端更新提示弹窗。
- **根因**：配置项分散且未设置版本号变更守门检查。
- **解法**：严守“外科手术式修改”纪律，提交前严格审查 `git diff`，确保版本字段只读封锁。

---

## 三、下次规避清单（Checklist）

### 1. 【禁止项】（Forbidden）
- [x] **严禁向大模型传递残缺题目信息**：严禁“有答案无选项”或“有题干无解析”地调用大模型。
- [x] **严禁原始录屏文件直传 Web 端**：严禁未经 `-movflags +faststart` 和 Closed-GOP 转码的 MP4 交付生产。
- [x] **严禁 AI 文本直接 `textContent` 输出**：涉及大模型 Markdown 内容必须经过格式转换。
- [x] **严禁随意变动发布版本号**：未获明确发版指令前，绝对禁止改动 `web/version.json` 及代码内 `CURRENT_APP_VERSION`。

### 2. 【必检项】（Must Check）
- [x] **模型请求 Payload 审查**：确认发送至大模型的 Prompt 中包含题型、科目、题干、全部选项、官方答案与官方解析。
- [x] **流媒体头信息校验**：使用 `ffprobe` 确认视频时间戳从 0 开始、无负 DTS、moov atom 位于文件头部。
- [x] **Git 变更范围精细审查**：`git status` 和 `git diff` 确认变更严格落在目标范围内。
- [x] **离线存储与缓存边界测试**：确认无网络或 API 异常时，题目解析与历史会话能安全降级展示。

### 3. 【关键配置】（Gold Standard Config）
```javascript
// 1. 标准 AI 考题上下文提取
function formatQuestionOptionsForAi(q) {
  if (!q || !q.options) return "（无单独选项）";
  const letters = ['A', 'B', 'C', 'D', 'E', 'F'];
  const lines = letters.filter(k => q.options[k]).map(k => `${k}. ${String(q.options[k]).trim()}`);
  return lines.length > 0 ? lines.join('\n') : "（判断题或无选项）";
}

// 2. 视频切片规范
// 目标：3秒一切片，微切片秒开，零卡顿
// ffmpeg -i master.mp4 -c copy -hls_time 3 -hls_list_size 0 -hls_segment_filename "chunk_%03d.ts" playlist.m3u8
```

---

## 四、可复用提示词（Prompts For Reuse）

### 1. 考题一键深度剖析 Prompt 模板
```text
你是一位高校教师资格证与教育学权威名师。输出直击考点核心，权威严谨，排版清晰美观，杜绝任何 Emoji。

【当前题目背景】
【科目】：{{subject}}
【题型】：{{typeName}}
【题干】：{{question}}
【题目选项】：
{{formattedOptions}}
【官方答案】：{{answer}}
【官方解析】：{{analysis}}

请按以下三部分精炼输出：
1. 【考点本质】：一句话点破核心考点或法理/教育学依据。
2. 【正解与混淆拆解】：讲透为什么选 {{answer}}，逐一拆解干扰选项的误导陷阱与辨析技巧。
3. 【秒记口诀】：给出一句好记的背诵口诀或记忆联想法。
```

### 2. 助教多轮追问上下文注入 System 设定
```text
你是一位高校教师资格证与教育学权威名师。输出直击考点核心，拒绝废话，排版层次清晰，杜绝任何 Emoji。
当前考生正在针对该题追问：
【题目】：[{{subject}}] {{typeName}} - {{question}}
【选项】：{{formattedOptions}}
【正确答案】：{{answer}}
请针对考生的具体困惑针对性答疑，结合相关考纲、教材原文及常见设错套路展开，语气专业严谨。
```
