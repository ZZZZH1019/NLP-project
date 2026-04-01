"""
StoryWeaver 主程序（Gradio 前端）

运行方式：
python app.py

功能：
1. 提供聊天式文字冒险交互界面。
2. 管理游戏对话历史与重开逻辑。
3. 调用 story_generator 生成剧情推进。
"""

from __future__ import annotations

import re
import html
from typing import Dict, List, Tuple
import gradio as gr

from story_generator import StoryGenerator


generator = StoryGenerator()
ChatMessage = Dict[str, str]
MAX_NARRATIVE_TURNS = 20


def _remove_blank_lines(text: str) -> str:
    """移除文本中的空白行，避免聊天区出现多余空行。"""
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


SECTION_ORDER = ["场景", "可疑线索", "可执行行动"]
SECTION_ALIASES: Dict[str, List[str]] = {
    "场景": ["场景", "当前场景", "现场", "情景", "行动结果", "结果反馈"],
    "可疑线索": ["可疑线索", "线索", "关键线索", "证据", "新线索", "技术鉴定失败"],
    "可执行行动": ["可执行行动", "可执行运动", "行动建议", "行动选项", "建议行动", "下一步行动"],
}


def _strip_prefix_index(line: str) -> str:
    """移除模型可能输出的前缀编号，避免重复编号。"""
    return re.sub(r"^[a-zA-Z0-9①-⑩\-\.\)\））、:：\s]+", "", line).strip()


def _detect_section(line: str) -> Tuple[str | None, str]:
    """识别当前行是否为小节标题，并返回规范小节名与同行尾部内容。"""
    stripped = line.strip()
    for canonical, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            matched = re.match(
                rf"^([>#\-\s]*)\*{{0,2}}[\[【(（]?\s*{re.escape(alias)}\s*[\]】)）]?\*{{0,2}}([：:]?)(.*)$",
                stripped,
            )
            if matched:
                tail = (matched.group(3) or "").strip()
                return canonical, tail
    return None, stripped


def _normalize_message_blocks(text: str) -> str:
    """将回复归一为三段结构：【场景】【可疑线索】【可执行行动】并统一大写编号。"""
    buckets: Dict[str, List[str]] = {section: [] for section in SECTION_ORDER}
    current_section = "场景"

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue

        section, tail = _detect_section(raw_line)
        if section:
            current_section = section
            if tail:
                buckets[current_section].append(tail)
            continue

        buckets[current_section].append(raw_line.strip())

    if not buckets["场景"]:
        buckets["场景"] = ["现场暂无新增描述。"]
    if not buckets["可疑线索"]:
        buckets["可疑线索"] = ["暂未发现新增可疑线索。"]
    if not buckets["可执行行动"]:
        buckets["可执行行动"] = ["继续调查现场细节", "追问关键相关人", "核验已得线索"]

    clues = [_strip_prefix_index(item) for item in buckets["可疑线索"] if _strip_prefix_index(item)]
    if len(clues) > 1:
        buckets["可疑线索"] = [f"{chr(ord('A') + i)}. {item}" for i, item in enumerate(clues)]
    elif len(clues) == 1:
        buckets["可疑线索"] = clues
    else:
        buckets["可疑线索"] = ["暂未发现新增可疑线索。"]

    actions = [_strip_prefix_index(item) for item in buckets["可执行行动"] if _strip_prefix_index(item)]
    if actions:
        buckets["可执行行动"] = [f"{chr(ord('A') + i)}. {item}" for i, item in enumerate(actions)]
    else:
        buckets["可执行行动"] = ["A. 继续调查现场细节", "B. 追问关键相关人", "C. 核验已得线索"]

    output_lines: List[str] = []
    for section in SECTION_ORDER:
        output_lines.append(f"**[ {section} ]**")
        output_lines.append("")
        output_lines.extend(buckets[section])
        output_lines.append("")

    return "\n".join(output_lines).strip()


def render_chat_html(messages: List[ChatMessage]) -> str:
    """将消息状态渲染为纯 HTML，避免 Chatbot 默认样式导致的额外空白。"""
    shell_style = (
        "min-height:320px;max-height:calc(100vh - 320px);border:1px solid #e5e7eb;border-top:none;"
        "border-radius:0 0 10px 10px;background:#fcfdff;overflow:hidden;"
    )
    scroll_style = (
        "min-height:320px;max-height:calc(100vh - 320px);overflow-y:auto;overflow-x:hidden;padding:10px 12px;"
        "box-sizing:border-box;"
    )
    list_style = "margin:0;padding:0;display:flex;flex-direction:column;gap:8px;"

    if not messages:
        return (
            f'<div id="story-shell" style="{shell_style}"><div id="story-scroll" style="{scroll_style}"><div id="story-list" style="{list_style}">'
            '<div class="story-empty" style="color:#6b7280;font-size:14px;line-height:1.5;padding:8px 10px;">剧情已加载，等待案件开场...</div>'
            '</div></div></div>'
        )

    parts: List[str] = []
    for msg in messages:
        role = msg.get("role", "assistant")
        row_justify = "flex-end" if role == "user" else "flex-start"
        bubble_bg = "#ecfeff" if role == "user" else "#ffffff"
        bubble_border = "#a5f3fc" if role == "user" else "#dbeafe"
        content = msg.get("content", "") or ""
        safe = html.escape(content)
        # 仅启用最小 Markdown：**加粗**，其余仍按纯文本处理。
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
        safe = safe.replace("\n", "<br>")
        parts.append(
            f'<div class="story-row" style="display:flex;justify-content:{row_justify};margin:0;">'
            f'<div class="story-bubble" style="max-width:90%;margin:0;padding:10px 12px;border-radius:12px;border:1px solid {bubble_border};background:{bubble_bg};box-sizing:border-box;">'
            f'<div class="story-content" style="margin:0;padding:0;word-break:break-word;line-height:1.5;font-size:14px;color:#0f172a;">{safe}</div>'
            "</div>"
            "</div>"
        )

    return (
        f'<div id="story-shell" style="{shell_style}"><div id="story-scroll" style="{scroll_style}"><div id="story-list" style="{list_style}">'
        + "".join(parts)
        + "</div></div></div>"
    )


def start_new_game(mode: str) -> Tuple[List[ChatMessage], List[Tuple[str, str]], str, int, bool]:
    """
    初始化新游戏。

    返回:
    - chat_display: Gradio Chatbot 显示内容
    - game_history: 供模型调用的历史轮次
    - status_text: 状态提示
    - turn_count: 当前回合数
    - is_game_over: 是否已结案
    """
    opening = generator.opening_scene().strip()
    chat_display: List[ChatMessage] = [
        {"role": "assistant", "content": opening}
    ]
    game_history: List[Tuple[str, str]] = []
    if mode == "叙事模式":
        status = f"叙事模式已开始：0/{MAX_NARRATIVE_TURNS} 回合。"
    else:
        status = "自由模式已开始：回合不设上限。"
    return chat_display, game_history, status, 0, False


def submit_action(
    user_input: str,
    chat_display: List[ChatMessage],
    game_history: List[Tuple[str, str]],
    mode: str,
    turn_count: int,
    is_game_over: bool,
) -> Tuple[List[ChatMessage], List[Tuple[str, str]], str, str, int, bool]:
    """
    处理玩家输入并返回 UI 所需更新。

    返回:
    - 更新后的 chat_display
    - 更新后的 game_history
    - 状态文本
    - 清空后的输入框内容
    - 更新后的 turn_count
    - 更新后的 is_game_over
    """
    user_text = (user_input or "").strip()
    if not user_text:
        return chat_display, game_history, "请输入你的行动或推理。", "", turn_count, is_game_over
    if len(user_text) > 100:
        return (
            chat_display,
            game_history,
            "输入超出 100 字，请精简后再提交。",
            user_text[:100],
            turn_count,
            is_game_over,
        )

    if mode == "叙事模式" and is_game_over:
        return (
            chat_display,
            game_history,
            "本案已结案，请点击“重新开始”开启新案件。",
            "",
            turn_count,
            is_game_over,
        )

    next_turn = turn_count + 1

    try:
        ai_reply = generator.generate_next_with_control(
            player_input=user_text,
            history=game_history,
            mode=mode,
            turn=next_turn,
            max_turns=MAX_NARRATIVE_TURNS,
        )
        ai_reply = _remove_blank_lines(ai_reply)
        ai_reply = _normalize_message_blocks(ai_reply)
    except Exception as exc:  # noqa: BLE001
        ai_reply = (
            "系统提示：当前无法连接剧情引擎，请检查 API Key、网络或配额后重试。\n"
            f"错误信息：{exc}"
        )

    # 展示层历史：Gradio 6 推荐使用 messages 格式。
    chat_display = chat_display + [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": ai_reply},
    ]

    # 模型层历史：只记录用户与助手文本对，供后续上下文续写。
    game_history = game_history + [(user_text, ai_reply)]

    if mode == "叙事模式":
        finished = next_turn >= MAX_NARRATIVE_TURNS
        if finished:
            status = f"叙事模式：{next_turn}/{MAX_NARRATIVE_TURNS} 回合，真相已揭示，案件已结案。"
        else:
            status = f"叙事模式：{next_turn}/{MAX_NARRATIVE_TURNS} 回合，剧情推进中。"
    else:
        finished = False
        status = f"自由模式：第 {next_turn} 回合，剧情已更新。"

    return chat_display, game_history, status, "", next_turn, finished


def start_new_game_ui(mode: str) -> Tuple[str, List[ChatMessage], List[Tuple[str, str]], str, int, bool]:
    """开局并同步返回剧情区 HTML。"""
    chat_display, game_history, status, turn_count, is_game_over = start_new_game(mode)
    story_html = render_chat_html(chat_display)
    return story_html, chat_display, game_history, status, turn_count, is_game_over


def submit_action_ui(
    user_input: str,
    chat_display: List[ChatMessage],
    game_history: List[Tuple[str, str]],
    mode: str,
    turn_count: int,
    is_game_over: bool,
) -> Tuple[str, List[ChatMessage], List[Tuple[str, str]], str, str, int, bool]:
    """提交行动并同步返回剧情区 HTML。"""
    next_chat, next_history, status, cleared_input, next_turn, finished = submit_action(
        user_input=user_input,
        chat_display=chat_display,
        game_history=game_history,
        mode=mode,
        turn_count=turn_count,
        is_game_over=is_game_over,
    )
    story_html = render_chat_html(next_chat)
    return story_html, next_chat, next_history, status, cleared_input, next_turn, finished


def build_interface() -> gr.Blocks:
    """构建 Gradio UI。"""
    with gr.Blocks(
        title="StoryWeaver - AI 文字冒险",
        css="""
        #header-row { align-items: flex-start; }
        #mode-panel { padding-top: 6px; }
        #mode-panel .label-wrap,
        #status-box .label-wrap,
        #action-input .label-wrap {
            min-height: 28px;
        }
        #mode-panel .label-wrap .label-text,
        #status-box .label-wrap .label-text,
        #action-input .label-wrap .label-text {
            font-size: 14px;
            line-height: 1.4;
            font-weight: 600;
        }
        #layout-root {
            height: calc(100vh - 240px);
            min-height: 0;
        }
        #left-panel {
            height: calc(100vh - 240px);
            min-height: 0;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            gap: 0;
        }
        #story-label {
            height: 32px;
            line-height: 32px;
            font-size: 16px;
            font-weight: 700;
            margin: 0;
            padding: 0 8px;
            flex-shrink: 0;
            border-bottom: 1px solid #e5e5e5;
        }
        #story-panel {
            flex: 1 1 auto;
            min-height: 320px;
            display: block;
        }
        #story-panel .html-container {
            min-height: 320px;
            padding: 0;
            margin: 0;
        }
        #story-shell {
            height: 100%;
            min-height: 0;
            border: 1px solid #e5e7eb;
            border-top: none;
            border-radius: 0 0 10px 10px;
            background: #fcfdff;
            overflow: hidden;
        }
        #story-scroll {
            height: 100%;
            min-height: 0;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 10px 12px;
            box-sizing: border-box;
        }
        #story-list {
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .story-empty {
            color: #6b7280;
            font-size: 14px;
            line-height: 1.5;
            padding: 8px 10px;
        }
        .story-row {
            display: flex;
            margin: 0;
        }
        .story-assistant {
            justify-content: flex-start;
        }
        .story-user {
            justify-content: flex-end;
        }
        .story-bubble {
            max-width: 90%;
            margin: 0;
            padding: 10px 12px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            box-sizing: border-box;
        }
        .story-assistant .story-bubble {
            background: #ffffff;
            border-color: #dbeafe;
        }
        .story-user .story-bubble {
            background: #ecfeff;
            border-color: #a5f3fc;
        }
        .story-role {
            margin: 0 0 4px 0;
            font-size: 12px;
            color: #475569;
            font-weight: 700;
        }
        .story-content {
            margin: 0;
            padding: 0;
            white-space: normal;
            word-break: break-word;
            line-height: 1.5;
            font-size: 14px;
            color: #0f172a;
        }
        .story-content strong {
            font-weight: 700;
            color: #111827;
        }
        #right-panel {
            display: flex;
            flex-direction: column;
            height: calc(100vh - 240px);
            min-height: 0;
            gap: 12px;
        }
        #right-panel > * {
            width: 100%;
        }
        #status-box {
            flex: 0 0 120px;
            min-height: 120px !important;
        }
        #status-box .wrap,
        #status-box textarea {
            min-height: 76px !important;
            max-height: 76px !important;
            height: 76px !important;
            font-size: 14px;
            line-height: 1.4;
        }
        #action-input {
            flex: 1 1 auto;
            min-height: 180px !important;
        }
        #action-input .wrap,
        #action-input textarea {
            min-height: 150px !important;
            max-height: 320px !important;
            height: 100% !important;
        }
        #action-buttons {
            margin-top: 0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            flex: 0 0 56px;
            min-height: 56px !important;
            gap: 10px;
            align-items: stretch;
        }
        #send-btn button,
        #restart-btn button {
            min-height: 48px !important;
            max-height: 48px !important;
            height: 48px !important;
            font-size: 15px !important;
        }
        """,
    ) as demo:
        with gr.Row(elem_id="header-row"):
            with gr.Column(scale=7):
                gr.Markdown(
                    """
                    # StoryWeaver - AI 文字冒险
                    你将扮演私家侦探 **林深**，调查一宗离奇失踪案。  
                    输入你的行动、提问或推理，推动剧情发展。
                    """
                )
            with gr.Column(scale=5, elem_id="mode-panel"):
                mode_selector = gr.Radio(
                    choices=["自由模式", "叙事模式"],
                    value="自由模式",
                    label="游戏模式",
                    info="自由模式：无回合上限；叙事模式：最多 20 回合并在结尾揭示真相。",
                )

        with gr.Row(equal_height=True, elem_id="layout-root"):
            with gr.Column(scale=7, elem_id="left-panel"):
                gr.HTML('<div id="story-label">📖 剧情内容</div>')
                story_panel = gr.HTML(
                    value=render_chat_html([]),
                    elem_id="story-panel",
                    container=False,
                )

            with gr.Column(scale=5, elem_id="right-panel"):
                status = gr.Textbox(
                    label="系统状态",
                    interactive=False,
                    lines=4,
                    max_lines=4,
                    elem_id="status-box",
                )
                user_input = gr.Textbox(
                    label="你的行动",
                    placeholder="例如：我先检查摔裂手机的最近通话记录，并询问报案人昨晚时间线。",
                    lines=9,
                    max_lines=9,
                    max_length=100,
                    elem_id="action-input",
                )
                with gr.Row(elem_id="action-buttons"):
                    send_btn = gr.Button("提交行动", variant="primary", elem_id="send-btn")
                    restart_btn = gr.Button("重新开始", elem_id="restart-btn")

        # 两个状态变量：一个用于 UI 展示历史，一个用于模型上下文历史。
        chat_state = gr.State([])
        game_state = gr.State([])
        turn_state = gr.State(0)
        game_over_state = gr.State(False)

        # 页面加载时自动开局。
        demo.load(
            fn=start_new_game_ui,
            inputs=[mode_selector],
            outputs=[story_panel, chat_state, game_state, status, turn_state, game_over_state],
        )

        mode_selector.change(
            fn=start_new_game_ui,
            inputs=[mode_selector],
            outputs=[story_panel, chat_state, game_state, status, turn_state, game_over_state],
        )

        send_btn.click(
            fn=submit_action_ui,
            inputs=[user_input, chat_state, game_state, mode_selector, turn_state, game_over_state],
            outputs=[story_panel, chat_state, game_state, status, user_input, turn_state, game_over_state],
        )

        user_input.submit(
            fn=submit_action_ui,
            inputs=[user_input, chat_state, game_state, mode_selector, turn_state, game_over_state],
            outputs=[story_panel, chat_state, game_state, status, user_input, turn_state, game_over_state],
        )

        restart_btn.click(
            fn=start_new_game_ui,
            inputs=[mode_selector],
            outputs=[story_panel, chat_state, game_state, status, turn_state, game_over_state],
        )

    return demo


if __name__ == "__main__":
    app = build_interface()
    app.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
