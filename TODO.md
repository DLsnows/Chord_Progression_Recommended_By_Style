# Chord Progression Recommendation System — TODO

## Phase 1: 项目基础设施
- [x] 1.1 初始化 Python 后端项目（pyproject.toml, 依赖安装）
- [x] 1.2 创建 config.py 配置常量
- [x] 1.3 定义 ChordInfo 数据模型
- [x] 1.4 初始化 React+TypeScript+Vite 前端项目
- [x] 1.5 定义 TypeScript 类型接口

## Phase 2: 数据流水线
- [x] 2.1 编写数据下载脚本（chord_mapping.csv + HuggingFace）
- [x] 2.2 实现 loader.py（解析和弦映射表 + 加载数据集 + 基础三和弦补全）
- [x] 2.3 实现 parser.py（段落提取、和弦标准化、genres子标签拆分 + 多标签分组 + main_genre回退记录）
- [x] 2.4 实现 augment.py（移调函数 + 单峰高斯权重 σ=3.85, 范围1.0~0.30 + 增强流水线）
- [x] 2.5 实现 transitions.py（按细粒度标签分组构建转移矩阵 + 根音矩阵 + parquet 持久化 + style_index.json）
- [x] 2.6 运行一次性数据构建脚本，验证数据完整（5K子集测试通过：1860和弦, 64177条记录, 3303组, 608K bigrams）

## Phase 3: 推荐引擎
- [x] 3.1 实现 matcher.py（NL查询 → 分层加权：子标签0.60 + 年代0.20 + main_genre 0.20 + 退避逻辑）
- [x] 3.2 实现 recommender.py（加权n-gram + 双因子混合α=0.85 + 冷启动 + 重复排除）
- [x] 3.3 实现 session.py（SQLite 会话持久化 + 分支CRUD + 分支切换）
- [x] 3.4 初始化 SQLite schema（sessions/branches/chord_selections 表 + 迁移）

## Phase 4: API 服务层
- [x] 4.1 定义 Pydantic schemas（含分支相关模型）
- [x] 4.2 实现所有 REST 路由（含分支端点）
- [x] 4.3 创建 FastAPI 入口（CORS, lifespan, SQLite 初始化）

## Phase 5: 前端核心
- [x] 5.1 实现 pianoGeometry.ts（琴键SVG几何计算）
- [x] 5.2 实现 midi.ts（音名→MIDI转换、和弦→MIDI音集）
- [x] 5.3 实现 PianoRoll.tsx（SVG钢琴卷帘组件）
- [x] 5.4 实现 API client（带类型的fetch封装）
- [x] 5.5 实现 useRecommendation hook（状态机 + 会话管理）

## Phase 6: 前端UI
- [x] 6.1 实现 StyleInput（文本输入 + 匹配结果显示/选择 + CSS Module + hover状态）
- [x] 6.2 实现 ChordCandidate（和弦卡片 + 钢琴卷帘缩略图 + CSS Module + hover动画）
- [x] 6.3 实现 ChordSelector（5候选行 + 加载/错误/空态 + CSS Module）
- [x] 6.4 实现 SequenceDisplay（已选序列 + 撤销/完成按钮 + readonly模式 + CSS Module）
- [x] 6.5 实现 BranchNav.tsx（分支标签切换 + 从N位置分叉 + 重命名/删除 + CSS Module）
- [x] 6.6 组装 App.tsx（状态机编排 + 布局 + DONE阶段分支对比展示）

## Phase 6.5: Tone.js MIDI 试听

> **目标**: 使用 Tone.js 集成和弦 MIDI 实时试听，用户可点击试听推荐候选和弦、已选序列和弦、以及完整进行播放。

### 架构设计
- **AudioEngine 单例**: 封装 Tone.js PolySynth，提供 `playChord()` / `playProgression()` / `stop()` 方法
- **波形选择**: triangle（三角波）— 柔和音色适合和弦播放，attack=0.02s 避免咔哒声
- **初始化策略**: 懒初始化，首次用户点击时调用 `Tone.start()` 解决浏览器自动播放限制
- **进度播放**: 使用 `Tone.Transport` 序列化调度，每和弦持续 2 拍，tempo 默认 100 BPM
- **视觉反馈**: 当前播放/悬停中的和弦高亮（CSS transition + active 状态）
- **音量**: 默认 -10dB，可通过音量滑块调节

### 组件改造清单
- ChordCandidate: 添加小扬声器图标按钮（hover 时显示），点击试听单个和弦
- SequenceDisplay: 添加 "Play All" 按钮播放完整进行；每个和弦芯片添加播放按钮
- 所有播放按钮统一使用 Unicode 字符（♪ 播放, ■ 停止），无需额外图标库

### 文件变更
| 文件 | 操作 |
|------|------|
| `frontend/package.json` | `npm install tone` |
| `frontend/src/utils/audioEngine.ts` | **新建** — AudioEngine 单例 |
| `frontend/src/components/ChordCandidate.tsx` | 添加试听按钮 + 播放状态 |
| `frontend/src/components/ChordCandidate.module.css` | 试听按钮样式 |
| `frontend/src/components/SequenceDisplay.tsx` | Play All + 单和弦播放 |
| `frontend/src/components/SequenceDisplay.module.css` | 播放控制样式 |

- [x] 6.5.1 安装 Tone.js 依赖
- [x] 6.5.2 创建 audioEngine.ts（AudioEngine 单例 + PolySynth 封装）
- [x] 6.5.3 ChordCandidate 添加试听播放按钮
- [x] 6.5.4 SequenceDisplay 添加 "Play All" 完整进行播放
- [x] 6.5.5 SequenceDisplay 每个和弦芯片添加单和弦播放
- [x] 6.5.6 添加 CSS 播放按钮/播放中动画样式
- [x] 6.5.7 TypeScript 类型检查 + Vite 构建验证

## Phase 7: 收尾打磨
- [x] 7.1 添加加载态/空态/错误边界
- [x] 7.2 端到端集成联调（前后端对接）
- [x] 7.3 编写 README.md（搭建说明 + 使用指南）
- [x] 7.4 Tone.js 集成 MIDI 试听（已在 Phase 6.5 完成）
