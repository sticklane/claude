# /fleet reference — dashboard template

Contents: Data shape · Fill rules · Palette constraints · Template

Loaded on demand by step 3 of the skill. Contains the data shape, the fill
rules, and the full HTML template.

## Data shape

One record per agent, already normalized by step 2:

```json
{
  "label": "build task/03-auth-routes",
  "kind": "build-worker",
  "status": "running",
  "started": "14:21:07",
  "elapsed": "11m 12s",
  "snippet": "running acceptance: npm test -- auth",
  "output": "~/.claude/…/tasks/a1b2c3.output"
}
```

## Fill rules

- Replace `{{GENERATED_AT}}`, the four `{{N_*}}` counts, and the three marked
  blocks (`TILE ROW`, `TIMELINE ROWS`, `TABLE ROWS`) with generated markup.
  Everything else ships verbatim.
- Status is never color alone: every status renders glyph + word
  (`▶ running`, `◌ queued`, `✓ completed`, `✕ failed`).
- Timeline geometry: `t0 = min(started)`, `t1 = now`. Per bar,
  `left = (started − t0) / (t1 − t0)`, `width = ((ended || now) − started) /
  (t1 − t0)`, floored at 0.75% so short scouts stay visible. Order rows by
  start time. Each bar carries a `title` tooltip:
  `"<label> — <status>, started <started>, <elapsed>"`.
- Times in table cells and axis labels are pre-formatted strings
  (`HH:MM:SS`, `11m 12s`) — no client-side JS, no external requests.
- Escape `label`/`snippet`/`output` for HTML.

## Palette constraints

The template's status colors were validated for contrast and red/green CVD
separation on both surfaces. If you re-theme: keep every bar and glyph
color at >=3:1 contrast against both surfaces, and never let color carry
status alone — each status keeps its glyph + word, with the word in ink.

## Template

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fleet — open agents</title>
<style>
  :root {
    --page: #f9f9f7; --surface: #fcfcfb;
    --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
    --hairline: #e1e0d9; --ring: rgba(11,11,11,0.10);
    --running: #2a78d6; --completed: #0ca30c;
    --failed: #d03b3b; --queued: #898781;
    --viz-running: #2a78d6; --viz-done: #0ca30c;
    --viz-failed: #d03b3b; --viz-open: #898781;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --page: #0d0d0d; --surface: #1a1a19;
      --ink: #ffffff; --ink-2: #c3c2b7;
      --hairline: #2c2c2a; --ring: rgba(255,255,255,0.10);
      --running: #3987e5;
      --viz-running: #3987e5;
    }
  }
  * { box-sizing: border-box; margin: 0; }
  body {
    background: var(--page); color: var(--ink);
    font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 24px; max-width: 960px; margin-inline: auto;
  }
  header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; }
  h1 { font-size: 18px; font-weight: 600; }
  .stamp { color: var(--muted); font-size: 12px; }
  section {
    background: var(--surface); border: 1px solid var(--ring);
    border-radius: 8px; padding: 16px; margin-bottom: 16px;
  }
  h2 { font-size: 12px; font-weight: 600; color: var(--ink-2);
       text-transform: uppercase; letter-spacing: .04em; margin-bottom: 12px; }

  /* stat tiles */
  .tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
  .tile { border: 1px solid var(--hairline); border-radius: 8px; padding: 12px 14px; }
  .tile .n { font-size: 28px; font-weight: 600; }
  .tile .l { color: var(--ink-2); font-size: 12px; margin-top: 2px; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
         margin-right: 6px; vertical-align: 1px; }

  /* status chips — glyph carries the color, the word carries the meaning */
  .chip { display: inline-flex; align-items: center; gap: 6px;
          padding: 1px 8px; border-radius: 999px; font-size: 12px;
          color: var(--ink-2); border: 1px solid var(--hairline); }
  .chip b { font-weight: 600; font-size: 13px; }
  .s-running   .dot { background: var(--running); }   .s-running   b { color: var(--running); }
  .s-completed .dot { background: var(--completed); } .s-completed b { color: var(--completed); }
  .s-failed    .dot { background: var(--failed); }    .s-failed    b { color: var(--failed); }
  .s-queued    .dot { background: var(--queued); }    .s-queued    b { color: var(--queued); }

/* >>> viz:timeline-css BEGIN */
.viz-lane { display: grid; grid-template-columns: 180px 1fr; align-items: center; gap: 10px; padding: 4px 0; }
.viz-lane .name { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.viz-track { position: relative; height: 10px; border-radius: 4px; background: rgba(128, 128, 128, 0.25); }
.viz-bar { position: absolute; top: 0; height: 10px; border-radius: 4px; min-width: 4px; }
.viz-bar.viz-running { background: var(--viz-running, #d98a63); }
.viz-bar.viz-open { background: var(--viz-open, #6ea3c0); }
.viz-bar.viz-done { background: var(--viz-done, #3a4150); }
.viz-bar.viz-failed { background: var(--viz-failed, #c96262); }
.viz-bar.viz-stale { background: var(--viz-stale, #5a6070); }
.viz-bar.viz-blocked { background: var(--viz-blocked, #d9b063); }
.viz-axis { display: grid; grid-template-columns: 180px 1fr; gap: 10px; margin-top: 6px; }
.viz-axis div { display: flex; justify-content: space-between; font-size: 11px; font-variant-numeric: tabular-nums; color: var(--viz-muted, #898781); }
.viz-graphwrap { background: #161922; border-radius: 8px; padding: 8px; display: inline-block; }
/* .viz-node/.viz-edge carry no rules here on purpose: their colors are
   per-node inline SVG attributes (dag()'s STATUS_HEX lookup), and a CSS
   rule targeting them would win the cascade over those attributes and
   flatten every node/edge to one color. The classes exist as host hooks. */
/* <<< viz:timeline-css END */

  /* table */
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 11px; color: var(--muted); font-weight: 500;
       padding: 6px 10px; border-bottom: 1px solid var(--hairline); }
  td { padding: 8px 10px; border-bottom: 1px solid var(--hairline);
       vertical-align: top; font-size: 13px; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: color-mix(in srgb, var(--ink) 4%, transparent); }
  td.t { font-variant-numeric: tabular-nums; white-space: nowrap; color: var(--ink-2); }
  td .snip { display: block; color: var(--muted); font-size: 12px;
             font-family: ui-monospace, monospace; margin-top: 2px;
             overflow-wrap: anywhere; }
  td .path { color: var(--muted); font-size: 11px; font-family: ui-monospace, monospace; }
</style>
</head>
<body>
<header>
  <h1>Fleet — open agents</h1>
  <div class="stamp">snapshot {{GENERATED_AT}} · re-run /fleet to refresh</div>
</header>

<section>
  <div class="tiles">
    <!-- TILE ROW: one tile per status, in this fixed order -->
    <div class="tile"><div class="n">{{N_RUNNING}}</div><div class="l"><span class="s-running"><span class="dot"></span></span>running</div></div>
    <div class="tile"><div class="n">{{N_QUEUED}}</div><div class="l"><span class="s-queued"><span class="dot"></span></span>queued</div></div>
    <div class="tile"><div class="n">{{N_COMPLETED}}</div><div class="l"><span class="s-completed"><span class="dot"></span></span>completed</div></div>
    <div class="tile"><div class="n">{{N_FAILED}}</div><div class="l"><span class="s-failed"><span class="dot"></span></span>failed</div></div>
  </div>
</section>

<section>
  <h2>Timeline</h2>
  <!-- TIMELINE ROWS: one .viz-lane per agent, ordered by start time -->
  <div class="viz-lane">
    <div class="name">build task/03-auth-routes</div>
    <div class="viz-track"><div class="viz-bar viz-running" style="left:12%;width:88%"
      title="build task/03-auth-routes — running, started 14:21:07, 11m 12s"></div></div>
  </div>
  <div class="viz-axis"><div></div><div><span>{{T0}}</span><span>now</span></div></div>
</section>

<section>
  <h2>Agents</h2>
  <table>
    <thead><tr><th>Agent</th><th>Status</th><th>Started</th><th>Elapsed</th></tr></thead>
    <tbody>
    <!-- TABLE ROWS: one tr per agent, running first, then queued, failed, completed -->
    <tr>
      <td>build task/03-auth-routes
        <span class="snip">running acceptance: npm test -- auth</span>
        <span class="path">~/.claude/…/tasks/a1b2c3.output</span></td>
      <td><span class="chip s-running"><b>▶</b>running</span></td>
      <td class="t">14:21:07</td>
      <td class="t">11m 12s</td>
    </tr>
    </tbody>
  </table>
</section>
</body>
</html>
```
