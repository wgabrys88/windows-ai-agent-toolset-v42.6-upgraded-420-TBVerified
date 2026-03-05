import asyncio
import json
from types import ModuleType

CURRENT_TASK = "Draw a can"
# CURRENT_TASK = "Open Notepad and type hello world"
# CURRENT_TASK = "Search the web for latest AI news"
# CURRENT_TASK = "Take a screenshot and describe what you see"

_AGENTS: dict[str, str] = {
    "Harper": "research",
    "Benjamin": "logic",
    "Lucas": "creative",
    "Atlas": "gui",
    "Nova": "manager",
}

_AGENT_SYSTEM: dict[str, str] = {
    "Harper": """
You are Harper, Research and Facts specialist in a computer-use AI swarm.
Current goal: {goal}
Phase: {phase}
Your role: gather facts, recall relevant knowledge, identify what information is needed.
Observation of current screen: {observation}
History: {history}
Respond with your analysis and concrete suggestions for next actions.
""",
    "Benjamin": """
You are Benjamin, Logic and Planning specialist in a computer-use AI swarm.
Current goal: {goal}
Phase: {phase}
Your role: reason step by step, plan precise action sequences, detect errors in reasoning.
Observation of current screen: {observation}
History: {history}
Debate so far: {debate}
Respond with your logical analysis and proposed action plan.
""",
    "Lucas": """
You are Lucas, Creative and Balance specialist in a computer-use AI swarm.
Current goal: {goal}
Phase: {phase}
Your role: propose alternative approaches, balance speed vs accuracy, avoid getting stuck.
Observation of current screen: {observation}
History: {history}
Debate so far: {debate}
Respond with creative alternatives and your balanced recommendation.
""",
    "Atlas": """
You are Atlas, GUI Navigation specialist in a computer-use AI swarm.
Current goal: {goal}
Phase: {phase}
Your role: identify UI elements, determine exact coordinates for actions, navigate interfaces.
Coordinates are in range 0-1000 mapping to the visible screen region.
Observation of current screen: {observation}
History: {history}
Debate so far: {debate}
Respond with specific UI element locations and exact action sequences.
""",
    "Nova": """
You are Nova, Task Manager in a computer-use AI swarm.
Current goal: {goal}
Phase: {phase}
Progress: {progress}%
Your role: assess completion, manage phase transitions, propose next goal when done.
Observation of current screen: {observation}
History: {history}
Debate so far: {debate}
Respond with completion assessment and phase transition recommendation.
""",
}

_CAPTAIN_SYSTEM = """
You are Grok, Captain and final decision maker of a computer-use AI swarm.
Current goal: {goal}
Phase: {phase}
Progress: {progress}%

You receive a full debate from 5 specialist agents. Synthesize it into a decision.

Respond with ONLY valid JSON, no explanation, no markdown, no code block:
{{
  "actions": [
    {{"action": "click", "x": 500, "y": 300}},
    {{"action": "type_text", "text": "hello"}},
    {{"action": "press_key", "key": "enter"}},
    {{"action": "hotkey", "keys": "ctrl+s"}},
    {{"action": "scroll_up", "x": 500, "y": 500}},
    {{"action": "scroll_down", "x": 500, "y": 500}},
    {{"action": "double_click", "x": 400, "y": 200}},
    {{"action": "right_click", "x": 400, "y": 200}},
    {{"action": "drag", "x1": 100, "y1": 100, "x2": 600, "y2": 400}},
    {{"action": "wait"}}
  ],
  "phase": "EXECUTE",
  "is_complete": false,
  "next_goal": null,
  "progress": 0
}}

actions array may be empty if waiting is appropriate.
phase must be one of: INTERPRET, PLAN, EXECUTE, EVALUATE. Set it based on what the swarm is doing.
is_complete true only when goal is fully achieved.
next_goal string only when is_complete is true, otherwise null.
progress integer 0-100.
"""


def _make_progress_overlay(phase: str, progress: int, goal: str) -> list[dict]:
    bar = max(1, progress * 9)
    return [
        {
            "points": [[80, 80], [920, 80], [920, 920], [80, 920]],
            "closed": True,
            "stroke": "#00ff88",
            "fill": "",
            "label": f"PHASE:{phase}",
            "label_position": [85, 83],
            "label_style": {"font_size": 11, "bg": "#000000", "color": "#00ff88", "align": "left"},
        },
        {
            "points": [[50, 30]],
            "closed": False,
            "stroke": "#ffffff",
            "fill": "",
            "label": goal[:60],
            "label_position": [50, 30],
            "label_style": {"font_size": 14, "bg": "#000000", "color": "#ffffff", "align": "left"},
        },
        {
            "points": [[50, 55], [50 + bar, 55]],
            "closed": False,
            "stroke": "#00ffff",
            "fill": "",
            "label": f"{progress}%",
            "label_position": [50 + bar + 4, 50],
            "label_style": {"font_size": 10, "bg": "", "color": "#00ffff", "align": "left"},
        },
    ]


def _dispatch_action(hub: ModuleType, action: dict) -> None:
    act = str(action.get("action", "")).lower()
    match act:
        case "click" | "double_click" | "right_click" | "scroll_up" | "scroll_down":
            if "x" not in action or "y" not in action:
                raise ValueError(f"action {act} missing x/y: {action}")
            x = int(action["x"])
            y = int(action["y"])
            match act:
                case "click": hub.actions(hub.click(x, y))
                case "double_click": hub.actions(hub.double_click(x, y))
                case "right_click": hub.actions(hub.right_click(x, y))
                case "scroll_up": hub.actions(hub.scroll_up(x, y))
                case "scroll_down": hub.actions(hub.scroll_down(x, y))
        case "type_text":
            hub.actions(hub.type_text(str(action.get("text", ""))))
        case "press_key":
            if "key" not in action:
                raise ValueError(f"action press_key missing key: {action}")
            hub.actions(hub.press_key(str(action["key"])))
        case "hotkey":
            keys = action.get("keys", "")
            if not isinstance(keys, str):
                raise ValueError(f"action hotkey keys must be a string, got: {keys!r}")
            hub.actions(hub.hotkey(keys))
        case "drag":
            for field in ("x1", "y1", "x2", "y2"):
                if field not in action:
                    raise ValueError(f"action drag missing {field}: {action}")
            hub.actions(hub.drag(
                int(action["x1"]), int(action["y1"]),
                int(action["x2"]), int(action["y2"]),
            ))
        case "wait" | _:
            pass


async def _call_agent(
    hub: ModuleType,
    name: str,
    system: str,
    user: str,
    frame_b64: str = "",
) -> str:
    hub.set_agent_status(name, "awaiting_vlm")
    user_content: list[dict] | str
    if frame_b64:
        user_content = [
            {"type": "text", "text": user},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{frame_b64}"}},
        ]
    else:
        user_content = user
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]
    result = await hub.call_vlm_agent(
        messages,
        temperature=0.5,
        max_tokens=1024,
        agent_name=name,
    )
    hub.swarm_message(name, "output", result or "(no response)")
    hub.set_agent_status(name, "idle")
    return result or ""


async def _debate_round(
    hub: ModuleType,
    state: dict,
    observation: str,
    prior_debate: str,
    frame_b64: str = "",
) -> str:
    ctx = {
        "goal": state["goal"],
        "phase": state["phase"],
        "progress": state["progress"],
        "observation": observation,
        "history": state["history"],
        "debate": prior_debate,
    }
    tasks = [
        asyncio.create_task(
            _call_agent(
                hub,
                name,
                _AGENT_SYSTEM[name].format(**ctx),
                f"Goal: {state['goal']}\nScreen: {observation}",
                frame_b64=frame_b64,
            )
        )
        for name in _AGENTS
    ]
    results = await asyncio.gather(*tasks)
    return "\n".join(
        f"[{name}]: {text}"
        for name, text in zip(_AGENTS.keys(), results)
    )


async def main(hub: ModuleType) -> None:
    state: dict = {
        "goal": CURRENT_TASK,
        "phase": "INTERPRET",
        "progress": 0,
        "history": "Starting.",
    }

    for name in _AGENTS:
        hub.set_agent_status(name, "idle")
    hub.set_agent_status("Grok", "idle")

    while True:
        hub.log_event(f"Cycle start — phase={state['phase']} progress={state['progress']}%")

        frame_b64 = await hub.get_frame()
        hub.request_fresh_frame()

        for ov in _make_progress_overlay(state["phase"], state["progress"], state["goal"]):
            hub.overlays(ov)

        observation = f"Phase={state['phase']} Progress={state['progress']}% Goal={state['goal']}"

        debate = ""
        for round_num in range(3):
            hub.log_event(f"Debate round {round_num + 1}")
            debate = await _debate_round(hub, state, observation, debate, frame_b64=frame_b64)

        hub.set_agent_status("Grok", "thinking")
        captain_system = _CAPTAIN_SYSTEM.format(
            goal=state["goal"],
            phase=state["phase"],
            progress=state["progress"],
        )
        captain_messages = [
            {"role": "system", "content": captain_system},
            {
                "role": "user",
                "content": (
                    f"Screen observation: {observation}\n"
                    f"Full agent debate:\n{debate}\n"
                    "Output ONLY the JSON decision now."
                ),
            },
        ]
        hub.swarm_message(
            "Grok",
            "input",
            f"Synthesizing {len(debate)} chars of debate",
            image_b64=frame_b64,
            system=captain_system,
        )

        raw = await hub.call_vlm_orchestrator(
            captain_messages,
            temperature=0.2,
            max_tokens=1200,
            agent_name="Grok",
        )

        hub.swarm_message("Grok", "output", raw or "(no response)")
        hub.set_agent_status("Grok", "idle")

        if not raw:
            hub.log_event("Captain returned empty response -- VLM failure", "error")
            hub.swarm_message("Grok", "error", "VLM returned empty response")
            await asyncio.sleep(2.0)
            continue
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start < 0 or end <= start:
            hub.log_event(f"Captain JSON not found in response: {raw[:200]}", "error")
            hub.swarm_message("Grok", "error", f"No JSON in response: {raw[:200]}")
            state["history"] = f"{state['history']} | Cycle failed: Grok produced no JSON"
            await asyncio.sleep(1.0)
            continue
        try:
            decision = json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError) as exc:
            hub.log_event(f"Captain JSON parse failed: {exc}", "error")
            hub.swarm_message("Grok", "error", f"JSON parse error: {exc} | raw: {raw[:200]}")
            state["history"] = f"{state['history']} | Cycle failed: Grok JSON malformed"
            await asyncio.sleep(1.0)
            continue

        actions: list = decision.get("actions", [])
        is_complete: bool = bool(decision.get("is_complete", False))
        next_goal: str | None = decision.get("next_goal")
        new_progress: int = int(decision.get("progress", state["progress"]))
        new_phase: str = str(decision.get("phase", state["phase"]))

        hub.set_agent_status("Grok", "acting")
        dispatched: list[str] = []
        dispatch_error: str = ""
        for act in actions:
            try:
                _dispatch_action(hub, act)
                dispatched.append(str(act.get("action", "?")))
            except ValueError as exc:
                dispatch_error = str(exc)
                hub.log_event(f"Action dispatch error: {exc}", "error")
                hub.swarm_message("Grok", "error", f"Dispatch error: {exc}")
                break
            await asyncio.sleep(hub.cfg("action_delay_seconds", 0.15))
        hub.set_agent_status("Grok", "idle")

        if is_complete and next_goal:
            state["history"] = f"Completed: {state['goal']}. Now: {next_goal}"
            state["goal"] = next_goal
            state["phase"] = "INTERPRET"
            state["progress"] = 0
            hub.log_event(f"Goal complete, transitioning to: {next_goal}", "ok")
        else:
            state["progress"] = new_progress
            state["phase"] = new_phase
            action_summary = ", ".join(dispatched) if dispatched else "none"
            error_note = f" | dispatch error: {dispatch_error}" if dispatch_error else ""
            state["history"] = (
                f"{state['history']} | phase={new_phase} progress={new_progress}%"
                f" actions=[{action_summary}]{error_note}"
            )[-800:]

        await asyncio.sleep(0.5)
