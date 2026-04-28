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
- [x] 6.1 实现 StyleInput（文本输入 + 匹配结果显示/选择）
- [x] 6.2 实现 ChordCandidate（和弦卡片 + 钢琴卷帘缩略图）
- [x] 6.3 实现 ChordSelector（5候选行 + 加载/错误状态）
- [x] 6.4 实现 SequenceDisplay（已选序列 + 撤销/完成按钮）
- [x] 6.5 实现 BranchNav.tsx（分支标签切换 + 从N位置分叉 + 重命名/删除）
- [x] 6.6 组装 App.tsx（状态机编排 + 布局）

## Phase 7: 收尾打磨
- [ ] 7.1 添加加载态/空态/错误边界
- [ ] 7.2 端到端集成联调（前后端对接）
- [ ] 7.3 编写 README.md（搭建说明 + 使用指南）
- [ ] 7.4 (可选) Tone.js 集成 MIDI 试听
