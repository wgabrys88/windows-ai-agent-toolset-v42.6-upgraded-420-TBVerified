Summary of all changes made

config.json — max_agent_vlm_concurrent raised to 5, vlm_request_delay_seconds set to 0, brain_file updated to brain_agentic.py.

brain_agentic.py — complete rewrite then patched: async def main(hub) entry point, all actions via hub.actions(hub.click(...)), parallel debate via asyncio.gather, drag takes (x1,y1,x2,y2), hotkey as single joined string, scroll with 2 args only, VLM via hub channels using config endpoint, all system prompts as triple-quoted strings, no globals except constants, no threads. Patched: Grok JSON now includes "phase" field written verbatim by Python (Python no longer infers phase from action list length). Missing coordinate fields (x/y/x1/y1/x2/y2) raise ValueError instead of silently defaulting. Missing "key" on press_key raises ValueError. Non-string "keys" on hotkey raises ValueError. frame_b64 passed to all 5 debate agents as image_url content so agents see the actual screen. history updated every cycle with phase, progress, actions taken, and dispatch errors (capped at 800 chars). Empty or unparseable Grok response surfaces as error to swarm and skips the cycle. max_tokens raised to 1024 for agents and 1200 for captain.

panel.html — complete rewrite then patched: three-quadrant layout with v-gutter (full height, col resize) and h-gutter (right pane only, row resize), both draggable with localStorage persistence. CSS grid stack for canvas (grid-area:1/1) replacing absolute positioning. fitCanvas called on both gutter drags. One row per agent updated in place. Collapsed state uses -webkit-line-clamp on body directly (agent-row-preview div removed). Expanded state uses max-height:60vh + overflow-y:auto. Auto-scroll to updated agent row when near bottom. Event log appends to bottom and auto-scrolls (consistent direction with swarm panel). badge-img replaced with ann-dot (pulsing colored dot). cycle counter removed from status bar. fallbackTimer not started on load, only inside es.onerror. SSE reconnect attempted after 5s on connection loss. lastPendingSeq renamed to lastAttemptedSeq. cycleCount removed. --radius and --split-x dead CSS variables removed. Save handler calls exportAnnotated() instead of duplicating OffscreenCanvas block. sbSeq, canvasStatus, annDot cached at module init.


Franz Project — Coding Rules


Architecture
All Python decisions live in the brain; franz_hub.py is pure plumbing that routes strings and executes actions, never making intelligence decisions itself.
The brain entry point must be async def main(hub: ModuleType) receiving the hub module as its only argument; all hub calls use the hub. prefix from that argument.
Every action must be enqueued via hub.actions(hub.click(...)) — helper functions return dicts and have no side effects on their own.
VLM calls must go through hub.call_vlm_agent() or hub.call_vlm_orchestrator() to respect semaphores and use the configured endpoint; never call the VLM endpoint directly with urllib.
Concurrency is asyncio-first; use asyncio.gather() for parallel agent calls, never ThreadPoolExecutor inside an async brain.
State that is only touched by the single async brain loop lives as a local variable inside main(); no module-level mutable globals in the brain.

API Contracts
hotkey takes one joined string argument such as "ctrl+c", never a list or unpacked args. Non-string value raises ValueError.
scroll_up and scroll_down take exactly two arguments (x, y); there is no amount or clicks parameter at the brain level.
drag takes four arguments (x1, y1, x2, y2); there are no drag_start or drag_end functions. All four fields are required; missing fields raise ValueError.
click, double_click, right_click, scroll_up, scroll_down all require x and y; missing fields raise ValueError. Python never invents fallback coordinates.
press_key requires the key field; missing field raises ValueError. Python never invents a fallback key.
line() takes (points, label, color) only; stroke_width is not a supported parameter.
All overlay dicts must include closed, stroke, and fill keys or the panel will silently skip rendering the shape.
Coordinates are normalised integers in the range 0-1000 mapping to the visible capture region.
Grok JSON output must include a "phase" field set to one of INTERPRET, PLAN, EXECUTE, EVALUATE. Python writes it verbatim and never infers phase from action list length or any other heuristic.

Config
All tuneable values live in config.json and are read at runtime via hub.cfg(key, default); no hardcoded endpoints, ports, or delays in the brain.
When raising agent concurrency, set max_agent_vlm_concurrent to match the number of parallel agents and set vlm_request_delay_seconds to 0 when the model server handles throttling itself.

Python Style
Target Python 3.13 exclusively; use match statements, type | None unions, slots=True dataclasses, and asyncio.TaskGroup or asyncio.gather where appropriate.
Adhere to Pylance strict rules; all variables and return types must be annotated.
All system prompts are triple-quoted docstring-style strings with no \n concatenation and no .format() embedded inside the literal.
No emojis, no non-ASCII characters anywhere in source code, strings, or log messages.
No comments, no dead code, no unused imports, no placeholder stubs left in delivered files.
Maximum deduplication: if the same logic appears twice, extract it into a helper.
No fluff: every line must earn its place; if removing a line changes nothing, remove it.
Silent failures are worse than loud ones; if a function receives wrong arguments, it must raise rather than silently return an empty result or invent a default.

HTML / CSS / JavaScript
Target only the latest Google Chrome; use HTML5, modern CSS, and ES modules — no legacy fallbacks, no polyfills, no var, no XMLHttpRequest.
Use OffscreenCanvas for all off-screen rendering; it is available in Chrome and avoids creating throwaway DOM elements.
SSE is the primary data channel; fallback polling only activates after an SSE error, never runs in parallel with a live SSE connection. SSE reconnect is attempted automatically after 5 seconds on connection loss.
One row per agent in the swarm panel, updated in place on each new message; never append a new card per message.
Rows are collapsed by default showing a two-line clamp applied directly to the body element; individual rows expand on click. Expanded state uses max-height:60vh and overflow-y:auto. There is no separate preview div.
Dead CSS classes and variables that have no corresponding HTML elements or usages must be removed.
Status dot animations use CSS @keyframes pulse only; no JavaScript-driven animation loops.
DOM elements queried repeatedly must be cached at module init; never call getElementById inside a hot path.
The panel layout is three-quadrant: canvas pane (left, full height), swarm wire (top-right), event log (bottom-right). Both gutters are draggable and persist position in localStorage. fitCanvas is called on both gutter drag events.
Event log appends to bottom and auto-scrolls; direction is consistent with swarm panel (newest at bottom).

Cross-file Consistency
Before writing any brain action call, verify the exact function signature in franz_hub.py.
Before writing any win32 subprocess interaction, verify the CLI argument name in win32.py's main() match block.
Before hardcoding any endpoint, port, or model name in the brain, check config.json for the canonical value and use hub.cfg() instead.
When adding a new overlay type in the brain, verify the panel's drawOverlay function handles all fields being added.

Review Process
Always cross-reference all files before flagging an issue; a concern in one file is only confirmed as a bug when proof exists in at least one other file.
Silent failures are worse than loud ones; if a function receives wrong arguments, it must raise rather than silently return an empty result.
When a global variable is set from one thread and read from another, it requires a lock or must be moved to a single-owner context.
