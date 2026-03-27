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
    opening = _remove_blank_lines(generator.opening_scene())
    chat_display: List[ChatMessage] = [
        {"role": "assistant", "content": f"[系统开场]\n{opening}"}
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


def build_interface() -> gr.Blocks:
    """构建 Gradio UI。"""
    with gr.Blocks(
        title="StoryWeaver - AI 文字冒险",
        css="""
        #layout-root { height: calc(100vh - 240px); }
        #story-panel {
            height: calc(100vh - 240px) !important;
            min-height: calc(100vh - 240px) !important;
            max-height: calc(100vh - 240px) !important;
            overflow: hidden !important;
        }
        #story-panel .wrap {
            height: calc(100vh - 240px) !important;
            min-height: calc(100vh - 240px) !important;
            max-height: calc(100vh - 240px) !important;
            overflow: hidden !important;
        }
        #story-panel .overflow-y-auto {
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain;
        }
        #story-panel pre,
        #story-panel code,
        #story-panel .message {
            white-space: pre-wrap !important;
            word-break: break-word !important;
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
        gr.Markdown(
            """
            # StoryWeaver - AI 文字冒险
            你将扮演私家侦探 **林深**，调查一宗离奇失踪案。  
            输入你的行动、提问或推理，推动剧情发展。
            """
        )
        mode_selector = gr.Radio(
            choices=["自由模式", "叙事模式"],
            value="自由模式",
            label="游戏模式",
            info="自由模式：无回合上限；叙事模式：最多 20 回合并在结尾揭示真相。",
        )

        with gr.Row(equal_height=True, elem_id="layout-root"):
            with gr.Column(scale=7):
                chatbot = gr.Chatbot(
                    label="剧情内容",
                    elem_id="story-panel",
                    render_markdown=False,
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
            fn=start_new_game,
            inputs=[mode_selector],
            outputs=[chatbot, game_state, status, turn_state, game_over_state],
        ).then(
            fn=lambda x: x,
            inputs=[chatbot],
            outputs=[chat_state],
        )

        mode_selector.change(
            fn=start_new_game,
            inputs=[mode_selector],
            outputs=[chatbot, game_state, status, turn_state, game_over_state],
        ).then(
            fn=lambda x: x,
            inputs=[chatbot],
            outputs=[chat_state],
        )

        send_btn.click(
            fn=submit_action,
            inputs=[user_input, chat_state, game_state, mode_selector, turn_state, game_over_state],
            outputs=[chatbot, game_state, status, user_input, turn_state, game_over_state],
        ).then(
            fn=lambda x: x,
            inputs=[chatbot],
            outputs=[chat_state],
        )

        user_input.submit(
            fn=submit_action,
            inputs=[user_input, chat_state, game_state, mode_selector, turn_state, game_over_state],
            outputs=[chatbot, game_state, status, user_input, turn_state, game_over_state],
        ).then(
            fn=lambda x: x,
            inputs=[chatbot],
            outputs=[chat_state],
        )

        restart_btn.click(
            fn=start_new_game,
            inputs=[mode_selector],
            outputs=[chatbot, game_state, status, turn_state, game_over_state],
        ).then(
            fn=lambda x: x,
            inputs=[chatbot],
            outputs=[chat_state],
        )

    return demo


if __name__ == "__main__":
    app = build_interface()
    app.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
