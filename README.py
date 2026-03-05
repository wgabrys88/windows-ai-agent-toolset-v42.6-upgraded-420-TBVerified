# Franz

A Windows computer-use AI swarm. Captures the screen, runs a 5-agent debate, and executes input actions to complete arbitrary tasks.

---

## Architecture

<!--
SVG diagrams below use hardcoded colors (no CSS variables, no prefers-color-scheme).
They render identically regardless of browser theme or OS dark mode.
-->

<svg xmlns="http://www.w3.org/2000/svg" width="660" height="200" font-family="Consolas,monospace" font-size="12">
  <rect width="660" height="200" fill="#0a0a0c" rx="8"/>
  <!-- hub box -->
  <rect x="20" y="20" width="620" height="60" fill="#121218" stroke="#252530" stroke-width="1" rx="4"/>
  <text x="330" y="44" fill="#4a9eff" text-anchor="middle" font-weight="bold" font-size="13">franz_hub.py</text>
  <text x="330" y="64" fill="#55556a" text-anchor="middle">HTTP server  |  asyncio loop  |  SSE bus  |  action queue  |  VLM channels</text>
  <!-- arrows down -->
  <line x1="140" y1="80" x2="140" y2="120" stroke="#252530" stroke-width="1"/>
  <line x1="330" y1="80" x2="330" y2="120" stroke="#252530" stroke-width="1"/>
  <line x1="520" y1="80" x2="520" y2="120" stroke="#252530" stroke-width="1"/>
  <polygon points="140,120 136,112 144,112" fill="#252530"/>
  <polygon points="330,120 326,112 334,112" fill="#252530"/>
  <polygon points="520,120 516,112 524,112" fill="#252530"/>
  <!-- child boxes -->
  <rect x="60" y="120" width="160" height="44" fill="#121218" stroke="#1a2a40" stroke-width="1" rx="4"/>
  <text x="140" y="138" fill="#6ab0ff" text-anchor="middle" font-weight="bold">brain_agentic.py</text>
  <text x="140" y="154" fill="#55556a" text-anchor="middle">intelligence</text>
  <rect x="250" y="120" width="160" height="44" fill="#121218" stroke="#3a2a10" stroke-width="1" rx="4"/>
  <text x="330" y="138" fill="#ffaa44" text-anchor="middle" font-weight="bold">win32.py</text>
  <text x="330" y="154" fill="#55556a" text-anchor="middle">subprocess / Win32</text>
  <rect x="440" y="120" width="160" height="44" fill="#121218" stroke="#2a1a3a" stroke-width="1" rx="4"/>
  <text x="520" y="138" fill="#cc88ff" text-anchor="middle" font-weight="bold">panel.html</text>
  <text x="520" y="154" fill="#55556a" text-anchor="middle">Chrome UI</text>
</svg>

### Component roles

| File | Role |
|---|---|
| `franz_hub.py` | Motherboard. Pure plumbing. Routes strings, executes actions, owns all queues and the HTTP server. Makes zero decisions. |
| `brain_agentic.py` | Intelligence. 5-agent debate swarm + Grok captain. All VLM calls and action decisions live here. |
| `win32.py` | Standalone CLI subprocess. Screen capture via GDI, all mouse/keyboard input via Win32 API. |
| `panel.html` | Single-file Chrome UI. Three-quadrant layout. Annotates frames, streams swarm wire, renders overlays. |
| `config.json` | All tuneable values. Read at runtime via `hub.cfg()`. |

---

## Data flow

<svg xmlns="http://www.w3.org/2000/svg" width="660" height="420" font-family="Consolas,monospace" font-size="11">
  <rect width="660" height="420" fill="#0a0a0c" rx="8"/>
  <!-- lane headers -->
  <rect x="10" y="10" width="116" height="24" fill="#1a2a40" rx="3"/>
  <text x="68" y="26" fill="#6ab0ff" text-anchor="middle" font-weight="bold">brain</text>
  <rect x="136" y="10" width="116" height="24" fill="#1a3020" rx="3"/>
  <text x="194" y="26" fill="#5edf8e" text-anchor="middle" font-weight="bold">hub</text>
  <rect x="262" y="10" width="116" height="24" fill="#3a2a10" rx="3"/>
  <text x="320" y="26" fill="#ffaa44" text-anchor="middle" font-weight="bold">win32</text>
  <rect x="388" y="10" width="116" height="24" fill="#2a1a3a" rx="3"/>
  <text x="446" y="26" fill="#cc88ff" text-anchor="middle" font-weight="bold">panel</text>
  <rect x="514" y="10" width="116" height="24" fill="#2a2a30" rx="3"/>
  <text x="572" y="26" fill="#a0a0b8" text-anchor="middle" font-weight="bold">VLM server</text>
  <!-- lane dividers -->
  <line x1="126" y1="10" x2="126" y2="410" stroke="#1a1a22" stroke-width="1"/>
  <line x1="252" y1="10" x2="252" y2="410" stroke="#1a1a22" stroke-width="1"/>
  <line x1="378" y1="10" x2="378" y2="410" stroke="#1a1a22" stroke-width="1"/>
  <line x1="504" y1="10" x2="504" y2="410" stroke="#1a1a22" stroke-width="1"/>
  <!-- step 1: hub -> win32 capture -->
  <line x1="194" y1="54" x2="320" y2="54" stroke="#ffaa44" stroke-width="1" marker-end="url(#arr)"/>
  <text x="257" y="50" fill="#55556a" text-anchor="middle">subprocess capture</text>
  <!-- step 2: win32 -> hub raw PNG -->
  <line x1="320" y1="70" x2="194" y2="70" stroke="#ffaa44" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="257" y="66" fill="#55556a" text-anchor="middle">raw PNG bytes</text>
  <!-- step 3: hub -> panel SSE frame -->
  <line x1="194" y1="100" x2="446" y2="100" stroke="#cc88ff" stroke-width="1"/>
  <text x="320" y="96" fill="#55556a" text-anchor="middle">SSE: frame event</text>
  <!-- step 4: panel -> hub GET /frame -->
  <line x1="446" y1="116" x2="194" y2="116" stroke="#cc88ff" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="320" y="112" fill="#55556a" text-anchor="middle">GET /frame (raw_b64 + overlays)</text>
  <!-- step 5: panel annotates -->
  <line x1="446" y1="140" x2="446" y2="156" stroke="#cc88ff" stroke-width="1"/>
  <text x="446" y="152" fill="#55556a" text-anchor="middle">draw + OffscreenCanvas</text>
  <!-- step 6: panel -> hub POST /annotated -->
  <line x1="446" y1="170" x2="194" y2="170" stroke="#cc88ff" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="320" y="166" fill="#55556a" text-anchor="middle">POST /annotated</text>
  <!-- step 7: hub -> brain get_frame -->
  <line x1="194" y1="196" x2="68" y2="196" stroke="#6ab0ff" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="131" y="192" fill="#55556a" text-anchor="middle">get_frame() resolves</text>
  <!-- step 8: brain -> hub call_vlm_agent x5 -->
  <line x1="68" y1="220" x2="194" y2="220" stroke="#6ab0ff" stroke-width="1"/>
  <text x="131" y="216" fill="#55556a" text-anchor="middle">call_vlm_agent x5</text>
  <!-- step 9: hub -> VLM agent -->
  <line x1="194" y1="236" x2="572" y2="236" stroke="#a0a0b8" stroke-width="1"/>
  <text x="383" y="232" fill="#55556a" text-anchor="middle">HTTP POST (agent channel)</text>
  <!-- step 10: VLM -> hub -->
  <line x1="572" y1="252" x2="194" y2="252" stroke="#a0a0b8" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="383" y="248" fill="#55556a" text-anchor="middle">agent text response</text>
  <!-- step 11: brain -> hub orchestrator -->
  <line x1="68" y1="278" x2="194" y2="278" stroke="#6ab0ff" stroke-width="1"/>
  <text x="131" y="274" fill="#55556a" text-anchor="middle">call_vlm_orchestrator</text>
  <!-- step 12: hub -> VLM orchestrator -->
  <line x1="194" y1="294" x2="572" y2="294" stroke="#a0a0b8" stroke-width="1"/>
  <text x="383" y="290" fill="#55556a" text-anchor="middle">HTTP POST (orchestrator channel)</text>
  <!-- step 13: VLM -> hub JSON -->
  <line x1="572" y1="310" x2="194" y2="310" stroke="#a0a0b8" stroke-width="1" stroke-dasharray="4,2"/>
  <text x="383" y="306" fill="#55556a" text-anchor="middle">JSON decision</text>
  <!-- step 14: brain -> hub actions -->
  <line x1="68" y1="336" x2="194" y2="336" stroke="#6ab0ff" stroke-width="1"/>
  <text x="131" y="332" fill="#55556a" text-anchor="middle">hub.actions()</text>
  <!-- step 15: hub -> win32 action -->
  <line x1="194" y1="352" x2="320" y2="352" stroke="#ffaa44" stroke-width="1"/>
  <text x="257" y="348" fill="#55556a" text-anchor="middle">subprocess click/type/drag</text>
  <!-- arrowhead marker -->
  <defs>
    <marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#55556a"/>
    </marker>
  </defs>
</svg>

---
"""
"""
## Swarm loop

Each cycle: capture frame -> 3 debate rounds (5 agents in parallel, each receives the screen image) -> Grok synthesizes -> dispatch actions.

<svg xmlns="http://www.w3.org/2000/svg" width="560" height="500" font-family="Consolas,monospace" font-size="11">
  <rect width="560" height="500" fill="#0a0a0c" rx="8"/>
  <defs>
    <marker id="a" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#252530"/>
    </marker>
  </defs>
  <!-- boxes -->
  <rect x="200" y="16" width="160" height="30" fill="#121218" stroke="#252530" rx="3"/>
  <text x="280" y="35" fill="#e4e4ec" text-anchor="middle">Cycle start</text>

  <rect x="200" y="66" width="160" height="30" fill="#121218" stroke="#252530" rx="3"/>
  <text x="280" y="85" fill="#e4e4ec" text-anchor="middle">Capture frame</text>

  <rect x="200" y="116" width="160" height="30" fill="#121218" stroke="#252530" rx="3"/>
  <text x="280" y="135" fill="#e4e4ec" text-anchor="middle">Draw progress overlays</text>

  <rect x="200" y="166" width="160" height="30" fill="#1a2a40" stroke="#4a9eff" rx="3"/>
  <text x="280" y="185" fill="#4a9eff" text-anchor="middle">Debate rounds 1-3</text>

  <!-- 5 agents -->
  <rect x="20" y="220" width="100" height="26" fill="#1a2a40" stroke="#6ab0ff" rx="3"/>
  <text x="70" y="237" fill="#6ab0ff" text-anchor="middle">Harper</text>
  <rect x="130" y="220" width="100" height="26" fill="#1a2a3a" stroke="#88bbff" rx="3"/>
  <text x="180" y="237" fill="#88bbff" text-anchor="middle">Benjamin</text>
  <rect x="240" y="220" width="100" height="26" fill="#2a1a3a" stroke="#cc88ff" rx="3"/>
  <text x="290" y="237" fill="#cc88ff" text-anchor="middle">Lucas</text>
  <rect x="350" y="220" width="100" height="26" fill="#1a3020" stroke="#5edf8e" rx="3"/>
  <text x="400" y="237" fill="#5edf8e" text-anchor="middle">Atlas</text>
  <rect x="460" y="220" width="80" height="26" fill="#3a2a10" stroke="#ffaa44" rx="3"/>
  <text x="500" y="237" fill="#ffaa44" text-anchor="middle">Nova</text>

  <!-- agents -> grok -->
  <line x1="70" y1="246" x2="260" y2="290" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="180" y1="246" x2="268" y2="290" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="290" y1="246" x2="280" y2="290" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="400" y1="246" x2="292" y2="290" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="500" y1="246" x2="300" y2="290" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>

  <rect x="200" y="290" width="160" height="30" fill="#2a2a30" stroke="#a0a0b8" rx="3"/>
  <text x="280" y="309" fill="#a0a0b8" text-anchor="middle">Grok: synthesize</text>

  <rect x="200" y="340" width="160" height="30" fill="#121218" stroke="#252530" rx="3"/>
  <text x="280" y="359" fill="#e4e4ec" text-anchor="middle">Parse JSON decision</text>

  <!-- decision diamond -->
  <polygon points="280,390 340,410 280,430 220,410" fill="#121218" stroke="#252530"/>
  <text x="280" y="414" fill="#e4e4ec" text-anchor="middle">is_complete?</text>

  <rect x="380" y="396" width="140" height="30" fill="#1a3020" stroke="#3ecf8e" rx="3"/>
  <text x="450" y="415" fill="#3ecf8e" text-anchor="middle">next_goal transition</text>

  <rect x="60" y="396" width="140" height="30" fill="#121218" stroke="#252530" rx="3"/>
  <text x="130" y="415" fill="#e4e4ec" text-anchor="middle">update phase+progress</text>

  <!-- arrows -->
  <line x1="280" y1="46" x2="280" y2="66" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="280" y1="96" x2="280" y2="116" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="280" y1="146" x2="280" y2="166" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="280" y1="196" x2="280" y2="220" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="280" y1="320" x2="280" y2="340" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="280" y1="370" x2="280" y2="390" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="340" y1="410" x2="380" y2="410" stroke="#3ecf8e" stroke-width="1" marker-end="url(#a)"/>
  <text x="360" y="406" fill="#3ecf8e" text-anchor="middle" font-size="10">yes</text>
  <line x1="220" y1="410" x2="200" y2="410" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <text x="210" y="406" fill="#55556a" text-anchor="middle" font-size="10">no</text>
  <!-- loop back -->
  <line x1="130" y1="396" x2="130" y2="470" stroke="#252530" stroke-width="1"/>
  <line x1="450" y1="426" x2="450" y2="470" stroke="#3ecf8e" stroke-width="1"/>
  <line x1="130" y1="470" x2="450" y2="470" stroke="#252530" stroke-width="1"/>
  <line x1="280" y1="470" x2="280" y2="490" stroke="#252530" stroke-width="1"/>
  <line x1="240" y1="16" x2="240" y2="8" stroke="#252530" stroke-width="1"/>
  <line x1="240" y1="8" x2="280" y2="8" stroke="#252530" stroke-width="1"/>
  <line x1="280" y1="8" x2="280" y2="16" stroke="#252530" stroke-width="1" marker-end="url(#a)"/>
  <line x1="280" y1="490" x2="280" y2="470" stroke="#252530" stroke-width="1"/>
</svg>

**Key change from previous version:** Grok's JSON output now includes a `"phase"` field. Python writes it verbatim — it no longer infers phase from action list length. History is updated every cycle (not only on goal completion), recording phase, progress, actions taken, and any dispatch errors.

---

## Panel layout

Three-quadrant layout. Both gutters are draggable. Positions persist in `localStorage`.

<svg xmlns="http://www.w3.org/2000/svg" width="500" height="300" font-family="Consolas,monospace" font-size="11">
  <rect width="500" height="300" fill="#0a0a0c" rx="8"/>
  <!-- canvas pane -->
  <rect x="10" y="10" width="240" height="252" fill="#121218" stroke="#1a2a40" stroke-width="1" rx="3"/>
  <text x="130" y="30" fill="#6ab0ff" text-anchor="middle" font-weight="bold">Annotated View</text>
  <text x="130" y="50" fill="#55556a" text-anchor="middle">canvas (CSS grid stack)</text>
  <text x="130" y="66" fill="#55556a" text-anchor="middle">overlays rendered by panel</text>
  <text x="130" y="82" fill="#55556a" text-anchor="middle">exported via OffscreenCanvas</text>
  <text x="130" y="98" fill="#55556a" text-anchor="middle">POSTed to /annotated</text>
  <rect x="30" y="230" width="200" height="22" fill="#0a0a0c" stroke="#252530" rx="2"/>
  <text x="130" y="245" fill="#55556a" text-anchor="middle">ann-dot  |  seq: N  (status bar)</text>
  <!-- v-gutter -->
  <rect x="254" y="10" width="6" height="252" fill="#252530" rx="2"/>
  <text x="257" y="140" fill="#55556a" text-anchor="middle" font-size="9" writing-mode="tb">v-gutter</text>
  <!-- swarm pane -->
  <rect x="264" y="10" width="226" height="152" fill="#121218" stroke="#2a1a3a" stroke-width="1" rx="3"/>
  <text x="377" y="30" fill="#cc88ff" text-anchor="middle" font-weight="bold">Swarm Wire</text>
  <text x="377" y="48" fill="#55556a" text-anchor="middle">one row per agent, updated in place</text>
  <text x="377" y="64" fill="#55556a" text-anchor="middle">collapsed: 2-line clamp</text>
  <text x="377" y="80" fill="#55556a" text-anchor="middle">expanded: 60vh + scroll</text>
  <text x="377" y="96" fill="#55556a" text-anchor="middle">auto-scroll when near bottom</text>
  <!-- h-gutter -->
  <rect x="264" y="166" width="226" height="6" fill="#252530" rx="2"/>
  <text x="377" y="172" fill="#55556a" text-anchor="middle" font-size="9">h-gutter</text>
  <!-- log pane -->
  <rect x="264" y="176" width="226" height="86" fill="#121218" stroke="#1a3020" stroke-width="1" rx="3"/>
  <text x="377" y="196" fill="#5edf8e" text-anchor="middle" font-weight="bold">Event Log</text>
  <text x="377" y="214" fill="#55556a" text-anchor="middle">append + auto-scroll</text>
  <text x="377" y="230" fill="#55556a" text-anchor="middle">newest at bottom</text>
  <!-- status bar -->
  <rect x="10" y="266" width="480" height="24" fill="#121218" stroke="#252530" stroke-width="1" rx="3"/>
  <text x="250" y="282" fill="#55556a" text-anchor="middle">Franz  |  seq: N  |  (SSE dot)</text>
</svg>

---
"""
"""
## Annotation pipeline

<svg xmlns="http://www.w3.org/2000/svg" width="560" height="260" font-family="Consolas,monospace" font-size="11">
  <rect width="560" height="260" fill="#0a0a0c" rx="8"/>
  <defs>
    <marker id="b" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#252530"/>
    </marker>
  </defs>
  <!-- lane headers -->
  <rect x="10" y="10" width="156" height="22" fill="#1a3020" rx="3"/>
  <text x="88" y="25" fill="#5edf8e" text-anchor="middle" font-weight="bold">_capture_loop</text>
  <rect x="196" y="10" width="156" height="22" fill="#2a1a3a" rx="3"/>
  <text x="274" y="25" fill="#cc88ff" text-anchor="middle" font-weight="bold">panel.html</text>
  <rect x="382" y="10" width="156" height="22" fill="#1a2a40" rx="3"/>
  <text x="460" y="25" fill="#6ab0ff" text-anchor="middle" font-weight="bold">brain</text>
  <line x1="186" y1="10" x2="186" y2="250" stroke="#1a1a22" stroke-width="1"/>
  <line x1="372" y1="10" x2="372" y2="250" stroke="#1a1a22" stroke-width="1"/>
  <!-- steps -->
  <text x="88" y="58" fill="#e4e4ec" text-anchor="middle">screenshot via win32</text>
  <line x1="88" y1="62" x2="274" y2="80" stroke="#252530" stroke-width="1" marker-end="url(#b)"/>
  <text x="181" y="76" fill="#55556a" text-anchor="middle">SSE: frame {seq}</text>
  <line x1="274" y1="84" x2="88" y2="100" stroke="#252530" stroke-width="1" stroke-dasharray="4,2" marker-end="url(#b)"/>
  <text x="181" y="98" fill="#55556a" text-anchor="middle">GET /frame</text>
  <text x="274" y="120" fill="#e4e4ec" text-anchor="middle">loadBaseImage</text>
  <text x="274" y="136" fill="#e4e4ec" text-anchor="middle">renderOverlays</text>
  <text x="274" y="152" fill="#e4e4ec" text-anchor="middle">exportAnnotated</text>
  <line x1="274" y1="156" x2="88" y2="172" stroke="#252530" stroke-width="1" stroke-dasharray="4,2" marker-end="url(#b)"/>
  <text x="181" y="170" fill="#55556a" text-anchor="middle">POST /annotated</text>
  <text x="88" y="192" fill="#e4e4ec" text-anchor="middle">_ann_result_b64 set</text>
  <line x1="88" y1="196" x2="460" y2="212" stroke="#252530" stroke-width="1" stroke-dasharray="4,2" marker-end="url(#b)"/>
  <text x="274" y="210" fill="#55556a" text-anchor="middle">_frame_event.set()</text>
  <text x="460" y="232" fill="#e4e4ec" text-anchor="middle">get_frame() returns</text>
</svg>

---

## VLM channels

Two independent semaphores. Agent calls never block the captain.

| Channel | Semaphore key | Default |
|---|---|---|
| Orchestrator (Grok) | `max_orchestrator_vlm_concurrent` | 1 |
| Agent (Harper..Nova) | `max_agent_vlm_concurrent` | 5 |

Agent messages now include the screen frame as `image_url` content so all 5 agents see the actual screen, not just Grok.

---

## HTTP API

| Method | Route | Description |
|---|---|---|
| GET | `/` | Serves `panel.html` |
| GET | `/events` | SSE stream (primary data channel) |
| GET | `/frame` | Current raw frame + overlays JSON |
| POST | `/annotated` | Panel submits merged annotated PNG |
| GET | `/state` | Snapshot: frame_seq, agents, swarm_count |
| GET | `/swarm?after=N` | Swarm messages from index N |
| GET | `/swarm_image/{idx}` | Image attached to swarm message idx |
| GET | `/config` | Current config |
| POST | `/config` | Update and persist config |
| GET | `/event_log` | Last 200 event log entries |

---

## Configuration

All values in `config.json`, accessed via `hub.cfg(key, default)`.

| Key | Default | Description |
|---|---|---|
| `server_host` | `127.0.0.1` | HTTP bind address |
| `server_port` | `1234` | HTTP port |
| `vlm_endpoint_url` | | OpenAI-compatible chat completions URL |
| `vlm_model_name` | | Model identifier sent in request body |
| `vlm_timeout_seconds` | `120` | Per-request timeout |
| `vlm_request_delay_seconds` | `0` | Delay between VLM calls (0 when server throttles itself) |
| `max_orchestrator_vlm_concurrent` | `1` | Orchestrator semaphore |
| `max_agent_vlm_concurrent` | `5` | Agent semaphore |
| `max_parallel_agents` | `1` | Agent task concurrency |
| `capture_region` | | Norm coords `x1,y1,x2,y2` or empty for full screen |
| `capture_width` | `640` | Output PNG width |
| `capture_height` | `640` | Output PNG height |
| `capture_interval_seconds` | `3.0` | Max time between captures |
| `action_delay_seconds` | `0.15` | Delay between dispatched actions |
| `show_cursor` | `true` | Render cursor crosshair overlay |
| `cursor_color` | `#ff4444` | Cursor overlay color |
| `cursor_arm` | `14` | Cursor crosshair arm length in norm units |
| `brain_file` | `brain_agentic.py` | Brain module filename |
| `log_to_disk` | `true` | Write session logs and frames to disk |
| `log_dir` | `logs` | Directory for session logs |

---
"""
"""
## Brain API contract

The brain receives the hub module as its only argument.

```python
async def main(hub: ModuleType) -> None: ...
```

### Actions (enqueue via hub.actions)

```python
hub.actions(hub.click(x, y))
hub.actions(hub.double_click(x, y))
hub.actions(hub.right_click(x, y))
hub.actions(hub.type_text("text"))
hub.actions(hub.press_key("enter"))
hub.actions(hub.hotkey("ctrl+c"))
hub.actions(hub.scroll_up(x, y))
hub.actions(hub.scroll_down(x, y))
hub.actions(hub.drag(x1, y1, x2, y2))
```

All coordinate fields (`x`, `y`, `x1`, `y1`, `x2`, `y2`) are required. Missing fields raise `ValueError` — the hub never invents fallback coordinates.

### Overlays

```python
hub.overlays(hub.dot(x, y, label, color))
hub.overlays(hub.box(x1, y1, x2, y2, label, stroke_color, fill_color))
hub.overlays(hub.line(points, label, color))
```

All overlay dicts must include `closed`, `stroke`, and `fill` keys.

### VLM

```python
await hub.call_vlm_agent(messages, temperature=0.5, max_tokens=1024, agent_name="Harper")
await hub.call_vlm_orchestrator(messages, temperature=0.2, max_tokens=1200, agent_name="Grok")
```

### Grok JSON output schema

```json
{
  "actions": [
    {"action": "click", "x": 500, "y": 300},
    {"action": "type_text", "text": "hello"},
    {"action": "press_key", "key": "enter"},
    {"action": "hotkey", "keys": "ctrl+s"},
    {"action": "scroll_up", "x": 500, "y": 500},
    {"action": "scroll_down", "x": 500, "y": 500},
    {"action": "double_click", "x": 400, "y": 200},
    {"action": "right_click", "x": 400, "y": 200},
    {"action": "drag", "x1": 100, "y1": 100, "x2": 600, "y2": 400},
    {"action": "wait"}
  ],
  "phase": "EXECUTE",
  "is_complete": false,
  "next_goal": null,
  "progress": 0
}
```

`phase` must be one of `INTERPRET`, `PLAN`, `EXECUTE`, `EVALUATE`. Python writes it verbatim.
`hotkey.keys` must be a joined string (`"ctrl+s"`), never a list.

### Utilities

```python
hub.cfg(key, default)
hub.log_event(text, level)           # level: info | ok | warn | error
hub.set_agent_status(agent, status)  # idle | awaiting_vlm | thinking | acting | error
hub.swarm_message(agent, direction, text, image_b64, system)
await hub.get_frame()                # returns annotated PNG as base64 string
hub.request_fresh_frame()
```

---

## win32.py CLI

Called exclusively as a subprocess by `franz_hub.py`. Never imported.

```
python win32.py capture       --region x1,y1,x2,y2  --width 640  --height 640
python win32.py click         --pos x,y              --region ...
python win32.py double_click  --pos x,y              --region ...
python win32.py right_click   --pos x,y              --region ...
python win32.py type_text     --text "..."
python win32.py press_key     --key enter
python win32.py hotkey        --keys ctrl+s
python win32.py scroll_up     --pos x,y              --region ...  --clicks 3
python win32.py scroll_down   --pos x,y              --region ...  --clicks 3
python win32.py drag          --from_pos x,y         --to_pos x,y  --region ...
python win32.py cursor_pos    --region ...
python win32.py select_region
```

`select_region` opens a fullscreen transparent overlay. Drag to select, right-click for full screen, Escape to cancel. Outputs norm coords `x1,y1,x2,y2` to stdout and exits 0, or exits 2 on cancel.

---

## Running

```
python franz_hub.py
```

Optional flags:

```
--brain <filename>   Override brain_file from config
--skip-region        Skip the region selection dialog
```

On startup:
1. Loads `config.json`
2. Prompts for capture region via `select_region` overlay (unless `--skip-region`)
3. Loads the brain module
4. Starts HTTP server on `server_host:server_port`
5. Opens asyncio loop and calls `brain.main(hub)`

Open `http://127.0.0.1:1234` in Chrome to connect the panel.

---

## Requirements

- Windows (Win32 API required)
- Python 3.13+
- Google Chrome (for panel)
- An OpenAI-compatible chat completions endpoint (local or remote)
- No third-party Python packages (stdlib only: `ctypes`, `asyncio`, `http.server`, `subprocess`, `zlib`, `struct`)

---

## Session logging

When `log_to_disk` is true, each run creates a timestamped directory under `log_dir`:

```
logs/
  20250101_120000_000000/
    events.txt        <- all log_event and action entries
    20250101_120001_000000.png
    20250101_120004_000000.png
    ...
```

---

## Coordinate system

All coordinates are normalized integers `0-1000` mapping to the configured capture region.

```
screen pixels  <-->  norm 0-1000  <-->  panel canvas pixels
```

`win32.py` converts norm coords to real screen pixels using the capture region bounds.
The panel scales the same 0-1000 space to canvas dimensions when rendering overlays.

---

## Coding rules

- The brain makes all decisions. `franz_hub.py` makes none.
- All action helpers return dicts and have no side effects. Side effects happen only when the dict is passed to `hub.actions()`.
- `hotkey` takes one joined string: `"ctrl+c"`, never a list.
- `scroll_up` / `scroll_down` take `(x, y)` only, no clicks parameter at brain level.
- `drag` takes `(x1, y1, x2, y2)`, no `drag_start` / `drag_end`.
- Coordinates are always norm integers `0-1000`. Missing required coordinate fields raise `ValueError`.
- Grok owns `phase` in its JSON output. Python never infers phase from action list length.
- History is updated every cycle with actions taken, phase, progress, and any dispatch errors.
- No emojis, no non-ASCII characters anywhere.
- No hardcoded endpoints, ports, or model names in the brain; use `hub.cfg()`.
- SSE is primary; fallback polling activates only after SSE failure, never in parallel.
- SSE reconnect is attempted automatically after 5 seconds on connection loss.
