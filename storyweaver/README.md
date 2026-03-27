# StoryWeaver - AI-Powered Text Adventure Game

一个基于 DeepSeek API 的现代探案推理文字冒险游戏。玩家扮演私家侦探 **林深**，通过输入行动与推理推进剧情，逐步揭开失踪案真相。

## 1. 项目结构

```text
storyweaver/
├── app.py                # Gradio 主程序
├── story_generator.py    # DeepSeek 调用与剧情生成
├── config.py             # 配置文件
├── requirements.txt      # 依赖列表
└── README.md             # 使用说明
```

## 2. 环境准备

- Python 3.10+
- 可用网络环境
- DeepSeek API Key

## 3. 安装依赖

在 `storyweaver` 目录执行：

```bash
pip install -r requirements.txt
```

## 4. 配置 API Key

新建 `.env` 文件（与 `config.py` 同级），写入：

```env
DEEPSEEK_API_KEY=你的DeepSeek密钥
# 以下可选
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
MAX_HISTORY=5
MAX_TOKENS=500
TEMPERATURE=0.8
REQUEST_TIMEOUT=60
```

## 5. 启动项目

```bash
python app.py
```

启动后在浏览器访问 Gradio 地址（默认 http://127.0.0.1:7860 ）即可开始游戏。

## 6. 游戏玩法建议

- 输入“动作”与“推理”结合的指令，例如：
  - 检查案发现场门锁和猫眼痕迹。
  - 调取失踪者昨晚 20:00-23:00 的通话记录。
  - 我怀疑报案人隐瞒了时间线，继续追问不在场证明。
- 记录关键线索，注意前后证词是否矛盾。

## 7. 游戏模式说明

- 自由模式：无回合上限，适合自由探索剧情。
- 叙事模式：最多 20 回合。
- 叙事模式节奏：
  - 第 1-6 回合：铺垫阶段（建立关系与时间线）
  - 第 7-14 回合：调查阶段（扩展证据链与矛盾）
  - 第 15-19 回合：收束阶段（聚焦关键证词与物证）
  - 第 20 回合：真相揭示阶段（输出真相、证据链、结案结论）

超过 20 回合后，系统会提示案件已结案，请重新开始。

## 8. 常见问题

### Q1: 提示未检测到 API Key
- 检查 `.env` 是否与 `config.py` 同级。
- 检查变量名是否为 `DEEPSEEK_API_KEY`。

### Q2: 接口调用失败
- 检查网络连通性。
- 检查密钥配额是否充足。
- 检查 `DEEPSEEK_BASE_URL` 是否正确。

## 9. 课程项目可扩展方向

- 引入“案件状态机”（嫌疑人关系图、时间线、证据库）。
- 增加“多结局系统”（真相结局、误判结局、未破案结局）。
- 增加“难度模式”（提示强度、线索隐蔽度、时间限制）。
- 增加“存档/读档”与“案件报告自动总结”。
