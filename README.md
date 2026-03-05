# Franz

A Windows computer-use AI swarm. Captures the screen, runs a 5-agent debate, and executes input actions to complete arbitrary tasks.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          franz_hub.py                            │
│   HTTP server  |  asyncio loop  |  SSE bus  |  action queue      │
│                |  VLM channels (orchestrator + agent)            │
└────────┬───────────────────┬──────────────────────┬─────────────┘
         │                   │                      │
  brain_agentic.py        win32.py             panel.html
  (intelligence)        (subprocess)           (Chrome UI)
```

| File | Role |
|---|---|
| `franz_hub.py` | Motherboard. Pure plumbing. Routes strings, executes actions, owns all queues and the HTTP server. Makes zero decisions. |
| `brain_agentic.py` | Intelligence. 5-agent debate swarm + Grok captain. All VLM calls and action decisions live here. |
| `win32.py` | Standalone CLI subprocess. Screen capture via GDI, all mouse/keyboard input via Win32 API. |
| `panel.html` | Single-file Chrome UI. Three-quadrant layout. Annotates frames, streams swarm wire, renders overlays. |
| `config.json` | All tuneable values. Read at runtime via `hub.cfg()`. |

---

## System diagram

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "background": "#050810",
    "primaryColor": "#0d1b2e",
    "primaryTextColor": "#a8d4ff",
    "primaryBorderColor": "#1e4a8a",
    "lineColor": "#2a6dd9",
    "secondaryColor": "#0a1628",
    "tertiaryColor": "#071020",
    "edgeLabelBackground": "#050810",
    "clusterBkg": "#080f1e",
    "clusterBorder": "#1e3a6e",
    "titleColor": "#4a9eff",
    "nodeTextColor": "#a8d4ff",
    "fontFamily": "Consolas, monospace"
  }
} }%%

flowchart LR
  subgraph CONFIG["config.json"]
    cfg["hub.cfg(key, default)"]
  end

  subgraph WIN32["win32.py  -  Win32 subprocess"]
    direction TB
    w_cap["capture\n--region --width --height\nreturns raw PNG bytes to stdout"]
    w_click["click / double_click / right_click\n--pos x,y --region"]
    w_type["type_text --text\npress_key --key\nhotkey --keys"]
    w_scroll["scroll_up / scroll_down\n--pos x,y --region --clicks"]
    w_drag["drag\n--from_pos --to_pos --region"]
    w_cur["cursor_pos --region\nreturns norm x,y to stdout"]
    w_sel["select_region\nfullscreen overlay\nexits 0 ok / 2 cancel"]
  end

  subgraph HUB["franz_hub.py  -  Motherboard  (zero decisions)"]
    direction TB

    subgraph HUB_BOOT["Startup"]
      h_cfg_load["_load_config()"]
      h_region["_run_select_region()"]
      h_brain_load["_load_brain(filename)"]
      h_server["ThreadingHTTPServer\nhost:port"]
      h_loop["asyncio.new_event_loop()"]
    end

    subgraph HUB_STATE["Shared state"]
      h_frame["_frame_b64\n_frame_seq\n_frame_event"]
      h_ann["_ann_pending_seq\n_ann_result_b64\n_ann_ready"]
      h_raw["_raw_b64_for_panel\n_overlays_for_panel"]
      h_aq["_action_queue\nasyncio.Queue"]
      h_swarm["_swarm_messages list\n_swarm_lock"]
      h_evlog["_event_log list\n_event_log_lock"]
      h_agents["_agent_states dict\n_agent_states_lock"]
      h_ovpend["_overlays_pending list\n_overlays_lock"]
    end

    subgraph HUB_SEM["VLM semaphores"]
      h_sem_orch["_vlm_orchestrator_semaphore\nmax_orchestrator_vlm_concurrent"]
      h_sem_agent["_vlm_agent_semaphore\nmax_agent_vlm_concurrent"]
    end

    subgraph HUB_TASKS["Async tasks"]
      h_capture["_capture_loop()\nwaits _capture_requested\nor capture_interval_seconds"]
      h_executor["_action_executor_loop()\ndrains _action_queue"]
    end

    subgraph HUB_HTTP["HTTP routes  (HubHandler)"]
      h_r_root["GET /\nserves panel.html"]
      h_r_events["GET /events\nSSE stream"]
      h_r_frame["GET /frame\nraw_b64 + overlays JSON"]
      h_r_ann["POST /annotated\nreceives merged PNG"]
      h_r_state["GET /state\nframe_seq agents swarm_count"]
      h_r_swarm["GET /swarm?after=N\nswarm messages slice"]
      h_r_img["GET /swarm_image/idx\nimage bytes"]
      h_r_cfg["GET|POST /config"]
      h_r_evlog["GET /event_log\nlast 200 entries"]
    end

    subgraph HUB_SSE["SSE bus  (_EventBus)"]
      h_bus["publish(event_type, data)\nfan-out to subscriber queues"]
      h_events["events: frame / frame_done\nstate / swarm / agent_status\nlog / connected"]
    end

    subgraph HUB_VLM["VLM HTTP  (_do_vlm_call)"]
      h_vlm["urllib POST to vlm_endpoint_url\nmodel / temperature / max_tokens\nreturns choices[0].message.content"]
    end

    subgraph HUB_API["Public brain API"]
      h_get_frame["get_frame()\nawaits _frame_event"]
      h_req_frame["request_fresh_frame()\nsets _capture_requested"]
      h_actions["actions(dict)\ncall_soon_threadsafe to _action_queue"]
      h_overlays["overlays(dict)\nappends _overlays_pending"]
      h_log["log_event(text, level)\nappends _event_log\npublishes SSE log"]
      h_status["set_agent_status(agent, status)\nupdates _agent_states\npublishes SSE agent_status"]
      h_swarm_msg["swarm_message(agent, dir, text, img, sys)\nappends _swarm_messages\npublishes SSE swarm"]
      h_call_agent["call_vlm_agent(messages, ...)\nacquires _vlm_agent_semaphore"]
      h_call_orch["call_vlm_orchestrator(messages, ...)\nacquires _vlm_orchestrator_semaphore"]
    end

    subgraph HUB_HELPERS["Action helpers (return dicts, no side effects)"]
      h_click["click(x,y)\ndouble_click(x,y)\nright_click(x,y)"]
      h_text["type_text(text)\npress_key(name)\nhotkey(combo)"]
      h_scroll["scroll_up(x,y)\nscroll_down(x,y)"]
      h_drag["drag(x1,y1,x2,y2)"]
      h_ovhelp["dot(x,y,label,color)\nbox(x1,y1,x2,y2,...)\nline(points,label,color)"]
    end

    subgraph HUB_LOG["Session logging"]
      h_disk["_log_to_disk(text)\n_save_frame_to_disk(b64)\nlogs/ timestamped dir"]
    end
  end

  subgraph BRAIN["brain_agentic.py  -  Intelligence"]
    direction TB
    b_main["async def main(hub)\nstate: goal / phase / progress / history"]

    subgraph BRAIN_AGENTS["5 debate agents  (asyncio.gather, parallel)"]
      b_harper["Harper\nResearch and Facts\nmax_tokens=1024"]
      b_benjamin["Benjamin\nLogic and Planning\nmax_tokens=1024"]
      b_lucas["Lucas\nCreative and Balance\nmax_tokens=1024"]
      b_atlas["Atlas\nGUI Navigation\nmax_tokens=1024"]
      b_nova["Nova\nTask Manager\nmax_tokens=1024"]
    end

    b_debate["_debate_round()\n3 rounds, each agent receives\nframe_b64 as image_url"]
    b_grok["Grok captain\ncall_vlm_orchestrator\nmax_tokens=1200\ntemp=0.2"]
    b_parse["parse JSON decision\nraise on empty / malformed\nlog error to swarm"]
    b_dispatch["_dispatch_action()\nraises ValueError on\nmissing coords or key"]
    b_history["update history every cycle\nphase + progress + actions\n+ dispatch errors  (cap 800)"]
    b_overlay["_make_progress_overlay()\nphase / goal / progress bar"]
  end

  subgraph PANEL["panel.html  -  Chrome UI"]
    direction TB
    p_sse["EventSource /events\nreconnects after 5s on loss"]
    p_frame["handleFrame(seq)\nGET /frame\nloadBaseImage\nrenderOverlays"]
    p_export["exportAnnotated()\nOffscreenCanvas\nPOST /annotated"]
    p_swarm["upsertAgentRow()\none row per agent\ncollapsed 2-line clamp\nexpanded 60vh scroll"]
    p_chips["upsertChip()\nagent status dots"]
    p_log["uiLog()\nevent log\nappend + auto-scroll"]
    p_layout["three-quadrant grid\nv-gutter col resize\nh-gutter row resize\nlocalStorage persist"]
    p_poll["fallbackPoll()\nonly after SSE error\nnever parallel"]
  end

  %% CONFIG wiring
  cfg -->|read at runtime| h_cfg_load
  cfg -->|read at runtime| b_main

  %% Startup sequence
  h_cfg_load --> h_region
  h_region -->|subprocess select_region| w_sel
  w_sel -->|norm coords stdout| h_region
  h_region --> h_brain_load
  h_brain_load --> h_server
  h_server --> h_loop
  h_loop -->|create_task| h_capture
  h_loop -->|create_task| h_executor
  h_loop -->|await brain.main| b_main

  %% Capture loop
  h_capture -->|subprocess capture| w_cap
  w_cap -->|raw PNG bytes| h_capture
  h_capture -->|cursor_pos subprocess| w_cur
  w_cur -->|norm x,y| h_capture
  h_capture -->|sets _raw_b64_for_panel\n_overlays_for_panel| h_raw
  h_capture -->|publish frame event| h_bus
  h_capture -->|awaits _ann_ready| h_ann
  h_capture -->|sets _frame_b64\n_frame_event.set| h_frame

  %% SSE bus to panel
  h_bus -->|SSE stream| h_r_events
  h_r_events -->|text/event-stream| p_sse

  %% Panel annotation pipeline
  p_sse -->|frame event| p_frame
  p_frame -->|GET /frame| h_r_frame
  h_r_frame -->|raw_b64 + overlays| h_raw
  p_frame --> p_export
  p_export -->|POST /annotated| h_r_ann
  h_r_ann -->|sets _ann_result_b64\ncall_soon_threadsafe _ann_ready.set| h_ann

  %% Brain frame access
  b_main -->|await get_frame| h_get_frame
  h_get_frame -->|awaits _frame_event| h_frame
  h_get_frame -->|returns annotated PNG b64| b_main

  %% Brain overlay
  b_main --> b_overlay
  b_overlay -->|hub.overlays(dict)| h_overlays
  h_overlays -->|appends| h_ovpend
  h_ovpend -->|consumed per frame| h_capture

  %% Debate
  b_main --> b_debate
  b_debate -->|asyncio.gather| b_harper
  b_debate -->|asyncio.gather| b_benjamin
  b_debate -->|asyncio.gather| b_lucas
  b_debate -->|asyncio.gather| b_atlas
  b_debate -->|asyncio.gather| b_nova
  b_harper -->|call_vlm_agent\nimage_url=frame_b64| h_call_agent
  b_benjamin -->|call_vlm_agent\nimage_url=frame_b64| h_call_agent
  b_lucas -->|call_vlm_agent\nimage_url=frame_b64| h_call_agent
  b_atlas -->|call_vlm_agent\nimage_url=frame_b64| h_call_agent
  b_nova -->|call_vlm_agent\nimage_url=frame_b64| h_call_agent
  h_call_agent -->|acquires sem| h_sem_agent
  h_sem_agent --> h_vlm
  h_vlm -->|HTTP POST| h_r_cfg
  h_vlm -->|response text| h_call_agent
  h_call_agent -->|agent text| b_debate
  b_debate -->|3 rounds accumulated| b_grok

  %% Grok
  b_grok -->|call_vlm_orchestrator| h_call_orch
  h_call_orch -->|acquires sem| h_sem_orch
  h_sem_orch --> h_vlm
  h_vlm -->|JSON string| h_call_orch
  h_call_orch -->|raw JSON string| b_grok
  b_grok --> b_parse

  %% Dispatch
  b_parse -->|decision.actions| b_dispatch
  b_dispatch -->|hub.actions(dict)| h_actions
  h_actions -->|call_soon_threadsafe| h_aq
  h_aq -->|dequeued by| h_executor
  h_executor -->|subprocess| w_click
  h_executor -->|subprocess| w_type
  h_executor -->|subprocess| w_scroll
  h_executor -->|subprocess| w_drag
  h_executor -->|request_fresh_frame| h_req_frame
  h_req_frame -->|sets _capture_requested| h_capture

  %% History + phase
  b_parse -->|phase verbatim| b_history
  b_dispatch --> b_history
  b_history -->|updates state| b_main

  %% Swarm wire
  b_harper -->|swarm_message| h_swarm_msg
  b_benjamin -->|swarm_message| h_swarm_msg
  b_lucas -->|swarm_message| h_swarm_msg
  b_atlas -->|swarm_message| h_swarm_msg
  b_nova -->|swarm_message| h_swarm_msg
  b_grok -->|swarm_message| h_swarm_msg
  h_swarm_msg -->|appends| h_swarm
  h_swarm_msg -->|publish swarm event| h_bus
  p_sse -->|swarm event| p_swarm

  %% Agent status
  b_main -->|set_agent_status| h_status
  h_status -->|publish agent_status| h_bus
  p_sse -->|agent_status event| p_chips

  %% Log
  b_main -->|log_event| h_log
  h_log -->|appends| h_evlog
  h_log -->|publish log event| h_bus
  p_sse -->|log event| p_log

  %% Panel fallback
  p_sse -->|on error only| p_poll
  p_poll -->|GET /state| h_r_state
  p_poll -->|GET /swarm| h_r_swarm

  %% Panel layout
  p_sse --> p_layout
  p_frame --> p_layout

  %% Logging to disk
  h_capture -->|_save_frame_to_disk| h_disk
  h_log -->|_log_to_disk| h_disk
  h_executor -->|_log_to_disk| h_disk
```

---

## Data flow

```
  brain              hub               win32          panel         VLM
    │                 │                  │              │             │
    │                 ├─ subprocess ─────►              │             │
    │                 ◄─ raw PNG ────────┤              │             │
    │                 │                  │              │             │
    │                 ├─ SSE: frame ─────────────────── ►             │
    │                 ◄─ GET /frame ──────────────────── ┤            │
    │                 │                  │   draw+export │            │
    │                 ◄─ POST /annotated ─────────────── ┤            │
    ◄─ get_frame() ───┤                  │              │             │
    │                 │                  │              │             │
    ├─ call_vlm_agent x5 ────────────────────────────────────────────►│
    ◄─ agent text ───────────────────────────────────────────────────-┤
    │                 │                  │              │             │
    ├─ call_vlm_orchestrator ────────────────────────────────────────►│
    ◄─ JSON decision ────────────────────────────────────────────────-┤
    │                 │                  │              │             │
    ├─ hub.actions() ─►                  │              │             │
    │                 ├─ subprocess ─────►              │             │
```

---

## Swarm loop

Each cycle: capture frame → 3 debate rounds (5 agents in parallel, each receives the screen image) → Grok synthesizes → dispatch actions.

```
                    ┌─────────────────┐
              ┌────►│   Cycle start   │◄──────────────────────┐
              │     └────────┬────────┘                       │
              │              │                                │
              │     ┌────────▼────────┐                       │
              │     │  Capture frame  │                       │
              │     └────────┬────────┘                       │
              │              │                                │
              │     ┌────────▼────────┐                       │
              │     │  Draw overlays  │                       │
              │     └────────┬────────┘                       │
              │              │                                │
              │     ┌────────▼────────┐                       │
              │     │ Debate rounds   │ (x3)                  │
              │     │  1 → 2 → 3      │                       │
              │     └──┬──┬──┬──┬──┬─┘                       │
              │        │  │  │  │  │                          │
              │   Harper Benjamin Lucas Atlas Nova            │
              │        │  │  │  │  │  (parallel, see screen) │
              │     ┌──▼──▼──▼──▼──▼─┐                       │
              │     │ Grok: synthesize│                       │
              │     └────────┬────────┘                       │
              │              │                                │
              │     ┌────────▼────────┐                       │
              │     │  Parse JSON     │                       │
              │     │  (phase owned   │                       │
              │     │   by Grok)      │                       │
              │     └────────┬────────┘                       │
              │              │                                │
              │     ┌────────▼────────┐                       │
              │     │ Dispatch actions│                       │
              │     └────────┬────────┘                       │
              │              │                                │
              │     ┌────────▼────────┐    ┌───────────────┐  │
              │     │  is_complete?   ├─yes─► next_goal     ├──┘
              │     └────────┬────────┘    └───────────────┘
              │              │ no
              │     ┌────────▼────────┐
              └─────┤ update history  │
                    │ phase/progress  │
                    └─────────────────┘
```

> **Note:** Grok's JSON output includes a `"phase"` field written verbatim by Python. Python never infers phase from action list length. History is updated every cycle with phase, progress, actions taken, and any dispatch errors.

---

## Panel layout

Three-quadrant layout. Both gutters are draggable. Positions persist in `localStorage`.

```
┌─────────────────────────┬─┬──────────────────────────┐
│                         │ │      Swarm Wire           │
│    Annotated View       │v│  one row per agent        │
│                         │g│  collapsed: 2-line clamp  │
│    canvas (CSS grid)    │u│  expanded: 60vh + scroll  │
│    overlays rendered    │t│  auto-scroll near bottom  │
│    exported via         │t│                           │
│    OffscreenCanvas      │e├───────────────────────────┤
│    POSTed /annotated    │r│  h-gutter                 │
│                         │ ├───────────────────────────┤
│                         │ │      Event Log            │
│                         │ │  append + auto-scroll     │
│                         │ │  newest at bottom         │
├─────────────────────────┴─┴──────────────────────────┤
│  Franz  |  seq: N  |  (SSE dot)                       │
└───────────────────────────────────────────────────────┘
```

---

## Annotation pipeline

```
  _capture_loop          panel.html              brain
       │                     │                     │
       │── screenshot ──────►│                     │
       │── SSE: frame{seq} ──►                     │
       │◄── GET /frame ───────┤                    │
       │         loadBaseImage + renderOverlays     │
       │         exportAnnotated (OffscreenCanvas)  │
       │◄── POST /annotated ──┤                    │
       │  _ann_result_b64 set │                     │
       │── _frame_event.set() ────────────────────►│
       │                      │         get_frame() resolves
```

---

## VLM channels

Two independent semaphores. Agent calls never block the captain.

| Channel | Semaphore key | Default |
|---|---|---|
| Orchestrator (Grok) | `max_orchestrator_vlm_concurrent` | 1 |
| Agent (Harper..Nova) | `max_agent_vlm_concurrent` | 5 |

Agent messages include the screen frame as `image_url` content — all 5 agents see the actual screen, not just Grok.

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
| `vlm_request_delay_seconds` | `0` | Delay between VLM calls |
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

## Brain API contract

```python
async def main(hub: ModuleType) -> None: ...
```

### Actions

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

All coordinate fields are required. Missing fields raise `ValueError` — the hub never invents fallback coordinates.

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
- No third-party Python packages — stdlib only: `ctypes`, `asyncio`, `http.server`, `subprocess`, `zlib`, `struct`

---

## Session logging

When `log_to_disk` is true, each run creates a timestamped directory under `log_dir`:

```
logs/
  20250101_120000_000000/
    events.txt
    20250101_120001_000000.png
    20250101_120004_000000.png
    ...
```

---

## Coordinate system

All coordinates are normalized integers `0–1000` mapping to the configured capture region.

```
screen pixels  <-->  norm 0-1000  <-->  panel canvas pixels
```

`win32.py` converts norm coords to real screen pixels using the capture region bounds.  
The panel scales the same `0–1000` space to canvas dimensions when rendering overlays.

---

## Coding rules

- The brain makes all decisions. `franz_hub.py` makes none.
- All action helpers return dicts and have no side effects. Side effects happen only when the dict is passed to `hub.actions()`.
- `hotkey` takes one joined string: `"ctrl+c"`, never a list.
- `scroll_up` / `scroll_down` take `(x, y)` only — no clicks parameter at brain level.
- `drag` takes `(x1, y1, x2, y2)` — no `drag_start` / `drag_end`.
- Coordinates are always norm integers `0–1000`. Missing required fields raise `ValueError`.
- Grok owns `phase` in its JSON output. Python never infers phase from action list length.
- History is updated every cycle with actions taken, phase, progress, and any dispatch errors.
- No emojis, no non-ASCII characters anywhere.
- No hardcoded endpoints, ports, or model names in the brain — use `hub.cfg()`.
- SSE is primary. Fallback polling activates only after SSE failure, never in parallel. SSE reconnect is attempted after 5 seconds on connection loss.
