// v2.6.41 | 2025-09-11
//
// PyGPT Runtime for streaming Markdown in QWebEngine:
//
// - QWebChannel bridge
// - markdown-it with lightweight KaTeX placeholders (no KaTeX compute on hot path)
// - Dollar-delimiter math placeholders: $...$ and $$...$$ (finalize/idle/always policy)
// - No inline hljs compute in renderer (final code highlight is deferred)
// - Lightweight, scroll+rAF driven hljs highlighting (no IntersectionObserver)
// - Async, chunked KaTeX rendering to avoid UI stalls
// - Async, scheduled tail promotion (small chunks, UI-friendly)
// - Adaptive snapshots, minimal DOM churn
// - Incremental, non-flickering code streaming (frozen prefix + plain tail)
// - Unified, bridge-based logger injected to all subsystems (no console)
// - Buffered logging with auto-flush when QWebChannel is ready
// - Runtime promotion of language from first-line directive during streaming
// - Stream-aware renderer (no linkify on hot path) and plain-text streaming fallback for huge code
// - Final highlight hard caps to avoid OOM on gigantic blocks
// - Precomputed code meta (len/head/tail and nl for full renderer) to avoid heavy .textContent reads

(function () {
  'use strict';

  // ==========================================================================
  // 0) Utils & Config
  // ==========================================================================

  // Small helper utilities used across the runtime.
  class Utils {
    static g(name, dflt) { return (typeof window[name] !== 'undefined') ? window[name] : dflt; }
    static now() { return (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now(); }

    // reuse a single detached element to reduce allocations on hot path.
    static escapeHtml(s) {
      const d = Utils._escDiv || (Utils._escDiv = document.createElement('div'));
      d.textContent = String(s ?? '');
      return d.innerHTML;
    }

    static countNewlines(s) {
      if (!s) return 0;
      let c = 0, i = -1; while ((i = s.indexOf('\n', i + 1)) !== -1) c++;
      return c;
    }
    static reEscape(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
    // Schedule a function in idle time (falls back to setTimeout).
    static idle(fn, timeout) {
      if ('requestIdleCallback' in window) return requestIdleCallback(fn, { timeout: timeout || 800 });
      return setTimeout(fn, 50);
    }
    // Cancel idle callback if possible (safe for fallback).
    static cancelIdle(id) {
      try {
        if ('cancelIdleCallback' in window) cancelIdleCallback(id);
        else clearTimeout(id);
      } catch (_) {}
    }
    static get SE() { return document.scrollingElement || document.documentElement; }

    // shared UTF-8 decoder to avoid per-call allocations.
    static utf8Decode(bytes) {
      if (!Utils._td) Utils._td = new TextDecoder('utf-8');
      return Utils._td.decode(bytes);
    }
  }

  // ==========================================================================
  // 0.1) Unified Logger (bridge-based; injected into classes)
  // ==========================================================================

  class Logger {
    // Production-grade logger with queue, batch sending and soft caps.
    constructor(cfg) {
      this.cfg = cfg || { LOG: {} };
      // Queue holds strings waiting to be sent over QWebChannel to Python.
      this.queue = [];
      this.queueBytes = 0; // approximate UTF-16 bytes (chars * 2)
      this.armed = false;
      this.maxTries = 480; // ~8s @60fps
      this.tries = 0;
      this.bridge = null;
      this._idleId = 0;              // idle-callback handle (backoff-friendly)
      this._lastFlushQueueBytes = 0; // last known bytes to detect progress

      // Centralized rAF manager handle (bound by runtime); falls back to microtasks until available.
      this.raf = null;
      this._rafScheduled = false;
      this._rafKey = { t: 'Logger:tick' };

      // Soft limits; tunable from window.* if desired.
      const L = this.cfg.LOG || {};
      this.MAX_QUEUE = Utils.g('LOG_MAX_QUEUE', L.MAX_QUEUE ?? 400);
      this.MAX_BYTES = Utils.g('LOG_MAX_BYTES', L.MAX_BYTES ?? 256 * 1024); // 256 KiB
      this.BATCH_MAX = Utils.g('LOG_BATCH_MAX', L.BATCH_MAX ?? 64);
      this.RATE_LIMIT_PER_SEC = Utils.g('LOG_RATE_LIMIT_PER_SEC', L.RATE_LIMIT_PER_SEC ?? 0); // 0 == off
      this._rlWindowMs = 1000;
      this._rlCount = 0;
      this._rlWindowStart = Utils.now();
    }
    // Connect a QWebChannel bridge and flush any pending messages.
    bindBridge(bridge) {
      this.bridge = bridge || null;
      // When bridge arrives, flush pending messages respecting caps.
      this.flush();
    }
    // Bind RafManager instance – ensures no direct requestAnimationFrame usage in Logger.
    bindRaf(raf) {
      this.raf = raf || null;
    }
    // Check if debug logging is enabled for a namespace.
    isEnabled(ns) {
      if (!ns) return !!(window.STREAM_DEBUG || window.MD_LANG_DEBUG);
      const key1 = ns + '_DEBUG';
      const key2 = ns.toUpperCase() + '_DEBUG';
      return !!(window[key1] || window[key2] || window.STREAM_DEBUG || window.MD_LANG_DEBUG);
    }
    // Pretty-view string (safe truncation for logs).
    pv(s, n = 120) {
      if (!s) return '';
      s = String(s);
      if (s.length <= n) return s.replace(/\n/g, '\\n');
      const k = Math.floor(n / 2);
      return (s.slice(0, k) + ' … ' + s.slice(-k)).replace(/\n/g, '\\n');
    }
    j(o) { try { return JSON.stringify(o); } catch (_) { try { return String(o); } catch(__){ return '[unserializable]'; } } }
    _emit(msg) {
      // Attempt batch-capable sink if provided by the bridge
      try {
        if (this.bridge) {
          if (typeof this.bridge.log_batch === 'function') { this.bridge.log_batch([String(msg)]); return true; }
          if (typeof this.bridge.logBatch === 'function') { this.bridge.logBatch([String(msg)]); return true; }
          if (typeof this.bridge.log === 'function') { this.bridge.log(String(msg)); return true; }
        }
        if (window.runtime && runtime.bridge && typeof runtime.bridge.log === 'function') {
          runtime.bridge.log(String(msg)); return true;
        }
      } catch (_) {}
      return false;
    }
    _emitBatch(arr) {
      try {
        if (!arr || !arr.length) return 0;
        // Prefer batch API if present; otherwise fallback to per-line
        if (this.bridge && typeof this.bridge.log_batch === 'function') { this.bridge.log_batch(arr.map(String)); return arr.length; }
        if (this.bridge && typeof this.bridge.logBatch === 'function') { this.bridge.logBatch(arr.map(String)); return arr.length; }
        if (this.bridge && typeof this.bridge.log === 'function') {
          for (let i = 0; i < arr.length; i++) this.bridge.log(String(arr[i]));
          return arr.length;
        }
      } catch (_) {}
      return 0;
    }
    _maybeDropForCaps(len) {
      // Hard cap queue size and memory to guard Python process via QWebChannel.
      if (this.queue.length <= this.MAX_QUEUE && this.queueBytes <= this.MAX_BYTES) return;
      const targetLen = Math.floor(this.MAX_QUEUE * 0.8);
      const targetBytes = Math.floor(this.MAX_BYTES * 0.8);
      // Drop oldest first; keep newest events
      while ((this.queue.length > targetLen || this.queueBytes > targetBytes) && this.queue.length) {
        const removed = this.queue.shift();
        this.queueBytes -= (removed ? removed.length * 2 : 0);
      }
      // Add one synthetic notice to indicate dropped logs (avoid recursion)
      const notice = '[LOGGER] queue trimmed due to caps';
      this.queue.unshift(notice);
      this.queueBytes += notice.length * 2;
    }
    _passRateLimit() {
      if (!this.RATE_LIMIT_PER_SEC || this.RATE_LIMIT_PER_SEC <= 0) return true;
      const now = Utils.now();
      if (now - this._rlWindowStart > this._rlWindowMs) {
        this._rlWindowStart = now;
        this._rlCount = 0;
      }
      if (this._rlCount >= this.RATE_LIMIT_PER_SEC) return false;
      return true;
    }
    // Push a log line; try immediate send, otherwise enqueue.
    log(text) {
      const msg = String(text);
      // If bridge is available, try immediate emit to avoid queueing overhead.
      if (this.bridge && (typeof this.bridge.log === 'function' || typeof this.bridge.log_batch === 'function' || typeof this.bridge.logBatch === 'function')) {
        if (this._passRateLimit()) {
          const ok = this._emit(msg);
          if (ok) return true;
        }
      }
      // Enqueue with caps; avoid unbounded growth
      this.queue.push(msg);
      this.queueBytes += msg.length * 2;
      this._maybeDropForCaps(msg.length);
      this._arm();
      return false;
    }
    // Debug wrapper respecting per-namespace switch.
    debug(ns, line, ctx) {
      if (!this.isEnabled(ns)) return false;
      let msg = `[${ns}] ${line || ''}`;
      if (typeof ctx !== 'undefined') msg += ' ' + this.j(ctx);
      return this.log(msg);
    }
    // Send a batch of lines if bridge is ready.
    flush(maxPerTick = this.BATCH_MAX) {
      // Centralized flush – no direct cancelAnimationFrame here; RafManager governs frames.
      if (!this.bridge && !(window.runtime && runtime.bridge && typeof runtime.bridge.log === 'function')) return 0;
      const n = Math.min(maxPerTick, this.queue.length);
      if (!n) return 0;
      const batch = this.queue.splice(0, n);
      // Update memory accounting before attempting emit to eagerly unlock memory
      let bytes = 0; for (let i = 0; i < batch.length; i++) bytes += batch[i].length * 2;
      this.queueBytes = Math.max(0, this.queueBytes - bytes);
      const sent = this._emitBatch(batch);

      // fix byte accounting for partial sends (re-queue remaining with accurate bytes).
      if (sent < batch.length) {
        const remain = batch.slice(sent);
        let remBytes = 0; for (let i = 0; i < remain.length; i++) remBytes += remain[i].length * 2;
        // Prepend remaining back to the queue preserving order
        for (let i = remain.length - 1; i >= 0; i--) this.queue.unshift(remain[i]);
        this.queueBytes += remBytes;
      }
      return sent;
    }
    _scheduleTick(tick) {
      // Prefer idle scheduling when bridge isn't available yet – avoids 60fps RAF churn.
      const preferIdle = !this.bridge;

      const scheduleIdle = () => {
        try { if (this._idleId) Utils.cancelIdle(this._idleId); } catch (_) {}
        // Use requestIdleCallback when available, fallback to small timeout. Keeps UI cold on idle.
        this._idleId = Utils.idle(() => { this._idleId = 0; tick(); }, 800);
      };

      if (preferIdle) { scheduleIdle(); return; }

      if (this._rafScheduled) return;
      this._rafScheduled = true;
      const run = () => { this._rafScheduled = false; tick(); };
      try {
        if (this.raf && typeof this.raf.schedule === 'function') {
          this.raf.schedule(this._rafKey, run, 'Logger', 3);
        } else if (typeof runtime !== 'undefined' && runtime.raf && typeof runtime.raf.schedule === 'function') {
          runtime.raf.schedule(this._rafKey, run, 'Logger', 3);
        } else {
          Promise.resolve().then(run);
        }
      } catch (_) {
        Promise.resolve().then(run);
      }
    }
    _arm() {
      if (this.armed) return;
      this.armed = true; this.tries = 0;
      const tick = () => {
        if (!this.armed) return;
        this.flush();
        this.tries++;
        if (this.queue.length === 0 || this.tries > this.maxTries) {
          this.armed = false;
          try { if (this._idleId) Utils.cancelIdle(this._idleId); } catch (_) {}
          this._idleId = 0;
          return;
        }
        this._scheduleTick(tick);
      };
      this._scheduleTick(tick);
    }
  }

  // ==========================================================================
  // RafManager (rAF-only)
  // ==========================================================================

  class RafManager {
    // rAF-only task pump with soft budget per flush to prevent long frames.
    constructor(cfg) {
      this.cfg = cfg || { RAF: {}, ASYNC: {} };
      this.tasks = new Map();
      this.groups = new Map();
      // rAF pump state
      this.tickId = 0;
      this._mode = 'raf';
      this.scheduled = false;
      this._flushInProgress = false;

      const R = (this.cfg && this.cfg.RAF) || {};
      this.FLUSH_BUDGET_MS = Utils.g('RAF_FLUSH_BUDGET_MS', R.FLUSH_BUDGET_MS ?? 7);
      this.MAX_TASKS_PER_FLUSH = Utils.g('RAF_MAX_TASKS_PER_FLUSH', R.MAX_TASKS_PER_FLUSH ?? 120);
    }
    // Start the pumping loop if needed.
    _armPump() {
      if (this.scheduled) return;
      this.scheduled = true;

      // Focus/visibility-agnostic, rAF-only scheduling (no timers, no watchdogs).
      const canRAF = typeof requestAnimationFrame === 'function';
      if (canRAF) {
        this._mode = 'raf';
        try {
          this.tickId = requestAnimationFrame(() => this.flush());
          return;
        } catch (_) {}
      }
      // Fallback without timers: schedule a microtask flush.
      this._mode = 'raf';
      Promise.resolve().then(() => this.flush());
    }
    // Schedule a function with an optional group and priority.
    schedule(key, fn, group = 'default', priority = 0) {
      if (!key) key = { k: 'anon' };
      this.tasks.set(key, { fn, group, priority });
      if (group) {
        let set = this.groups.get(group);
        if (!set) { set = new Set(); this.groups.set(group, set); }
        set.add(key);
      }
      this._armPump();
    }
    // Run pending tasks within a time and count budget.
    flush() {
      // Cancel rAF handle if any; nothing else (timers removed).
      try { if (this.tickId) cancelAnimationFrame(this.tickId); } catch (_) {}
      this.tickId = 0;
      this.scheduled = false;

      // Snapshot tasks and clear the map; re-queue leftovers if we exceed budget.
      const list = Array.from(this.tasks.entries()).map(([key, v]) => ({ key, ...v }));
      this.tasks.clear();
      list.sort((a, b) => a.priority - b.priority);

      const start = Utils.now();
      let processed = 0;

      for (let idx = 0; idx < list.length; idx++) {
        const t = list[idx];
        try { t.fn(); } catch (_) {}
        processed++;
        if (t.group) {
          const set = this.groups.get(t.group);
          if (set) { set.delete(t.key); if (set.size === 0) this.groups.delete(t.group); }
        }

        // Soft budget: if long, re-queue the rest for next rAF.
        const elapsed = Utils.now() - start;
        if (processed >= this.MAX_TASKS_PER_FLUSH || elapsed >= this.FLUSH_BUDGET_MS) {
          for (let j = idx + 1; j < list.length; j++) {
            const r = list[j];
            this.tasks.set(r.key, { fn: r.fn, group: r.group, priority: r.priority });
          }
          this._armPump();
          return;
        }
      }

      if (this.tasks.size) {
        this._armPump();
      }
    }
    // Force immediate flush or schedule next frame.
    kick(forceImmediate = true) {
      if (forceImmediate && this.tasks.size) {
        if (this._flushInProgress) return;
        this._flushInProgress = true;
        try { this.scheduled = true; this.flush(); } catch (_) {} finally { this._flushInProgress = false; }
        return;
      }
      this._armPump();
    }
    // Cancel a specific scheduled task by key.
    cancel(key) {
      const t = this.tasks.get(key);
      if (!t) return;
      this.tasks.delete(key);
      if (t.group) {
        const set = this.groups.get(t.group);
        if (set) { set.delete(key); if (set.size === 0) this.groups.delete(t.group); }
      }
    }
    // Cancel all tasks in a group.
    cancelGroup(group) {
      const set = this.groups.get(group);
      if (!set) return;
      for (const key of set) this.tasks.delete(key);
      this.groups.delete(group);
    }
    // Cancel everything and reset the pump.
    cancelAll() {
      this.tasks.clear();
      this.groups.clear();
      try { if (this.tickId) cancelAnimationFrame(this.tickId); } catch (_) {}
      this.tickId = 0;
      this.scheduled = false;
    }
    isScheduled(key) { return this.tasks.has(key); }

    // Awaitable "next frame" helper – resolves on next flush.
    nextFrame() {
      return new Promise((resolve) => {
        const key = { t: 'raf:nextFrame', i: Math.random() };
        this.schedule(key, () => resolve(), 'RafNext', 0);
      });
    }
  }

  // Return math rendering policy from window.MATH_STREAM_MODE.
  function getMathMode() {
    const v = String(window.MATH_STREAM_MODE || 'finalize-only').toLowerCase();
    return (v === 'idle' || v === 'always' || v === 'finalize-only') ? v : 'finalize-only';
  }

  // ==========================================================================
  // 0.2) Async runner (cooperative yielding for heavy tasks)
  // ==========================================================================

  class AsyncRunner {
    // Cooperative scheduler (rAF-based) for CPU-heavy tasks (keeps UI responsive).
    constructor(cfg, raf) {
      this.cfg = cfg || {};
      this.raf = raf || null;
      const A = this.cfg.ASYNC || {};
      this.SLICE_MS = Utils.g('ASYNC_SLICE_MS', A.SLICE_MS ?? 12);
      this.MIN_YIELD_MS = Utils.g('ASYNC_MIN_YIELD_MS', A.MIN_YIELD_MS ?? 0); // kept only for config compatibility
    }
    // Check whether we should yield control to the browser.
    _inputPending() {
      try {
        const s = navigator && navigator.scheduling;
        return !!(s && s.isInputPending && s.isInputPending({ includeContinuous: true }));
      } catch (_) { return false; }
    }
    shouldYield(startTs) {
      if (this._inputPending()) return true;
      return (Utils.now() - startTs) >= this.SLICE_MS;
    }
    // Yield cooperatively via next rAF frame (with a safe fallback).
    async yield() {
      // Centralized rAF yield; fallback to a tiny timer if raf manager is not ready yet.
      if (this.raf && typeof this.raf.nextFrame === 'function') {
        await this.raf.nextFrame();
        return;
      }
      if (typeof runtime !== 'undefined' && runtime.raf && typeof runtime.raf.nextFrame === 'function') {
        await runtime.raf.nextFrame();
        return;
      }
      await new Promise(r => setTimeout(r, 16));
    }
    // Process items in small batches with periodic yields.
    async forEachChunk(arr, fn, label) {
      if (!arr || !arr.length) return;
      let start = Utils.now();
      for (let i = 0; i < arr.length; i++) {
        await fn(arr[i], i);
        if (this.shouldYield(start)) { await this.yield(); start = Utils.now(); }
      }
    }
  }

  // ==========================================================================
  // Config
  // ==========================================================================

  class Config {
    constructor() {
      // Process identifier (passed from host).
      this.PID = Utils.g('PID', 0);

      // UI: scroll behavior and busy/zoom signalling thresholds (milliseconds / pixels).
      this.UI = {
        AUTO_FOLLOW_REENABLE_PX: Utils.g('AUTO_FOLLOW_REENABLE_PX', 8),     // Enable auto-follow when near bottom
        SCROLL_NEAR_MARGIN_PX: Utils.g('SCROLL_NEAR_MARGIN_PX', 450),      // How close to bottom is considered "near"
        INTERACTION_BUSY_MS: Utils.g('UI_INTERACTION_BUSY_MS', 140),       // Minimum busy time for interactions
        ZOOM_BUSY_MS: Utils.g('UI_ZOOM_BUSY_MS', 300)                      // Minimum busy time for zoom
      };

      // FAB (floating action button) visibility and debounce.
      this.FAB = {
        SHOW_DOWN_THRESHOLD_PX: Utils.g('SHOW_DOWN_THRESHOLD_PX', 0),      // Show "down" arrow when scroll distance is large
        TOGGLE_DEBOUNCE_MS: Utils.g('FAB_TOGGLE_DEBOUNCE_MS', 100)         // Debounce for icon/text toggles
      };

      // Highlighting controls and per-frame budget.
      this.HL = {
        PER_FRAME: Utils.g('HL_PER_FRAME', 2),                             // How many code blocks to highlight per frame
        DISABLE_ALL: Utils.g('DISABLE_SYNTAX_HIGHLIGHT', false)            // Global off switch for hljs
      };

      // Intersection-like margins (we do our own scan, but these guide budgets).
      this.OBSERVER = {
        CODE_ROOT_MARGIN: Utils.g('CODE_ROOT_MARGIN', '1000px 0px 1000px 0px'),
        BOX_ROOT_MARGIN: Utils.g('BOX_ROOT_MARGIN', '1500px 0px 1500px 0px'),
        CODE_THRESHOLD: [0, 0.001], BOX_THRESHOLD: 0
      };

      // Viewport scan preload distance (in pixels).
      this.SCAN = { PRELOAD_PX: Utils.g('SCAN_PRELOAD_PX', 1000) };

      // Code scroll behavior (auto-follow re-enable margin and near-bottom margin).
      this.CODE_SCROLL = {
        AUTO_FOLLOW_REENABLE_PX: Utils.g('CODE_AUTO_FOLLOW_REENABLE_PX', 8),
        NEAR_MARGIN_PX: Utils.g('CODE_SCROLL_NEAR_MARGIN_PX', 48)
      };

      // Stream (snapshot) budgets and queue limits.
      this.STREAM = {
        MAX_PER_FRAME: Utils.g('STREAM_MAX_PER_FRAME', 8),                 // How many chunks to process per frame
        EMERGENCY_COALESCE_LEN: Utils.g('STREAM_EMERGENCY_COALESCE_LEN', 300), // If queue grows beyond, coalesce
        COALESCE_MODE: Utils.g('STREAM_COALESCE_MODE', 'fixed'),           // fixed | adaptive
        SNAPSHOT_MAX_STEP: Utils.g('STREAM_SNAPSHOT_MAX_STEP', 8000),      // Upper bound for adaptive step
        // Bounds for queue to prevent memory growth on bursty streams
        QUEUE_MAX_ITEMS: Utils.g('STREAM_QUEUE_MAX_ITEMS', 1200),
        PRESERVE_CODES_MAX: Utils.g('STREAM_PRESERVE_CODES_MAX', 120)      // Max code blocks to attempt reuse
      };

      // Math (KaTeX) idle batching and per-batch hint.
      this.MATH = {
        IDLE_TIMEOUT_MS: Utils.g('MATH_IDLE_TIMEOUT_MS', 800),
        BATCH_HINT: Utils.g('MATH_BATCH_HINT', 24)
      };

      // Icon URLs (provided by host app).
      this.ICONS = {
        EXPAND: Utils.g('ICON_EXPAND', ''), COLLAPSE: Utils.g('ICON_COLLAPSE', ''),
        CODE_MENU: Utils.g('ICON_CODE_MENU', ''), CODE_COPY: Utils.g('ICON_CODE_COPY', ''),
        CODE_RUN: Utils.g('ICON_CODE_RUN', ''), CODE_PREVIEW: Utils.g('ICON_CODE_PREVIEW', '')
      };

      // Localized UI strings.
      this.LOCALE = {
        PREVIEW: Utils.g('LOCALE_PREVIEW', 'Preview'),
        RUN: Utils.g('LOCALE_RUN', 'Run'),
        COLLAPSE: Utils.g('LOCALE_COLLAPSE', 'Collapse'),
        EXPAND: Utils.g('LOCALE_EXPAND', 'Expand'),
        COPY: Utils.g('LOCALE_COPY', 'Copy'),
        COPIED: Utils.g('LOCALE_COPIED', 'Copied')
      };

      // Code block styling theme (hljs theme key or custom).
      this.CODE_STYLE = Utils.g('CODE_SYNTAX_STYLE', 'default');

      // Adaptive snapshot profile for plain text.
      this.PROFILE_TEXT = {
        base: Utils.g('PROFILE_TEXT_BASE', 4),                 // Base step (chars) between snapshots
        growth: Utils.g('PROFILE_TEXT_GROWTH', 1.28),          // Growth factor for adaptive
        minInterval: Utils.g('PROFILE_TEXT_MIN_INTERVAL', 4),  // Minimum time between snapshots (ms)
        softLatency: Utils.g('PROFILE_TEXT_SOFT_LATENCY', 60), // If idle for this long, force a snapshot
        adaptiveStep: Utils.g('PROFILE_TEXT_ADAPTIVE_STEP', false)
      };

      // Adaptive snapshot profile for code (line-aware).
      this.PROFILE_CODE = {
        base: 2048,                 // Fewer snapshots during fence-open warm-up (reduce transient fragments)
        growth: 2.6,                // Ramp step quickly if adaptive is enabled
        minInterval: 500,           // Minimum time between snapshots (ms) to avoid churn
        softLatency: 1200,          // Force snapshot only after a noticeable idle (ms)
        minLinesForHL: 50, minCharsForHL: 5000,
        promoteMinInterval: 300, promoteMaxLatency: 800, promoteMinLines: 50,
        adaptiveStep: Utils.g('PROFILE_CODE_ADAPTIVE_STEP', true),
        // Hard switches to plain streaming (no incremental hljs, minimal DOM churn)
        stopAfterLines: 300,        // Turn off incremental hljs very early
        streamPlainAfterLines: 0,   // Belt-and-suspenders: enforce plain mode soon after
        streamPlainAfterChars: 0,   // Also guard huge single-line code (chars cap)
        maxFrozenChars: 32000,      // If promotions slipped through, cap before spans grow too large
        finalHighlightMaxLines: Utils.g('PROFILE_CODE_FINAL_HL_MAX_LINES', 1000),
        finalHighlightMaxChars: Utils.g('PROFILE_CODE_FINAL_HL_MAX_CHARS', 350000)
      };

      // Debounce for heavy resets (ms).
      this.RESET = {
        HEAVY_DEBOUNCE_MS: Utils.g('RESET_HEAVY_DEBOUNCE_MS', 24)
      };

      // Logging caps (used by Logger).
      this.LOG = {
        MAX_QUEUE: Utils.g('LOG_MAX_QUEUE', 400),
        MAX_BYTES: Utils.g('LOG_MAX_BYTES', 256 * 1024),
        BATCH_MAX: Utils.g('LOG_BATCH_MAX', 64),
        RATE_LIMIT_PER_SEC: Utils.g('LOG_RATE_LIMIT_PER_SEC', 0)
      };

      // Async tuning for background work.
      this.ASYNC = {
        SLICE_MS: Utils.g('ASYNC_SLICE_MS', 12),
        MIN_YIELD_MS: Utils.g('ASYNC_MIN_YIELD_MS', 0),
        MD_NODES_PER_SLICE: Utils.g('ASYNC_MD_NODES_PER_SLICE', 12)
      };

      // RAF pump tuning (budget per frame).
      this.RAF = {
        FLUSH_BUDGET_MS: Utils.g('RAF_FLUSH_BUDGET_MS', 7),
        MAX_TASKS_PER_FLUSH: Utils.g('RAF_MAX_TASKS_PER_FLUSH', 120)
      };

      // Markdown tuning – allow/disallow indented code blocks.
      this.MD = {
        ALLOW_INDENTED_CODE: Utils.g('MD_ALLOW_INDENTED_CODE', false)
      };

      // Custom markup rules for simple tags in text.
      this.CUSTOM_MARKUP_RULES = Utils.g('CUSTOM_MARKUP_RULES', [
        { name: 'cmd',   open: '[!cmd]',   close: '[/!cmd]',   tag: 'div',     className: 'cmd', innerMode: 'text' },
        { name: 'think', open: '[!think]', close: '[/!think]', tag: 'think', className: '',    innerMode: 'text' }
      ]);
    }
  }

  // ==========================================================================
  // 1) DOM references
  // ==========================================================================

  class DOMRefs {
    constructor() { this.els = {}; this.domOutputStream = null; this.domStreamMsg = null; }
    // Cache frequently used elements by id.
    init() {
      const ids = [
        'container','_nodes_','_append_input_','_append_output_before_','_append_output_',
        '_append_live_','_footer_','_loader_','tips','scrollFab','scrollFabIcon'
      ];
      ids.forEach(id => { this.els[id] = document.getElementById(id); });
    }
    // Get element by id (reads cache first).
    get(id) { return this.els[id] || document.getElementById(id); }
    // Reset ephemeral pointers (used during stream).
    resetEphemeral() { this.domStreamMsg = null; }
    // Release refs and restore default scroll behavior.
    cleanup() {
      this.resetEphemeral(); this.domOutputStream = null; this.els = {};
      try { history.scrollRestoration = "auto"; } catch (_) {}
    }
    // Faster clear of a container by avoiding innerHTML='' (which is slow on large trees).
    fastClear(id) {
      const el = this.get(id);
      if (!el) return null;
      // Fast paths:
      if (el.firstChild) {
        // Prefer replaceChildren, fallback to textContent.
        if (el.replaceChildren) el.replaceChildren();
        else el.textContent = '';
      }
      return el;
    }

    // Clear and ensure paint on next frame (await before reading layout).
    async fastClearAndPaint(id) {
      const el = this.fastClear(id);
      if (!el) return null;
      // Yield to the next frame through the centralized RafManager to ensure repaint.
      try {
        if (typeof runtime !== 'undefined' && runtime.raf && typeof runtime.raf.nextFrame === 'function') {
          await runtime.raf.nextFrame();
        } else {
          await new Promise(r => setTimeout(r, 16));
        }
      } catch (_) {}
      return el;
    }

    // Hard clear by temporarily hiding element to avoid intermediate paints.
    fastClearHidden(id) {
      const el = this.get(id);
      if (!el) return null;
      const prevDisplay = el.style.display;
      el.style.display = 'none';       // pause paints
      if (el.replaceChildren) el.replaceChildren();
      else el.textContent = '';
      el.style.display = prevDisplay;  // resume paints
      return el;
    }
    // Replace element node by a shallow clone (drops children).
    hardReplaceByClone(id) {
      const el = this.get(id);
      if (!el || !el.parentNode) return null;
      const clone = el.cloneNode(false);
      try { el.replaceWith(clone); } catch (_) { el.innerHTML = ''; }
      this.els[id] = clone;
      if (id === '_append_output_') this.domOutputStream = clone;
      return clone;
    }
    // Clear streaming containers and transient state.
    hardResetStreamContainers() {
      this.resetEphemeral();
      this.domOutputStream = null;
      this.fastClearHidden('_append_output_before_');
      this.fastClearHidden('_append_output_');
    }
    // Return output stream container, caching reference.
    getStreamContainer() {
      if (this.domOutputStream && this.domOutputStream.isConnected) return this.domOutputStream;
      const el = this.get('_append_output_'); if (el) this.domOutputStream = el; return el;
    }
    // Get or create current streaming message container (.msg-box > .msg > .md-snapshot-root).
    getStreamMsg(create, name_header) {
      const container = this.getStreamContainer(); if (!container) return null;
      if (this.domStreamMsg && this.domStreamMsg.isConnected) return this.domStreamMsg;

      let box = container.querySelector('.msg-box'); let msg = null;
      if (!box && create) {
        box = document.createElement('div'); box.classList.add('msg-box', 'msg-bot');
        if (name_header) {
          const name = document.createElement('div'); name.classList.add('name-header','name-bot'); name.innerHTML = name_header; box.appendChild(name);
        }
        msg = document.createElement('div'); msg.classList.add('msg');
        const snap = document.createElement('div'); snap.className = 'md-snapshot-root';
        msg.appendChild(snap); box.appendChild(msg); container.appendChild(box);
      } else if (box) {
        msg = box.querySelector('.msg');
        if (msg && !msg.querySelector('.md-snapshot-root')) {
          const snap = document.createElement('div'); snap.className = 'md-snapshot-root'; msg.appendChild(snap);
        }
      }
      if (msg) this.domStreamMsg = msg;
      return msg;
    }
    // Clear the "before" area (older messages area).
    clearStreamBefore() {
      if (typeof window.hideTips === 'function') { window.hideTips(); }
      const el = this.fastClearHidden('_append_output_before_');
      if (el) { /* no-op */ }
    }
    // Clear output stream area.
    clearOutput() { this.hardResetStreamContainers(); }
    // Clear messages list and reset state.
    clearNodes() {
      this.clearStreamBefore();
      const el = this.fastClearHidden('_nodes_'); if (el) { el.classList.add('empty_list'); }
      this.resetEphemeral();
    }
    // Clear input area.
    clearInput() { this.fastClearHidden('_append_input_'); }
    // Clear live area and hide it.
    clearLive() {
      const el = this.fastClearHidden('_append_live_'); if (!el) return;
      el.classList.remove('visible');
      el.classList.add('hidden');
      this.resetEphemeral();
    }
  }

  // ==========================================================================
  // 2) Code scroll state manager
  // ==========================================================================

  class CodeScrollState {
    constructor(cfg, raf) {
      this.cfg = cfg;
      this.raf = raf;
      this.map = new WeakMap();
      this.rafMap = new WeakMap();
      this.rafIds = new Set(); // legacy
      this.rafKeyMap = new WeakMap();
    }
    // Get or create per-code element state.
    state(el) {
      let s = this.map.get(el);
      if (!s) { s = { autoFollow: false, lastScrollTop: 0, userInteracted: false, freezeUntil: 0 }; this.map.set(el, s); }
      return s;
    }
    // Check if code block is already finalized (not streaming).
    isFinalizedCode(el) {
      if (!el || el.tagName !== 'CODE') return false;
      if (el.dataset && el.dataset._active_stream === '1') return false;
      const highlighted = (el.getAttribute('data-highlighted') === 'yes') || el.classList.contains('hljs');
      return highlighted;
    }
    // Is element scrolled close to the bottom by a margin?
    isNearBottomEl(el, margin = 100) {
      if (!el) return true;
      const distance = el.scrollHeight - el.clientHeight - el.scrollTop;
      return distance <= margin;
    }
    // Scroll code element to the bottom respecting interaction state.
    scrollToBottom(el, live = false, force = false) {
      if (!el || !el.isConnected) return;
      if (!force && this.isFinalizedCode(el)) return;

      const st = this.state(el);
      const now = Utils.now();
      if (!force && st.freezeUntil && now < st.freezeUntil) return;

      const distNow = el.scrollHeight - el.clientHeight - el.scrollTop;
      if (!force && distNow <= 1) { st.lastScrollTop = el.scrollTop; return; }

      const marginPx = live ? 96 : this.cfg.CODE_SCROLL.NEAR_MARGIN_PX;
      const behavior = 'instant';

      if (!force) {
        if (live && st.autoFollow !== true) return;
        if (!live && !(st.autoFollow === true || this.isNearBottomEl(el, marginPx) || !st.userInteracted)) return;
      }

      try { el.scrollTo({ top: el.scrollHeight, behavior }); } catch (_) { el.scrollTop = el.scrollHeight; }
      st.lastScrollTop = el.scrollTop;
    }
    // Schedule bottom scroll in rAF (coalesces multiple calls).
    scheduleScroll(el, live = false, force = false) {
      if (!el || !el.isConnected) return;
      if (!force && this.isFinalizedCode(el)) return;
      if (this.rafMap.get(el)) return;
      this.rafMap.set(el, true);

      let key = this.rafKeyMap.get(el);
      if (!key) { key = { t: 'codeScroll', el }; this.rafKeyMap.set(el, key); }

      this.raf.schedule(key, () => {
        this.rafMap.delete(el);
        this.scrollToBottom(el, live, force);
      }, 'CodeScroll', 0);
    }
    // Attach scroll/wheel/touch handlers to manage auto-follow state.
    attachHandlers(codeEl) {
      if (!codeEl || codeEl.dataset.csListeners === '1') return;
      codeEl.dataset.csListeners = '1';
      const st = this.state(codeEl);

      const onScroll = (ev) => {
        const top = codeEl.scrollTop;
        const isUser = !!(ev && ev.isTrusted === true);
        const now = Utils.now();

        if (this.isFinalizedCode(codeEl)) {
          if (isUser) st.userInteracted = true;
          st.autoFollow = false;
          st.lastScrollTop = top;
          return;
        }

        if (isUser) {
          if (top + 1 < st.lastScrollTop) {
            st.autoFollow = false; st.userInteracted = true; st.freezeUntil = now + 1000;
          } else if (this.isNearBottomEl(codeEl, this.cfg.CODE_SCROLL.AUTO_FOLLOW_REENABLE_PX)) {
            st.autoFollow = true;
          }
        } else {
          if (this.isNearBottomEl(codeEl, this.cfg.CODE_SCROLL.AUTO_FOLLOW_REENABLE_PX)) st.autoFollow = true;
        }
        st.lastScrollTop = top;
      };

      const onWheel = (ev) => {
        st.userInteracted = true;
        const now = Utils.now();

        if (this.isFinalizedCode(codeEl)) { st.autoFollow = false; return; }

        if (ev.deltaY < 0) { st.autoFollow = false; st.freezeUntil = now + 1000; }
        else if (this.isNearBottomEl(codeEl, this.cfg.CODE_SCROLL.AUTO_FOLLOW_REENABLE_PX)) { st.autoFollow = true; }
      };

      codeEl.addEventListener('scroll', onScroll, { passive: true });
      codeEl.addEventListener('wheel', onWheel, { passive: true });
      codeEl.addEventListener('touchstart', function () { st.userInteracted = true; }, { passive: true });
    }
    // Ensure code starts scrolled to bottom once after insert.
    initCodeBottomOnce(codeEl) {
      if (!codeEl || !codeEl.isConnected) return;
      if (codeEl.dataset && codeEl.dataset._active_stream === '1') return;
      if (codeEl.dataset && codeEl.dataset.csInitBtm === '1') return;
      const wrapper = codeEl.closest('.code-wrapper');
      if (!wrapper) return;

      codeEl.dataset.csInitBtm = '1';
      const key = { t: 'codeInitBottom', el: codeEl };
      this.raf.schedule(key, () => {
        if (!codeEl.isConnected) return;
        try {
          this.scrollToBottom(codeEl, false, true);
          const st = this.state(codeEl);
          st.autoFollow = false;
          st.lastScrollTop = codeEl.scrollTop;
        } catch (_) {}
      }, 'CodeScroll', 0);
    }
    // Attach handlers to all bot code blocks under root (or document).
    initScrollableBlocks(root) {
      const scope = root || document;
      let nodes = [];
      if (scope.nodeType === 1 && scope.closest && scope.closest('.msg-box.msg-bot')) {
        nodes = scope.querySelectorAll('pre code');
      } else {
        nodes = document.querySelectorAll('.msg-box.msg-bot pre code');
      }
      if (!nodes.length) return;
      nodes.forEach((code) => {
        this.attachHandlers(code);
        if (code.dataset._active_stream === '1') {
          const st = this.state(code);
          st.autoFollow = true;
          this.scheduleScroll(code, true, false);
        } else {
          this.initCodeBottomOnce(code);
        }
      });
    }
    // Transfer stored scroll state between elements (after replace).
    transfer(oldEl, newEl) {
      if (!oldEl || !newEl || oldEl === newEl) return;
      const oldState = this.map.get(oldEl);
      if (oldState) this.map.set(newEl, { ...oldState });
      this.attachHandlers(newEl);
    }
    // Cancel any scheduled scroll tasks for code blocks.
    cancelAllScrolls() {
      try { this.raf.cancelGroup('CodeScroll'); } catch (_) {}
      this.rafMap = new WeakMap();
      this.rafIds.clear();
    }
  }

  // ==========================================================================
  // 3) Highlighter (hljs) + rAF viewport scan
  // ==========================================================================

  class Highlighter {
    constructor(cfg, codeScroll, raf) {
      this.cfg = cfg;
      this.codeScroll = codeScroll;
      this.raf = raf;
      this.hlScheduled = false;
      this.hlQueue = [];
      this.hlQueueSet = new Set();
      this.scanScheduled = false;

      // Global scanning state for budgeted viewport scans (prevents long frames).
      this._globalScanState = null;
      // Budget per scan step (ms) – based on RAF budget hint with a small clamp.
      const hint = (cfg && cfg.RAF && cfg.RAF.FLUSH_BUDGET_MS) ? cfg.RAF.FLUSH_BUDGET_MS : 7;
      this.SCAN_STEP_BUDGET_MS = Math.max(3, Math.min(12, hint));
    }
    // Global switch to skip all highlighting.
    isDisabled() { return !!this.cfg.HL.DISABLE_ALL; }
    // Configure hljs once (safe if hljs not present).
    initHLJS() {
      if (this.isDisabled()) return;
      if (typeof hljs !== 'undefined' && hljs) { try { hljs.configure({ ignoreUnescapedHTML: true }); } catch (_) {} }
    }
    // Check if code is near viewport (with preload).
    _nearViewport(el) {
      const preload = this.cfg.SCAN.PRELOAD_PX;
      const vh = window.innerHeight || Utils.SE.clientHeight || 800;
      const r = el.getBoundingClientRect();
      return r.bottom >= -preload && r.top <= (vh + preload);
    }
    // Queue a code element for highlight; skip active streaming code and heavy-known cases.
    queue(codeEl, activeCode) {
      if (this.isDisabled()) return;
      if (!codeEl || !codeEl.isConnected) return;
      if (activeCode && codeEl === activeCode.codeEl) return;
      if (codeEl.getAttribute('data-highlighted') === 'yes') return;
      if (codeEl.dataset && (codeEl.dataset.hlStreamSuspended === '1' || codeEl.dataset.finalHlSkip === '1')) return; // skip heavy blocks intentionally left plain
      if (!codeEl.closest('.msg-box.msg-bot')) return;
      if (!this.hlQueueSet.has(codeEl)) { this.hlQueueSet.add(codeEl); this.hlQueue.push(codeEl); }
      if (!this.hlScheduled) {
        this.hlScheduled = true;
        this.raf.schedule('HL:flush', () => this.flush(activeCode), 'Highlighter', 1);
      }
    }
    // Process a small batch of code elements per frame.
    flush(activeCode) {
      if (this.isDisabled()) { this.hlScheduled = false; this.hlQueueSet.clear(); this.hlQueue.length = 0; return; }
      this.hlScheduled = false;
      let count = 0;
      while (this.hlQueue.length && count < this.cfg.HL.PER_FRAME) {
        const el = this.hlQueue.shift();
        if (el && el.isConnected) this.safeHighlight(el, activeCode);
        if (el) this.hlQueueSet.delete(el);
        count++;
        try {
          const sched = (navigator && navigator.scheduling && navigator.scheduling.isInputPending) ? navigator.scheduling : null;
          if (sched && sched.isInputPending({ includeContinuous: true })) {
            if (this.hlQueue.length) {
              this.hlScheduled = true;
              this.raf.schedule('HL:flush', () => this.flush(activeCode),  'Highlighter', 1);
            }
            return;
          }
        } catch (_) {}
      }
      if (this.hlQueue.length) {
        this.hlScheduled = true;
        this.raf.schedule('HL:flush', () => this.flush(activeCode), 'Highlighter', 1);
      }
    }
    // Highlight a single code block with safety checks and scroll preservation.
    safeHighlight(codeEl, activeCode) {
      if (this.isDisabled()) return;
      if (!window.hljs || !codeEl || !codeEl.isConnected) return;
      if (!codeEl.closest('.msg-box.msg-bot')) return;
      if (codeEl.getAttribute('data-highlighted') === 'yes') return;
      if (activeCode && codeEl === activeCode.codeEl) return;

      // fast-skip final highlight for gigantic blocks using precomputed meta.
      try {
        const wrap = codeEl.closest('.code-wrapper');
        const maxLines = this.cfg.PROFILE_CODE.finalHighlightMaxLines | 0;
        const maxChars = this.cfg.PROFILE_CODE.finalHighlightMaxChars | 0;

        // Prefer wrapper meta if available to avoid .textContent on huge nodes.
        let lines = NaN, chars = NaN;
        if (wrap) {
          const nlAttr = wrap.getAttribute('data-code-nl');
          const lenAttr = wrap.getAttribute('data-code-len');
          if (nlAttr) lines = parseInt(nlAttr, 10);
          if (lenAttr) chars = parseInt(lenAttr, 10);
        }

        if ((Number.isFinite(lines) && maxLines > 0 && lines > maxLines) ||
            (Number.isFinite(chars) && maxChars > 0 && chars > maxChars)) {
          codeEl.classList.add('hljs');
          codeEl.setAttribute('data-highlighted', 'yes');
          codeEl.dataset.finalHlSkip = '1';
          try { this.codeScroll.attachHandlers(codeEl); } catch (_) {}
          this.codeScroll.scheduleScroll(codeEl, false, false);
          return;
        }

        // Fallback to reading actual text only if wrapper meta is missing.
        if (!Number.isFinite(lines) || !Number.isFinite(chars)) {
          const txt0 = codeEl.textContent || '';
          const ln0 = Utils.countNewlines(txt0);
          if ((maxLines > 0 && ln0 > maxLines) || (maxChars > 0 && txt0.length > maxChars)) {
            codeEl.classList.add('hljs');
            codeEl.setAttribute('data-highlighted', 'yes');
            codeEl.dataset.finalHlSkip = '1';
            try { this.codeScroll.attachHandlers(codeEl); } catch (_) {}
            this.codeScroll.scheduleScroll(codeEl, false, false);
            return;
          }
        }
      } catch (_) { /* safe fallback */ }

      const wasNearBottom = this.codeScroll.isNearBottomEl(codeEl, 16);
      const st = this.codeScroll.state(codeEl);
      const shouldAutoScrollAfter = (st.autoFollow === true) || wasNearBottom;

      try {
        try { codeEl.classList.remove('hljs'); codeEl.removeAttribute('data-highlighted'); } catch (_) {}
        const txt = codeEl.textContent || '';
        codeEl.textContent = txt; // ensure no stale spans remain
        hljs.highlightElement(codeEl);
        codeEl.setAttribute('data-highlighted', 'yes');
      } catch (_) {
        if (!codeEl.classList.contains('hljs')) codeEl.classList.add('hljs');
      } finally {
        try { this.codeScroll.attachHandlers(codeEl); } catch (_) {}
        const needInitForce = (codeEl.dataset && (codeEl.dataset.csInitBtm === '1' || codeEl.dataset.justFinalized === '1'));
        const mustScroll = shouldAutoScrollAfter || needInitForce;
        if (mustScroll) this.codeScroll.scheduleScroll(codeEl, false, !!needInitForce);
        if (codeEl.dataset) {
          if (codeEl.dataset.csInitBtm === '1') codeEl.dataset.csInitBtm = '0';
          if (codeEl.dataset.justFinalized === '1') codeEl.dataset.justFinalized = '0';
        }
      }
    }

    // Start a budgeted global scan – split across frames to avoid long blocking.
    _startGlobalScan(activeCode) {
      if (this.isDisabled()) return;
      const preload = this.cfg.SCAN_PRELOAD_PX || this.cfg.SCAN.PRELOAD_PX;
      const vh = window.innerHeight || Utils.SE.clientHeight || 800;
      const rectTop = 0 - preload, rectBottom = vh + preload;
      const nodes = Array.from(document.querySelectorAll('.msg-box.msg-bot pre code:not([data-highlighted="yes"])'));
      this._globalScanState = { nodes, idx: 0, rectTop, rectBottom, activeCode };
      this._scanGlobalStep();
    }
    // Continue global scan for visible code elements under a time budget.
    _scanGlobalStep() {
      const state = this._globalScanState;
      if (!state || !state.nodes || state.idx >= state.nodes.length) { this._globalScanState = null; return; }
      const start = Utils.now();
      while (state.idx < state.nodes.length) {
        const code = state.nodes[state.idx++];
        if (!code || !code.isConnected) continue;
        if (state.activeCode && code === state.activeCode.codeEl) continue;
        try {
          const r = code.getBoundingClientRect();
          if (r.bottom >= state.rectTop && r.top <= state.rectBottom) this.queue(code, state.activeCode);
        } catch (_) {}
        if ((Utils.now() - start) >= this.SCAN_STEP_BUDGET_MS) {
          // Schedule next slice to keep UI responsive.
          this.raf.schedule('HL:scanStep', () => this._scanGlobalStep(), 'Highlighter', 2);
          return;
        }
      }
      this._globalScanState = null;
    }

    // Observe new code blocks and queue those near the viewport.
    observeNewCode(root, opts, activeCode) {
      const scope = root || document;
      let nodes;
      if (scope.nodeType === 1 && scope.closest && scope.closest('.msg-box.msg-bot')) nodes = scope.querySelectorAll('pre code');
      else nodes = document.querySelectorAll('.msg-box.msg-bot pre code');
      if (!nodes || !nodes.length) return;

      const options = Object.assign({ deferLastIfStreaming: false, minLinesForLast: 2, minCharsForLast: 120 }, (opts || {}));
      nodes.forEach((code) => {
        if (!code.closest('.msg-box.msg-bot')) return;
        this.codeScroll.attachHandlers(code);
        if (this.isDisabled()) return;
        if (activeCode && code === activeCode.codeEl) return;

        if (options.deferLastIfStreaming && activeCode && code === activeCode.codeEl) {
          const tailLen = (activeCode.tailEl && activeCode.tailEl.textContent) ? activeCode.tailEl.textContent.length : 0;
          const tailLines = (typeof activeCode.tailLines === 'number') ? activeCode.tailLines : 0;
          if (tailLines < options.minLinesForLast && tailLen < options.minCharsForLast) return;
        }
        if (this._nearViewport(code)) this.queue(code, activeCode);
      });
    }
    // Schedule a viewport scan in a budgeted way.
    scheduleScanVisibleCodes(activeCode) {
      if (this.isDisabled()) return;

      // Fast bail-out: nothing to highlight and no active streaming code.
      try {
        const anyCandidate = document.querySelector('.msg-box.msg-bot pre code:not([data-highlighted="yes"])');
        const hasActive = !!(activeCode && activeCode.codeEl && activeCode.codeEl.isConnected);
        if (!anyCandidate && !hasActive) return;
      } catch (_) { /* safe fallback */ }

      // If a scan is already in progress, just ensure next step is scheduled; otherwise schedule start.
      if (this._globalScanState) {
        this.raf.schedule('HL:scanStep', () => this._scanGlobalStep(), 'Highlighter', 2);
        return;
      }
      if (this.scanScheduled) return;
      this.scanScheduled = true;
      this.raf.schedule('HL:scan', () => {
        this.scanScheduled = false;
        this._startGlobalScan(activeCode || null);
      }, 'Highlighter', 2);
    }

    // Direct scan (synchronous) – used in places where root scope is small.
    scanVisibleCodes(activeCode) {
      this._startGlobalScan(activeCode || null);
    }
    // Scan only inside a given root (synchronous, small scopes).
    scanVisibleCodesInRoot(root, activeCode) {
      if (this.isDisabled()) return;
      const preload = this.cfg.SCAN_PRELOAD_PX || this.cfg.SCAN.PRELOAD_PX;
      const vh = window.innerHeight || Utils.SE.clientHeight || 800;
      const rectTop = 0 - preload, rectBottom = vh + preload;
      const scope = root || document;
      const nodes = scope.querySelectorAll('.msg-box.msg-bot pre code:not([data-highlighted="yes"])');
      // Local root scans tend to be small – keep them synchronous for simplicity.
      nodes.forEach((code) => {
        if (!code.isConnected) return;
        if (activeCode && code === activeCode.codeEl) return;
        const r = code.getBoundingClientRect();
        if (r.bottom >= rectTop && r.top <= rectBottom) this.queue(code, activeCode);
      });
    }
    installBoxObserver() { /* no-op */ }
    // Visit bot message boxes and call callback (used for local scans).
    observeMsgBoxes(root, onBoxIntersect) {
      const scope = root || document;
      let boxes;
      if (scope.nodeType === 1) boxes = scope.querySelectorAll('.msg-box.msg-bot');
      else boxes = document.querySelectorAll('.msg-box.msg-bot');
      boxes.forEach((box) => { onBoxIntersect && onBoxIntersect(box); });
    }
    // Clear all internal queues and scheduled jobs.
    cleanup() {
      try { this.raf.cancelGroup('Highlighter'); } catch (_) {}
      this.hlScheduled = false;
      this.scanScheduled = false;
      this._globalScanState = null;
      this.hlQueueSet.clear(); this.hlQueue.length = 0;
    }
  }

  // ==========================================================================
  // 4) Custom Markup Processor
  // ==========================================================================

  class CustomMarkup {
    // Logger-aware processor; no console usage.
    constructor(cfg, logger) {
      this.cfg = cfg || { CUSTOM_MARKUP_RULES: [] };
      this.logger = logger || new Logger(cfg);
      this.__compiled = null;
    }
    _d(line, ctx) { try { this.logger.debug('CM', line, ctx); } catch (_) {} }

    // Compile rules once; also precompile strict and whitespace-tolerant "full match" regexes.
    compile(rules) {
      const src = Array.isArray(rules) ? rules : (window.CUSTOM_MARKUP_RULES || this.cfg.CUSTOM_MARKUP_RULES || []);
      const compiled = [];
      for (const r of src) {
        if (!r || typeof r.open !== 'string' || typeof r.close !== 'string') continue;
        const tag = (r.tag || 'span').toLowerCase();
        const className = (r.className || r.class || '').trim();
        const innerMode = (r.innerMode === 'markdown-inline' || r.innerMode === 'text') ? r.innerMode : 'text';

        const re = new RegExp(Utils.reEscape(r.open) + '([\\s\\S]*?)' + Utils.reEscape(r.close), 'g');
        const reFull = new RegExp('^' + Utils.reEscape(r.open) + '([\\s\\S]*?)' + Utils.reEscape(r.close) + '$');
        const reFullTrim = new RegExp('^\\s*' + Utils.reEscape(r.open) + '([\\s\\S]*?)' + Utils.reEscape(r.close) + '\\s*$');

        const item = { name: r.name || tag, tag, className, innerMode, open: r.open, close: r.close, re, reFull, reFullTrim };
        compiled.push(item);
        this._d('COMPILE_RULE', { name: item.name, tag: item.tag, innerMode: item.innerMode, open: item.open, close: item.close });
      }
      if (compiled.length === 0) {
        const open = '[!cmd]', close = '[/!cmd]';
        const item = {
          name: 'cmd', tag: 'p', className: 'cmd', innerMode: 'text', open, close,
          re: new RegExp(Utils.reEscape(open) + '([\\s\\S]*?)' + Utils.reEscape(close), 'g'),
          reFull: new RegExp('^' + Utils.reEscape(open) + '([\\s\\S]*?)' + Utils.reEscape(close) + '$'),
          reFullTrim: new RegExp('^\\s*' + Utils.reEscape(open) + '([\\s\\S]*?)' + Utils.reEscape(close) + '\\s*$')
        };
        compiled.push(item);
        this._d('COMPILE_RULE_FALLBACK', { name: item.name });
      }
      return compiled;
    }
    // Ensure rules are compiled and cached.
    ensureCompiled() {
      if (!this.__compiled) {
        this.__compiled = this.compile(window.CUSTOM_MARKUP_RULES || this.cfg.CUSTOM_MARKUP_RULES);
        this._d('ENSURE_COMPILED', { count: this.__compiled.length });
      }
      return this.__compiled;
    }
    // Replace rules set (also exposes rules on window).
    setRules(rules) {
      this.__compiled = this.compile(rules);
      window.CUSTOM_MARKUP_RULES = Array.isArray(rules) ? rules.slice() : (this.cfg.CUSTOM_MARKUP_RULES || []).slice();
      this._d('SET_RULES', { count: this.__compiled.length });
    }
    // Return current rules as array.
    getRules() {
      const list = (window.CUSTOM_MARKUP_RULES ? window.CUSTOM_MARKUP_RULES.slice()
                                               : (this.cfg.CUSTOM_MARKUP_RULES || []).slice());
      this._d('GET_RULES', { count: list.length });
      return list;
    }

    // Context guards
    isInsideForbiddenContext(node) {
      const p = node.parentElement; if (!p) return true;
      return !!p.closest('pre, code, kbd, samp, var, script, style, textarea, .math-pending, .hljs, .code-wrapper');
    }
    isInsideForbiddenElement(el) {
      if (!el) return true;
      return !!el.closest('pre, code, kbd, samp, var, script, style, textarea, .math-pending, .hljs, .code-wrapper');
    }

    // Global finder on a single text blob (original per-text-node logic).
    findNextMatch(text, from, rules) {
      let best = null;
      for (const rule of rules) {
        rule.re.lastIndex = from;
        const m = rule.re.exec(text);
        if (m) {
          const start = m.index, end = rule.re.lastIndex;
          if (!best || start < best.start) best = { rule, start, end, inner: m[1] || '' };
        }
      }
      return best;
    }

    // Strict full match of a pure text node (legacy path).
    findFullMatch(text, rules) {
      for (const rule of rules) {
        if (rule.reFull) {
          const m = rule.reFull.exec(text);
          if (m) return { rule, inner: m[1] || '' };
        } else {
          // Legacy safety net (should not normally execute).
          rule.re.lastIndex = 0;
          const m = rule.re.exec(text);
          if (m && m.index === 0 && (rule.re.lastIndex === text.length)) {
            const m2 = rule.re.exec(text);
            if (!m2) return { rule, inner: m[1] || '' };
          }
        }
      }
      return null;
    }

    // Set inner content according to the rule's mode.
    setInnerByMode(el, mode, text, MD) {
      if (mode === 'markdown-inline' && typeof window.markdownit !== 'undefined') {
        try {
          if (MD && typeof MD.renderInline === 'function') { el.innerHTML = MD.renderInline(text || ''); return; }
          const tempMD = window.markdownit({ html: false, linkify: true, breaks: true, highlight: () => '' });
          el.innerHTML = tempMD.renderInline(text || ''); return;
        } catch (_) {}
      }
      el.textContent = text || '';
    }

    // Try to replace an entire <p> that is a full custom markup match.
    _tryReplaceFullParagraph(el, rules, MD) {
      if (!el || el.tagName !== 'P') return false;
      if (this.isInsideForbiddenElement(el)) {
        this._d('P_SKIP_FORBIDDEN', { tag: el.tagName });
        return false;
      }
      const t = el.textContent || '';
      if (t.indexOf('[!') === -1) return false;

      for (const rule of rules) {
        if (!rule || rule.tag !== 'p') continue;
        const m = rule.reFullTrim ? rule.reFullTrim.exec(t) : null;
        if (!m) continue;

        const out = document.createElement('p');
        if (rule.className) out.className = rule.className;
        out.setAttribute('data-cm', rule.name);
        const innerText = m[1] || '';
        this.setInnerByMode(out, rule.innerMode, innerText, MD);

        try { el.replaceWith(out); } catch (_) {
          const parent = el.parentNode; if (parent) parent.replaceChild(out, el);
        }

        this._d('P_REPLACED', { rule: rule.name, preview: this.logger.pv(t, 160) });
        return true;
      }
      this._d('P_NO_FULL_MATCH', { preview: this.logger.pv(t, 160) });
      return false;
    }

    // Apply custom markup with two-phase strategy:
    // 1) Full-paragraph tolerant pass (survives linkify splitting).
    // 2) Legacy per-text-node pass for partial inline cases.
    apply(root, MD) {
      this.ensureCompiled();
      const rules = this.__compiled;
      if (!root || !rules || !rules.length) return;

      const scope = (root.nodeType === 1 || root.nodeType === 11) ? root : document;
      try {
        const paragraphs = (typeof scope.querySelectorAll === 'function') ? scope.querySelectorAll('p') : [];
        this._d('P_TOLERANT_SCAN_START', { count: paragraphs.length });

        if (paragraphs && paragraphs.length) {
          for (let i = 0; i < paragraphs.length; i++) {
            const p = paragraphs[i];
            if (p && p.getAttribute && p.getAttribute('data-cm')) continue;
            // Quick check: avoid work if no marker in entire <p>
            const tc = p && (p.textContent || '');
            if (!tc || tc.indexOf('[!') === -1) continue;
            this._tryReplaceFullParagraph(p, rules, MD);
          }
        }
      } catch (e) {
        this._d('P_TOLERANT_SCAN_ERR', String(e));
      }

      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: (node) => {
          if (!node || !node.nodeValue || node.nodeValue.indexOf('[!') === -1) return NodeFilter.FILTER_SKIP;
          if (this.isInsideForbiddenContext(node)) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        }
      });

      let node;
      while ((node = walker.nextNode())) {
        const text = node.nodeValue;
        if (!text || text.indexOf('[!') === -1) continue;

        const parent = node.parentElement;

        // Entire text node equals one full match and parent is <p>.
        if (parent && parent.tagName === 'P' && parent.childNodes.length === 1) {
          const fm = this.findFullMatch(text, rules);
          if (fm && fm.rule.tag === 'p') {
            const out = document.createElement('p');
            if (fm.rule.className) out.className = fm.rule.className;
            out.setAttribute('data-cm', fm.rule.name);
            this.setInnerByMode(out, fm.rule.innerMode, fm.inner, MD);
            try { parent.replaceWith(out); } catch (_) {
              const par = parent.parentNode; if (par) par.replaceChild(out, parent);
            }
            this._d('WALKER_FULL_REPLACE', { rule: fm.rule.name, preview: this.logger.pv(text, 160) });
            continue;
          }
        }

        // General inline replacement inside the text node (span-like).
        let i = 0;
        let didReplace = false;
        const frag = document.createDocumentFragment();

        while (i < text.length) {
          const m = this.findNextMatch(text, i, rules);
          if (!m) break;

          if (m.start > i) {
            frag.appendChild(document.createTextNode(text.slice(i, m.start)));
          }

          const tag = (m.rule.tag === 'p') ? 'span' : m.rule.tag;
          const el = document.createElement(tag);
          if (m.rule.className) el.className = m.rule.className;
          el.setAttribute('data-cm', m.rule.name);
          this.setInnerByMode(el, m.rule.innerMode, m.inner, MD);

          frag.appendChild(el);
          this._d('WALKER_INLINE_MATCH', { rule: m.rule.name, start: m.start, end: m.end });
          i = m.end;
          didReplace = true;
        }

        if (!didReplace) continue;

        if (i < text.length) {
          frag.appendChild(document.createTextNode(text.slice(i)));
        }

        const parentNode = node.parentNode;
        if (parentNode) {
          parentNode.replaceChild(frag, node);
          this._d('WALKER_INLINE_DONE', { preview: this.logger.pv(text, 120) });
        }
      }
    }
  }

  // ==========================================================================
  // 5) Markdown runtime (markdown-it + code wrapper + math placeholders)
  // ==========================================================================

  class MarkdownRenderer {
    constructor(cfg, customMarkup, logger, asyncer, raf) {
      this.cfg = cfg; this.customMarkup = customMarkup; this.MD = null;
      this.logger = logger || new Logger(cfg);
      // Cooperative async utilities available in renderer for heavy decode/render paths
      this.asyncer = asyncer || new AsyncRunner(cfg, raf);
      this.raf = raf || null;

      // Fast-path streaming renderer without linkify to reduce regex work on hot path.
      this.MD_STREAM = null;

      this.hooks = {
        observeNewCode: () => {},
        observeMsgBoxes: () => {},
        scheduleMathRender: () => {},
        codeScrollInit: () => {}
      };
    }
    // Initialize markdown-it instances and plugins.
    init() {
      if (!window.markdownit) { this.logger.log('[MD] markdown-it not found – rendering skipped.'); return; }
      // Full renderer (used for non-hot paths, final results)
      this.MD = window.markdownit({ html: false, linkify: true, breaks: true, highlight: () => '' });
      // Streaming renderer (no linkify) – hot path
      this.MD_STREAM = window.markdownit({ html: false, linkify: false, breaks: true, highlight: () => '' });

      // SAFETY: disable CommonMark "indented code blocks" unless explicitly enabled.
      if (!this.cfg.MD || this.cfg.MD.ALLOW_INDENTED_CODE !== true) {
        try { this.MD.block.ruler.disable('code'); } catch (_) {}
        try { this.MD_STREAM.block.ruler.disable('code'); } catch (_) {}
      }

      const escapeHtml = Utils.escapeHtml;

      // Dollar and bracket math placeholder plugins: generate lightweight placeholders to be picked up by KaTeX later.
      const mathDollarPlaceholderPlugin = (md) => {
        function notEscaped(src, pos) { let back = 0; while (pos - back - 1 >= 0 && src.charCodeAt(pos - back - 1) === 0x5C) back++; return (back % 2) === 0; }
        function math_block_dollar(state, startLine, endLine, silent) {
          const pos = state.bMarks[startLine] + state.tShift[startLine];
          const max = state.eMarks[startLine];
          if (pos + 1 >= max) return false;
          if (state.src.charCodeAt(pos) !== 0x24 || state.src.charCodeAt(pos + 1) !== 0x24) return false;
          let nextLine = startLine + 1, found = false;
          for (; nextLine < endLine; nextLine++) {
            let p = state.bMarks[nextLine] + state.tShift[nextLine];
            const pe = state.eMarks[nextLine];
            if (p + 1 < pe && state.src.charCodeAt(p) === 0x24 && state.src.charCodeAt(p + 1) === 0x24) { found = true; break; }
          }
          if (!found) return false;
          if (silent) return true;

          const contentStart = state.bMarks[startLine] + state.tShift[startLine] + 2;
          const contentEndLine = nextLine - 1;
          let content = '';
          if (contentEndLine >= startLine + 1) {
            const startIdx = state.bMarks[startLine + 1];
            const endIdx = state.eMarks[contentEndLine];
            content = state.src.slice(startIdx, endIdx);
          } else content = '';

          const token = state.push('math_block_dollar', '', 0);
          token.block = true; token.content = content; state.line = nextLine + 1; return true;
        }
        function math_inline_dollar(state, silent) {
          const pos = state.pos, src = state.src, max = state.posMax;
          if (pos >= max) return false;
          if (src.charCodeAt(pos) !== 0x24) return false;
          if (pos + 1 < max && src.charCodeAt(pos + 1) === 0x24) return false;
          const after = pos + 1 < max ? src.charCodeAt(pos + 1) : 0;
          if (after === 0x20 || after === 0x0A || after === 0x0D) return false;
          let i = pos + 1;
          while (i < max) {
            const ch = src.charCodeAt(i);
            if (ch === 0x24 && notEscaped(src, i)) {
              const before = i - 1 >= 0 ? src.charCodeAt(i - 1) : 0;
              if (before === 0x20 || before === 0x0A || before === 0x0D) { i++; continue; }
              break;
            }
            i++;
          }
          if (i >= max || src.charCodeAt(i) !== 0x24) return false;

          if (!silent) {
            const token = state.push('math_inline_dollar', '', 0);
            token.block = false; token.content = src.slice(pos + 1, i);
          }
          state.pos = i + 1; return true;
        }

        md.block.ruler.before('fence', 'math_block_dollar', math_block_dollar, { alt: ['paragraph', 'reference', 'blockquote', 'list'] });
        md.inline.ruler.before('escape', 'math_inline_dollar', math_inline_dollar);

        md.renderer.rules.math_inline_dollar = (tokens, idx) => {
          const tex = tokens[idx].content || '';
          return `<span class="math-pending" data-display="0"><span class="math-fallback">$${escapeHtml(tex)}$</span><script type="math/tex">${escapeHtml(tex)}</script></span>`;
        };
        md.renderer.rules.math_block_dollar = (tokens, idx) => {
          const tex = tokens[idx].content || '';
          return `<div class="math-pending" data-display="1"><div class="math-fallback">$$${escapeHtml(tex)}$$</div><script type="math/tex; mode=display">${escapeHtml(tex)}</script></div>`;
        };
      };

      const mathBracketsPlaceholderPlugin = (md) => {
        function math_brackets(state, silent) {
          const src = state.src, pos = state.pos, max = state.posMax;
          if (pos + 1 >= max || src.charCodeAt(pos) !== 0x5C) return false;
          const next = src.charCodeAt(pos + 1);
          if (next !== 0x28 && next !== 0x5B) return false;
          const isInline = (next === 0x28); const close = isInline ? '\\)' : '\\]';
          const start = pos + 2; const end = src.indexOf(close, start);
          if (end < 0) return false;
          const content = src.slice(start, end);
          if (!silent) {
            const t = state.push(isInline ? 'math_inline_bracket' : 'math_block_bracket', '', 0);
            t.content = content; t.block = !isInline;
          }
          state.pos = end + 2; return true;
        }
        md.inline.ruler.before('escape', 'math_brackets', math_brackets);
        md.renderer.rules.math_inline_bracket = (tokens, idx) => {
          const tex = tokens[idx].content || '';
          return `<span class="math-pending" data-display="0"><span class="math-fallback">\\(${escapeHtml(tex)}\\)</span><script type="math/tex">${escapeHtml(tex)}</script></span>`;
        };
        md.renderer.rules.math_block_bracket = (tokens, idx) => {
          const tex = tokens[idx].content || '';
          return `<div class="math-pending" data-display="1"><div class="math-fallback">\\[${escapeHtml(tex)}\\]</div><script type="math/tex; mode=display">${escapeHtml(tex)}</script></div>`;
        };
      };

      this.MD.use(mathDollarPlaceholderPlugin);
      this.MD.use(mathBracketsPlaceholderPlugin);
      this.MD_STREAM.use(mathDollarPlaceholderPlugin);
      this.MD_STREAM.use(mathBracketsPlaceholderPlugin);

      const cfg = this.cfg; const logger = this.logger;
      (function codeWrapperPlugin(md, logger) {
        let CODE_IDX = 1;
        const log = (line, ctx) => logger.debug('MD_LANG', line, ctx);

        const DEDUP = (window.MD_LANG_LOG_DEDUP !== false);
        const seenFP = new Set();
        const makeFP = (info, raw) => {
          const head = (raw || '').slice(0, 96);
          return String(info || '') + '|' + String((raw || '').length) + '|' + head;
        };

        const ALIAS = {
          txt: 'plaintext', text: 'plaintext', plaintext: 'plaintext',
          sh: 'bash', shell: 'bash', zsh: 'bash', 'shell-session': 'bash',
          py: 'python', python3: 'python', py3: 'python',
          js: 'javascript', node: 'javascript', nodejs: 'javascript',
          ts: 'typescript', 'ts-node': 'typescript',
          yml: 'yaml', kt: 'kotlin', rs: 'rust',
          csharp: 'csharp', 'c#': 'csharp', 'c++': 'cpp',
          ps: 'powershell', ps1: 'powershell', pwsh: 'powershell', powershell7: 'powershell',
          docker: 'dockerfile'
        };
        function normLang(s) { if (!s) return ''; const v = String(s).trim().toLowerCase(); return ALIAS[v] || v; }
        function isSupportedByHLJS(lang) { try { return !!(window.hljs && hljs.getLanguage && hljs.getLanguage(lang)); } catch (_) { return false; } }
        function classForHighlight(lang) { if (!lang) return 'plaintext'; return isSupportedByHLJS(lang) ? lang : 'plaintext'; }
        function stripBOM(s) { return (s && s.charCodeAt(0) === 0xFEFF) ? s.slice(1) : s; }

        function detectFromFirstLine(raw, rid) {
          if (!raw) return { lang: '', content: raw, isOutput: false };
          const lines = raw.split(/\r?\n/);
          if (!lines.length) return { lang: '', content: raw, isOutput: false };
          let i = 0; while (i < lines.length && !lines[i].trim()) i++;
          if (i >= lines.length) { log(`#${rid} first-line: only whitespace`); return { lang: '', content: raw, isOutput: false }; }
          let first = stripBOM(lines[i]).trim();
          first = first.replace(/^\s*lang(?:uage)?\s*[:=]\s*/i, '').trim();
          let token = first.split(/\s+/)[0].replace(/:$/, '');
          if (!/^[A-Za-z][\w#+\-\.]{0,30}$/.test(token)) { log(`#${rid} first-line: no token match`, { first }); return { lang: '', content: raw, isOutput: false }; }
          let cand = normLang(token);
          if (cand === 'output') {
            const content = lines.slice(i + 1).join('\n');
            log(`#${rid} first-line: output header`);
            return { lang: 'python', headerLabel: 'output', content, isOutput: true };
          }
          const rest = lines.slice(i + 1).join('\n');
          if (!rest.trim()) { log(`#${rid} first-line: directive but no content after, ignore`, { cand }); return { lang: '', content: raw, isOutput: false }; }
          log(`#${rid} first-line: directive accepted`, { cand, restLen: rest.length, hljs: isSupportedByHLJS(cand) });
          return { lang: cand, headerLabel: cand, content: rest, isOutput: false };
        }

        md.renderer.rules.fence = (tokens, idx) => renderFence(tokens[idx]);
        md.renderer.rules.code_block = (tokens, idx) => renderFence({ info: '', content: tokens[idx].content || '' });

        function resolveLanguageAndContent(info, raw, rid) {
          const infoLangRaw = (info || '').trim().split(/\s+/)[0] || '';
          let cand = normLang(infoLangRaw);
          if (cand === 'output') {
            log(`#${rid} info: output header`);
            return { lang: 'python', headerLabel: 'output', content: raw, isOutput: true };
          }
          if (cand) {
            log(`#${rid} info: token`, { infoLangRaw, cand, hljs: isSupportedByHLJS(cand) });
            return { lang: cand, headerLabel: cand, content: raw, isOutput: false };
          }
          const det = detectFromFirstLine(raw, rid);
          if (det && (det.lang || det.isOutput)) return det;
          log(`#${rid} resolve: fallback`);
          return { lang: '', headerLabel: 'code', content: raw, isOutput: false };
        }

        function renderFence(token) {
          const raw = token.content || '';
          const rid = String(CODE_IDX + '');
          const fp = makeFP(token.info || '', raw);
          const canLog = !DEDUP || !seenFP.has(fp);
          if (canLog) log(`FENCE_ENTER #${rid}`, { info: (token.info || ''), rawHead: logger.pv(raw) });

          const res = resolveLanguageAndContent(token.info || '', raw, rid);
          const isOutput = !!res.isOutput;
          const headerLabel = isOutput ? 'output' : (res.headerLabel || (res.lang || 'code'));
          const langClass = isOutput ? 'python' : classForHighlight(res.lang);

          if (canLog) {
            log(`FENCE_RESOLVE #${rid}`, { headerLabel, langToken: (res.lang || ''), langClass, hljsSupported: isSupportedByHLJS(res.lang || ''), contentLen: (res.content || '').length });
            if (DEDUP) seenFP.add(fp);
          }

          // precompute code meta to avoid expensive .textContent on next phases
          const content = res.content || '';
          const len = content.length;
          const head = content.slice(0, 64);
          const tail = content.slice(-64);
          const headEsc = Utils.escapeHtml(head);
          const tailEsc = Utils.escapeHtml(tail);
          // Note: for full renderer we will also persist data-code-nl (see below).

          const inner = Utils.escapeHtml(content);
          const idxLocal = CODE_IDX++;

          let actions = '';
          if (langClass === 'html') {
            actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-preview"><img src="${cfg.ICONS.CODE_PREVIEW}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.PREVIEW)}</span></a>`;
          } else if (langClass === 'python' && headerLabel !== 'output') {
            actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-run"><img src="${cfg.ICONS.CODE_RUN}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.RUN)}</span></a>`;
          }
          actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-collapse"><img src="${cfg.ICONS.CODE_MENU}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.COLLAPSE)}</span></a>`;
          actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-copy"><img src="${cfg.ICONS.CODE_COPY}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.COPY)}</span></a>`;

          // attach precomputed meta (len/head/tail) on wrapper for downstream optimizations
          return (
            `<div class="code-wrapper highlight" data-index="${idxLocal}"` +
            ` data-code-lang="${Utils.escapeHtml(res.lang || '')}"` +
            ` data-code-len="${String(len)}" data-code-head="${headEsc}" data-code-tail="${tailEsc}"` + // meta (no nl here – only in full renderer)
            ` data-locale-collapse="${Utils.escapeHtml(cfg.LOCALE.COLLAPSE)}" data-locale-expand="${Utils.escapeHtml(cfg.LOCALE.EXPAND)}"` +
            ` data-locale-copy="${Utils.escapeHtml(cfg.LOCALE.COPY)}" data-locale-copied="${Utils.escapeHtml(cfg.LOCALE.COPIED)}" data-style="${Utils.escapeHtml(cfg.CODE_STYLE)}">` +
              `<p class="code-header-wrapper"><span><span class="code-header-lang">${Utils.escapeHtml(headerLabel)}   </span>${actions}</span></p>` +
              `<pre><code class="language-${Utils.escapeHtml(langClass)} hljs">${inner}</code></pre>` +
            `</div>`
          );
        }
      })(this.MD_STREAM, this.logger);

      // Apply wrapper plugin to full renderer with extra meta (includes number of lines).
      (function codeWrapperPlugin(md, logger) {
        // identical core logic – augmented with data-code-nl for full renderer
        let CODE_IDX = 1;
        const log = (line, ctx) => logger.debug('MD_LANG', line, ctx);

        const DEDUP = (window.MD_LANG_LOG_DEDUP !== false);
        const seenFP = new Set();
        const makeFP = (info, raw) => {
          const head = (raw || '').slice(0, 96);
          return String(info || '') + '|' + String((raw || '').length) + '|' + head;
        };

        const ALIAS = {
          txt: 'plaintext', text: 'plaintext', plaintext: 'plaintext',
          sh: 'bash', shell: 'bash', zsh: 'bash', 'shell-session': 'bash',
          py: 'python', python3: 'python', py3: 'python',
          js: 'javascript', node: 'javascript', nodejs: 'javascript',
          ts: 'typescript', 'ts-node': 'typescript',
          yml: 'yaml', kt: 'kotlin', rs: 'rust',
          csharp: 'csharp', 'c#': 'csharp', 'c++': 'cpp',
          ps: 'powershell', ps1: 'powershell', pwsh: 'powershell', powershell7: 'powershell',
          docker: 'dockerfile'
        };
        function normLang(s) { if (!s) return ''; const v = String(s).trim().toLowerCase(); return ALIAS[v] || v; }
        function isSupportedByHLJS(lang) { try { return !!(window.hljs && hljs.getLanguage && hljs.getLanguage(lang)); } catch (_) { return false; } }
        function classForHighlight(lang) { if (!lang) return 'plaintext'; return isSupportedByHLJS(lang) ? lang : 'plaintext'; }
        function stripBOM(s) { return (s && s.charCodeAt(0) === 0xFEFF) ? s.slice(1) : s; }

        function detectFromFirstLine(raw, rid) {
          if (!raw) return { lang: '', content: raw, isOutput: false };
          const lines = raw.split(/\r?\n/);
          if (!lines.length) return { lang: '', content: raw, isOutput: false };
          let i = 0; while (i < lines.length && !lines[i].trim()) i++;
          if (i >= lines.length) { log(`#${rid} first-line: only whitespace`); return { lang: '', content: raw, isOutput: false }; }
          let first = stripBOM(lines[i]).trim();
          first = first.replace(/^\s*lang(?:uage)?\s*[:=]\s*/i, '').trim();
          let token = first.split(/\s+/)[0].replace(/:$/, '');
          if (!/^[A-Za-z][\w#+\-\.]{0,30}$/.test(token)) { log(`#${rid} first-line: no token match`, { first }); return { lang: '', content: raw, isOutput: false }; }
          let cand = normLang(token);
          if (cand === 'output') {
            const content = lines.slice(i + 1).join('\n');
            log(`#${rid} first-line: output header`);
            return { lang: 'python', headerLabel: 'output', content, isOutput: true };
          }
          const rest = lines.slice(i + 1).join('\n');
          if (!rest.trim()) { log(`#${rid} first-line: directive but no content after, ignore`, { cand }); return { lang: '', content: raw, isOutput: false }; }
          log(`#${rid} first-line: directive accepted`, { cand, restLen: rest.length, hljs: isSupportedByHLJS(cand) });
          return { lang: cand, headerLabel: cand, content: rest, isOutput: false };
        }

        md.renderer.rules.fence = (tokens, idx) => renderFence(tokens[idx]);
        md.renderer.rules.code_block = (tokens, idx) => renderFence({ info: '', content: tokens[idx].content || '' });

        function resolveLanguageAndContent(info, raw, rid) {
          const infoLangRaw = (info || '').trim().split(/\s+/)[0] || '';
          let cand = normLang(infoLangRaw);
          if (cand === 'output') {
            log(`#${rid} info: output header`);
            return { lang: 'python', headerLabel: 'output', content: raw, isOutput: true };
          }
          if (cand) {
            log(`#${rid} info: token`, { infoLangRaw, cand, hljs: isSupportedByHLJS(cand) });
            return { lang: cand, headerLabel: cand, content: raw, isOutput: false };
          }
          const det = detectFromFirstLine(raw, rid);
          if (det && (det.lang || det.isOutput)) return det;
          log(`#${rid} resolve: fallback`);
          return { lang: '', headerLabel: 'code', content: raw, isOutput: false };
        }

        function renderFence(token) {
          const raw = token.content || '';
          const rid = String(CODE_IDX + '');
          const fp = makeFP(token.info || '', raw);
          const canLog = !DEDUP || !seenFP.has(fp);
          if (canLog) log(`FENCE_ENTER #${rid}`, { info: (token.info || ''), rawHead: logger.pv(raw) });

          const res = resolveLanguageAndContent(token.info || '', raw, rid);
          const isOutput = !!res.isOutput;
          const headerLabel = isOutput ? 'output' : (res.headerLabel || (res.lang || 'code'));
          const langClass = isOutput ? 'python' : classForHighlight(res.lang);

          if (canLog) {
            log(`FENCE_RESOLVE #${rid}`, { headerLabel, langToken: (res.lang || ''), langClass, hljsSupported: isSupportedByHLJS(res.lang || ''), contentLen: (res.content || '').length });
            if (DEDUP) seenFP.add(fp);
          }

          // precompute code meta
          const content = res.content || '';
          const len = content.length;
          const head = content.slice(0, 64);
          const tail = content.slice(-64);
          const headEsc = Utils.escapeHtml(head);
          const tailEsc = Utils.escapeHtml(tail);
          const nl = Utils.countNewlines(content);

          const inner = Utils.escapeHtml(content);
          const idxLocal = CODE_IDX++;

          let actions = '';
          if (langClass === 'html') {
            actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-preview"><img src="${cfg.ICONS.CODE_PREVIEW}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.PREVIEW)}</span></a>`;
          } else if (langClass === 'python' && headerLabel !== 'output') {
            actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-run"><img src="${cfg.ICONS.CODE_RUN}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.RUN)}</span></a>`;
          }
          actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-collapse"><img src="${cfg.ICONS.CODE_MENU}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.COLLAPSE)}</span></a>`;
          actions += `<a href="empty:${idxLocal}" class="code-header-action code-header-copy"><img src="${cfg.ICONS.CODE_COPY}" class="action-img" data-id="${idxLocal}"><span>${Utils.escapeHtml(cfg.LOCALE.COPY)}</span></a>`;

          return (
            `<div class="code-wrapper highlight" data-index="${idxLocal}"` +
            ` data-code-lang="${Utils.escapeHtml(res.lang || '')}"` +
            ` data-code-len="${String(len)}" data-code-head="${headEsc}" data-code-tail="${tailEsc}" data-code-nl="${String(nl)}"` + // include nl for full renderer
            ` data-locale-collapse="${Utils.escapeHtml(cfg.LOCALE.COLLAPSE)}" data-locale-expand="${Utils.escapeHtml(cfg.LOCALE.EXPAND)}"` +
            ` data-locale-copy="${Utils.escapeHtml(cfg.LOCALE.COPY)}" data-locale-copied="${Utils.escapeHtml(cfg.LOCALE.COPIED)}" data-style="${Utils.escapeHtml(cfg.CODE_STYLE)}">` +
              `<p class="code-header-wrapper"><span><span class="code-header-lang">${Utils.escapeHtml(headerLabel)}   </span>${actions}</span></p>` +
              `<pre><code class="language-${Utils.escapeHtml(langClass)} hljs">${inner}</code></pre>` +
            `</div>`
          );
        }
      })(this.MD, this.logger);
    }
    // Replace "sandbox:" links with file:// in markdown source (host policy).
    preprocessMD(s) { return (s || '').replace(/\]\(sandbox:/g, '](file://'); }
    // Decode base64 UTF-8 to string (shared TextDecoder).
    b64ToUtf8(b64) {
      const bin = atob(b64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return Utils.utf8Decode(bytes);
    }

    // Apply custom markup for bot messages only (method name kept for API).
    applyCustomMarkupForBots(root) {
      const MD = this.MD;
      try {
        const scope = root || document;
        const targets = [];

        // If scope itself is a bot message box
        if (scope && scope.nodeType === 1 && scope.classList && scope.classList.contains('msg-box') &&
            scope.classList.contains('msg-bot')) {
          targets.push(scope);
        }

        // Collect bot message boxes within the scope
        if (scope && typeof scope.querySelectorAll === 'function') {
          const list = scope.querySelectorAll('.msg-box.msg-bot');
          for (let i = 0; i < list.length; i++) targets.push(list[i]);
        }

        // If scope is inside a bot message, include the closest ancestor as well
        if (scope && scope.nodeType === 1 && typeof scope.closest === 'function') {
          const closestMsg = scope.closest('.msg-box.msg-bot');
          if (closestMsg) targets.push(closestMsg);
        }

        // Deduplicate and apply rules only to bot messages
        const seen = new Set();
        for (const el of targets) {
          if (!el || !el.isConnected || seen.has(el)) continue;
          seen.add(el);
          this.customMarkup.apply(el, MD);
        }
      } catch (_) {
        // Keep render path resilient
      }
    }

    // Helper: choose renderer (hot vs full) for snapshot use.
    _md(streamingHint) {
      return streamingHint ? (this.MD_STREAM || this.MD) : (this.MD || this.MD_STREAM);
    }

    // Async, batched processing of [data-md64] / [md-block-markdown] to keep UI responsive on heavy loads.
    // Note: user messages are rendered as plain text (no markdown-it, no custom markup, no KaTeX).
    async renderPendingMarkdown(root) {
      const MD = this.MD; if (!MD) return;
      const scope = root || document;

      // Collect both legacy base64 holders and new native Markdown holders
      const nodes = Array.from(scope.querySelectorAll('[data-md64], [md-block-markdown]'));
      if (nodes.length === 0) {
        // Nothing to materialize right now. Avoid arming rAF work unless there is
        // actually something present that needs highlight/scroll/math.
        try {
          const hasBots = !!(scope && scope.querySelector && scope.querySelector('.msg-box.msg-bot'));
          const hasWrappers = !!(scope && scope.querySelector && scope.querySelector('.code-wrapper'));
          const hasCodes = !!(scope && scope.querySelector && scope.querySelector('.msg-box.msg-bot pre code'));
          const hasUnhighlighted = !!(scope && scope.querySelector && scope.querySelector('.msg-box.msg-bot pre code:not([data-highlighted="yes"])'));
          const hasMath = !!(scope && scope.querySelector && scope.querySelector('script[type^="math/tex"]'));

          // Apply Custom Markup only if bot messages are present.
          if (hasBots) { this.applyCustomMarkupForBots(scope); }

          // Restore collapsed state only if we can actually find wrappers.
          if (hasWrappers) { this.restoreCollapsedCode(scope); }

          // Initialize code scroll helpers for current root.
          this.hooks.codeScrollInit(scope);

          // Init code-scroll/highlight observers only when there are codes in DOM.
          if (hasCodes) {
            this.hooks.observeMsgBoxes(scope);
            this.hooks.observeNewCode(scope, {
              deferLastIfStreaming: true,
              minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
              minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
            });
            if (hasUnhighlighted && typeof runtime !== 'undefined' && runtime.highlighter) {
              runtime.highlighter.scanVisibleCodesInRoot(scope, runtime.stream.activeCode || null);
            }
          }

          // Schedule KaTeX render only if there are math scripts present.
          if (hasMath) { this.hooks.scheduleMathRender(scope); }
          this.hooks.codeScrollInit(scope);

        } catch (_) { /* swallow: keep idle path safe */ }

        return;
      }

      // Track which bot message boxes actually changed to avoid a heavy global Custom Markup pass.
      const touchedBoxes = new Set();

      // Budgeted, cooperative loop: process nodes one-by-one with per-frame yield when needed.
      const perSlice = (this.cfg.ASYNC && this.cfg.ASYNC.MD_NODES_PER_SLICE) || 12; // upper bound per frame
      let sliceCount = 0;
      let startedAt = Utils.now();

      for (let j = 0; j < nodes.length; j++) {
        const el = nodes[j];
        if (!el || !el.isConnected) continue;

        let md = '';
        const isNative = el.hasAttribute('md-block-markdown');
        const msgBox = (el.closest && el.closest('.msg-box.msg-bot, .msg-box.msg-user')) || null;
        const isUserMsg = !!(msgBox && msgBox.classList.contains('msg-user'));
        const isBotMsg = !!(msgBox && msgBox.classList.contains('msg-bot'));

        // Read source text (do not preprocess for user messages to keep it raw)
        if (isNative) {
          try { md = isUserMsg ? (el.textContent || '') : this.preprocessMD(el.textContent || ''); } catch (_) { md = ''; }
          try { el.removeAttribute('md-block-markdown'); } catch (_) {}
        } else {
          const b64 = el.getAttribute('data-md64'); if (!b64) continue;
          try { md = this.b64ToUtf8(b64); } catch (_) { md = ''; }
          el.removeAttribute('data-md64');
          if (!isUserMsg) { try { md = this.preprocessMD(md); } catch (_) {} }
        }

        if (isUserMsg) {
          // User message: replace placeholder with raw plain text only.
          const span = document.createElement('span');
          span.textContent = md;
          el.replaceWith(span);
          // Intentionally do NOT add to touchedBoxes; no Custom Markup for user.
        } else if (isBotMsg) {
          // Bot message: full markdown-it render with Custom Markup.
          let html = '';
          try { html = MD.render(md); } catch (_) { html = Utils.escapeHtml(md); }

          // build fragment directly (avoid intermediate container allocations).
          let frag = null;
          try {
            const range = document.createRange();
            const ctx = el.parentNode || document.body || document.documentElement;
            range.selectNode(ctx);
            frag = range.createContextualFragment(html);
          } catch (_) {
            const tmp = document.createElement('div');
            tmp.innerHTML = html;
            frag = document.createDocumentFragment();
            while (tmp.firstChild) frag.appendChild(tmp.firstChild);
          }

          // Apply Custom Markup on a lightweight DocumentFragment
          try { this.customMarkup.apply(frag, MD); } catch (_) {}

          el.replaceWith(frag);
          touchedBoxes.add(msgBox);
        } else {
          // Outside of any message box: materialize as plain text.
          const span = document.createElement('span');
          span.textContent = md;
          el.replaceWith(span);
        }

        sliceCount++;
        // Yield by time budget or by count to keep frame short and reactive.
        if (sliceCount >= perSlice || this.asyncer.shouldYield(startedAt)) {
          await this.asyncer.yield();
          startedAt = Utils.now();
          sliceCount = 0;
        }
      }

      // Apply Custom Markup only to actually modified BOT messages (keeps this pass light).
      try {
        touchedBoxes.forEach(box => { try { this.customMarkup.apply(box, MD); } catch (_) {} });
      } catch (_) {}

      // Same post-processing as before (idempotent with external calls).
      this.restoreCollapsedCode(scope);
      this.hooks.observeNewCode(scope, {
        deferLastIfStreaming: true,
        minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
        minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
      });
      this.hooks.observeMsgBoxes(scope);
      this.hooks.scheduleMathRender(scope);
      this.hooks.codeScrollInit(scope);

      if (typeof runtime !== 'undefined' && runtime.highlighter) {
       runtime.highlighter.scanVisibleCodesInRoot(scope, runtime.stream.activeCode || null);
      }
    }

    // Render streaming snapshot (reduced features).
    renderStreamingSnapshot(src) {
      const md = this._md(true);
      if (!md) return '';
      try { return md.render(src); } catch (_) { return Utils.escapeHtml(src); }
    }
    // Render final snapshot (full features).
    renderFinalSnapshot(src) {
      const md = this._md(false);
      if (!md) return '';
      try { return md.render(src); } catch (_) { return Utils.escapeHtml(src); }
    }

    // Restore collapse/expand state of code blocks after DOM updates.
    restoreCollapsedCode(root) {
      const scope = root || document;
      const wrappers = scope.querySelectorAll('.code-wrapper');
      wrappers.forEach((wrapper) => {
        const index = wrapper.getAttribute('data-index');
        const localeCollapse = wrapper.getAttribute('data-locale-collapse');
        const localeExpand = wrapper.getAttribute('data-locale-expand');
        const source = wrapper.querySelector('code');
        const isCollapsed = (window.__collapsed_idx || []).includes(index);
        if (!source) return;
        const btn = wrapper.querySelector('.code-header-collapse');
        if (isCollapsed) {
          source.style.display = 'none';
          if (btn) { const span = btn.querySelector('span'); if (span) span.textContent = localeExpand; }
        } else {
          source.style.display = 'block';
          if (btn) { const span = btn.querySelector('span'); if (span) span.textContent = localeCollapse; }
        }
      });
    }
  }
  window.__collapsed_idx = window.__collapsed_idx || [];

  // ==========================================================================
  // 6) Math renderer (async, chunked)
  // ==========================================================================
  class MathRenderer {
    constructor(cfg, raf, asyncer) {
      this.cfg = cfg; this.raf = raf; this.asyncer = asyncer;
      this.scheduled = false;

      // rAF key used by the central pump (do not change – API compatibility).
      this.rafKey = { t: 'Math:render' };

      // Pending roots aggregation: if document-level render is requested, it supersedes others.
      this._pendingRoots = new Set();
      this._pendingDoc = false;
    }

    // Async, cooperative KaTeX rendering to avoid long blocking on many formulas.
    async renderAsync(root) {
      if (typeof katex === 'undefined') return;
      const scope = root || document;
      const scripts = Array.from(scope.querySelectorAll('script[type^="math/tex"]'));
      const useToString = (typeof katex.renderToString === 'function');

      const batchFn = async (script) => {
        if (!script || !script.isConnected) return;
        // Only render math in bot messages
        if (!script.closest('.msg-box.msg-bot')) return;
        const t = script.getAttribute('type') || '';
        const displayMode = t.indexOf('mode=display') > -1;
        // avoid innerText (it may trigger layout). textContent is sufficient here.
        const mathContent = script.textContent || '';
        const parent = script.parentNode; if (!parent) return;

        try {
          if (useToString) {
            let html = '';
            try {
              html = katex.renderToString(mathContent, { displayMode, throwOnError: false });
            } catch (_) {
              const fb = displayMode ? `\\[${mathContent}\\]` : `\\(${mathContent}\\)`;
              html = (displayMode ? `<div>${Utils.escapeHtml(fb)}</div>` : `<span>${Utils.escapeHtml(fb)}</span>`);
            }
            const host = document.createElement(displayMode ? 'div' : 'span');
            host.innerHTML = html;
            const el = host.firstElementChild || host;
            if (parent.classList && parent.classList.contains('math-pending')) parent.replaceWith(el);
            else parent.replaceChild(el, script);
          } else {
            const el = document.createElement(displayMode ? 'div' : 'span');
            try { katex.render(mathContent, el, { displayMode, throwOnError: false }); }
            catch (_) { el.textContent = (displayMode ? `\\[${mathContent}\\]` : `\\(${mathContent}\\)`); }
            if (parent.classList && parent.classList.contains('math-pending')) parent.replaceWith(el);
            else parent.replaceChild(el, script);
          }
        } catch (_) {
          // Keep fallback text intact on any error
        }
      };

      // Process formulas cooperatively (rAF yields).
      await this.asyncer.forEachChunk(scripts, batchFn, 'MathRenderer');
    }

    // Schedule math rendering for a root. Coalesces multiple calls.
    schedule(root, _delayIgnored = 0, forceNow = false) {
      // If KaTeX is not available, honor no-op. API stays intact.
      if (typeof katex === 'undefined') return;

      // Normalize root (default to whole document).
      const targetRoot = root || document;

      // Fast existence check to avoid arming rAF when nothing to do, but still
      // keep aggregation semantics: if a job is already scheduled we can still
      // merge new roots into the pending set when they actually contain math.
      let hasMath = true;
      if (!forceNow) {
        try {
          hasMath = !!(targetRoot && targetRoot.querySelector && targetRoot.querySelector('script[type^="math/tex"]'));
        } catch (_) { hasMath = false; }
        if (!hasMath) return; // nothing to render for this root; safe early exit
      }

      // Aggregate roots so nothing is lost while one job is already scheduled.
      if (targetRoot === document || targetRoot === document.documentElement || targetRoot === document.body) {
        this._pendingDoc = true;                 // promote to a full-document sweep
        this._pendingRoots.clear();              // small optimization (document covers all)
      } else if (!this._pendingDoc) {
        this._pendingRoots.add(targetRoot);
      }

      // If a task is already scheduled, do not arm another – coalescing will take care of it.
      if (this.scheduled && this.raf && typeof this.raf.isScheduled === 'function' && this.raf.isScheduled(this.rafKey)) return;

      this.scheduled = true;
      const priority = forceNow ? 0 : 2;

      // Single rAF job drains all pending roots; renderAsync remains public and unchanged.
      this.raf.schedule(this.rafKey, () => {
        this.scheduled = false;

        const useDoc = this._pendingDoc;
        const roots = [];

        if (useDoc) {
          roots.push(document);
        } else {
          this._pendingRoots.forEach((r) => {
            // Only keep connected elements to avoid useless work.
            try {
              if (r && (r.isConnected === undefined || r.isConnected)) roots.push(r);
            } catch (_) {
              // Conservative: keep the root; renderAsync guards internally.
              roots.push(r);
            }
          });
        }

        // Reset aggregation state before running (new calls can aggregate afresh).
        this._pendingDoc = false;
        this._pendingRoots.clear();

        // Fire-and-forget async drain; keep renderAsync API intact.
        (async () => {
          for (let i = 0; i < roots.length; i++) {
            try { await this.renderAsync(roots[i]); } catch (_) { /* swallow – resilient */ }
          }
        })();
      }, 'Math', priority);
    }
    // Cleanup pending work and state.
    cleanup() {
      try { this.raf.cancelGroup('Math'); } catch (_) {}
      this.scheduled = false;

      // Ensure pending state is fully cleared on cleanup.
      try { this._pendingRoots.clear(); } catch (_) {}
      this._pendingDoc = false;
    }
  }

  // ==========================================================================
  // 7) Scroll manager + FAB
  // ==========================================================================

  class ScrollManager {
    constructor(cfg, dom, raf) {
      this.cfg = cfg; this.dom = dom; this.raf = raf;
      this.autoFollow = true; this.userInteracted = false;
      this.lastScrollTop = 0; this.prevScroll = 0;
      this.currentFabAction = 'none'; this.fabFreezeUntil = 0;
      this.scrollScheduled = false; this.scrollFabUpdateScheduled = false;
      this.scrollRAF = 0; this.scrollFabRAF = 0;
    }
    // Is page near the bottom by given margin?
    isNearBottom(marginPx = 100) {
      const el = Utils.SE; const distance = el.scrollHeight - el.clientHeight - el.scrollTop;
      return distance <= marginPx;
    }
    // Schedule a page scroll to bottom if auto-follow allows it.
    scheduleScroll(live = false) {
      if (live === true && this.autoFollow !== true) return;
      if (this.scrollScheduled) return;
      this.scrollScheduled = true;
      this.raf.schedule('SM:scroll', () => { this.scrollScheduled = false; this.scrollToBottom(live); this.scheduleScrollFabUpdate(); }, 'ScrollManager', 1);
    }
    // Cancel any pending page scroll.
    cancelPendingScroll() {
      try { this.raf.cancelGroup('ScrollManager'); } catch (_) {}
      this.scrollScheduled = false;
      this.scrollFabUpdateScheduled = false;
      this.scrollRAF = 0; this.scrollFabRAF = 0;
    }
    // Jump to bottom immediately (no smooth behavior).
    forceScrollToBottomImmediate() {
      const el = Utils.SE; el.scrollTop = el.scrollHeight; this.prevScroll = el.scrollHeight;
    }
    // Scroll window to bottom based on auto-follow and margins.
    scrollToBottom(live = false, force = false) {
      const el = Utils.SE; const marginPx = this.cfg.UI.SCROLL_NEAR_MARGIN_PX; const behavior = 'instant';
      if (live === true && this.autoFollow !== true) { this.prevScroll = el.scrollHeight; return; }
      if ((live === true && this.userInteracted === false) || this.isNearBottom(marginPx) || live === false || force) {
        try { el.scrollTo({ top: el.scrollHeight, behavior }); } catch (_) { el.scrollTop = el.scrollHeight; }
      }
      this.prevScroll = el.scrollHeight;
    }
    // Check if window has vertical scroll bar.
    hasVerticalScroll() { const el = Utils.SE; return (el.scrollHeight - el.clientHeight) > 1; }
    // Compute the current FAB action (none/up/down).
    computeFabAction() {
      const el = Utils.SE; const hasScroll = (el.scrollHeight - el.clientHeight) > 1;
      if (!hasScroll) return 'none';
      const dist = el.scrollHeight - el.clientHeight - el.scrollTop;
      if (dist <= 2) return 'up';
      if (dist >= this.cfg.FAB.SHOW_DOWN_THRESHOLD_PX) return 'down';
      return 'none';
    }
    // Update FAB to show correct direction and label.
    updateScrollFab(force = false, actionOverride = null, bypassFreeze = false) {
      const btn = this.dom.get('scrollFab'); const icon = this.dom.get('scrollFabIcon');
      if (!btn || !icon) return;
      const now = Utils.now(); const action = actionOverride || this.computeFabAction();
      if (!force && !bypassFreeze && now < this.fabFreezeUntil && action !== this.currentFabAction) return;
      if (action === 'none') {
        if (this.currentFabAction !== 'none' || force) { btn.classList.remove('visible'); this.currentFabAction = 'none'; }
        return;
      }
      if (action !== this.currentFabAction || force) {
        if (action === 'up') {
          if (icon.dataset.dir !== 'up') { icon.src = this.cfg.ICONS.COLLAPSE; icon.dataset.dir = 'up'; }
          btn.title = "Go to top";
        } else {
          if (icon.dataset.dir !== 'down') { icon.src = this.cfg.ICONS.EXPAND; icon.dataset.dir = 'down'; }
          btn.title = "Go to bottom";
        }
        btn.setAttribute('aria-label', btn.title);
        this.currentFabAction = action; btn.classList.add('visible');
      } else if (!btn.classList.contains('visible')) btn.classList.add('visible');
    }
    // Schedule a FAB state refresh.
    scheduleScrollFabUpdate() {
      if (this.scrollFabUpdateScheduled) return;
      this.scrollFabUpdateScheduled = true;
      this.raf.schedule('SM:fab', () => {
        this.scrollFabUpdateScheduled = false;
        const action = this.computeFabAction(); if (action !== this.currentFabAction) this.updateScrollFab(false, action);
      }, 'ScrollManager', 2);
    }
    // If user is near bottom, enable auto-follow again.
    maybeEnableAutoFollowByProximity() {
      const el = Utils.SE;
      if (!this.autoFollow) {
        const dist = el.scrollHeight - el.clientHeight - el.scrollTop;
        if (dist <= this.cfg.UI.AUTO_FOLLOW_REENABLE_PX) this.autoFollow = true;
      }
    }
    // User-triggered scroll to top; disables auto-follow.
    scrollToTopUser() {
      this.userInteracted = true; this.autoFollow = false;
      try { const el = Utils.SE; el.scrollTo({ top: 0, behavior: 'instant' }); this.lastScrollTop = el.scrollTop; }
      catch (_) { const el = Utils.SE; el.scrollTop = 0; this.lastScrollTop = 0; }
    }
    // User-triggered scroll to bottom; may re-enable auto-follow if near bottom.
    scrollToBottomUser() {
      this.userInteracted = true; this.autoFollow = false;
      try { const el = Utils.SE; el.scrollTo({ top: el.scrollHeight, behavior: 'instant' }); this.lastScrollTop = el.scrollTop; }
      catch (_) { const el = Utils.SE; el.scrollTop = el.scrollHeight; this.lastScrollTop = el.scrollTop; }
      this.maybeEnableAutoFollowByProximity();
    }
  }

  // ==========================================================================
  // 8) Tips manager
  // ==========================================================================

  // Tips manager (drop-in replacement): rotates small hint messages in a top overlay.
  class TipsManager {
    // Lightweight tips rotator that works with your CSS (.tips/.visible)
    // and is backward-compatible with legacy `let tips = [...]` injection.
    constructor(dom) {
      this.dom = dom;
      this.hidden = false;
      this._timers = [];
      this._running = false;
      this._idx = 0;
    }

    // Resolve tips list from multiple legacy/new sources.
    _getList() {
      // New preferred: window.TIPS (array)
      const upper = (typeof window !== 'undefined') ? window.TIPS : undefined;
      if (Array.isArray(upper) && upper.length) return upper;

      // Legacy inline: window.tips (array or JSON string)
      const lower = (typeof window !== 'undefined') ? window.tips : undefined;
      if (Array.isArray(lower) && lower.length) return lower;
      if (typeof lower === 'string' && lower.trim().length) {
        try { const arr = JSON.parse(lower); if (Array.isArray(arr)) return arr; } catch (_) {}
      }

      // Optional: data-tips='["...","..."]' on #tips
      const host = this._host();
      if (host && host.dataset && typeof host.dataset.tips === 'string') {
        try { const arr = JSON.parse(host.dataset.tips); if (Array.isArray(arr)) return arr; } catch (_) {}
      }

      return [];
    }

    _host() {
      return this.dom.get('tips') || document.getElementById('tips');
    }

    _clearTimers() {
      for (const t of this._timers) { try { clearTimeout(t); } catch (_) {} }
      this._timers.length = 0;
    }

    // Stop any running rotation timers.
    stopTimers() {
      this._clearTimers();
      this._running = false;
    }

    _applyBaseStyle(el) {
      if (!el) return;
      // Keep your flex layout and sizing; do not overwrite width/height.
      // Ensure it renders above other layers.
      const z = (typeof window !== 'undefined' && typeof window.TIPS_ZINDEX !== 'undefined')
        ? String(window.TIPS_ZINDEX) : '2147483000';
      el.style.zIndex = z;
    }

    // Hide tips layer and stop rotation.
    hide() {
      if (this.hidden) return;
      this.stopTimers();
      const el = this._host();
      if (el) {
        // Remove visibility class and hide hard (used when stream starts etc.)
        el.classList.remove('visible');
        el.classList.remove('hidden'); // in case it was set elsewhere
        el.style.display = 'none';
      }
      this.hidden = true;
    }

    // Show tips layer (does not start rotation).
    show() {
      const list = this._getList(); if (!list.length) return;
      const el = this._host(); if (!el) return;

      this.hidden = false;
      this._applyBaseStyle(el);
      el.classList.remove('hidden');
      el.style.display = 'block'; // CSS handles opacity via .tips/.visible
      // Do not add 'visible' yet – cycle() takes care of fade-in steps.
    }

    // Show one tip (by index) and fade it in next frame.
    _showOne(idx) {
      const list = this._getList(); if (!list.length) return;
      const el = this._host(); if (!el || this.hidden) return;

      this._applyBaseStyle(el);
      el.innerHTML = list[idx % list.length];

      // Centralize "next-frame" visibility toggle through RafManager to guarantee CSS transition.
      try {
        if (typeof runtime !== 'undefined' && runtime.raf && typeof runtime.raf.schedule === 'function') {
          const key = { t: 'Tips:show', el, i: Math.random() };
          runtime.raf.schedule(key, () => {
            if (this.hidden || !el.isConnected) return;
            el.classList.add('visible');
          }, 'Tips', 2);
        } else {
          // Fallback: no frame delay – still functional, transition may not play.
          el.classList.add('visible');
        }
      } catch (_) {
        el.classList.add('visible');
      }
    }

    // Internal loop: show, wait, hide, wait fade, next.
    _cycleLoop() {
      if (this.hidden) return;
      const el = this._host(); if (!el) return;

      const VISIBLE_MS = (typeof window !== 'undefined' && window.TIPS_VISIBLE_MS) ? window.TIPS_VISIBLE_MS : 15000;
      const FADE_MS    = (typeof window !== 'undefined' && window.TIPS_FADE_MS) ? window.TIPS_FADE_MS : 1000;

      this._showOne(this._idx);

      // Sequence: visible -> wait -> remove 'visible' -> wait fade -> next
      this._timers.push(setTimeout(() => {
        if (this.hidden) return;
        el.classList.remove('visible');
        this._timers.push(setTimeout(() => {
          if (this.hidden) return;
          const list = this._getList(); if (!list.length) return;
          this._idx = (this._idx + 1) % list.length;
          this._cycleLoop();
        }, FADE_MS));
      }, VISIBLE_MS));
    }

    // Start rotation with initial delay.
    cycle() {
      const list = this._getList(); if (!list.length || this._running) return;
      this._running = true; this._idx = 0;
      this.show(); // make sure the host is visible and centered

      const INIT_DELAY = (typeof window !== 'undefined' && window.TIPS_INIT_DELAY_MS) ? window.TIPS_INIT_DELAY_MS : 10000;
      this._timers.push(setTimeout(() => {
        if (this.hidden) return;
        this._cycleLoop();
      }, Math.max(0, INIT_DELAY)));
    }

    // Stop and reset.
    cleanup() {
      this.stopTimers();
      const el = this._host();
      if (el) el.classList.remove('visible');
    }
  }

  // ==========================================================================
  // 9) Tool output + Nodes manager
  // ==========================================================================

  class ToolOutput {
    // Placeholder for loader show (can be extended by host).
    showLoader() { return; }
    // Hide spinner elements in bot messages.
    hideLoader() {
      const elements = document.querySelectorAll('.msg-bot');
      if (elements.length > 0) elements.forEach(el => { const s = el.querySelector('.spinner'); if (s) s.style.display = 'none'; });
    }
    begin() { this.showLoader(); }
    end() { this.hideLoader(); }
    enable() { const els = document.querySelectorAll('.tool-output'); if (els.length) els[els.length - 1].style.display = 'block'; }
    disable() { const els = document.querySelectorAll('.tool-output'); if (els.length) els[els.length - 1].style.display = 'none'; }
    // Append HTML into the latest tool-output content area.
    append(content) {
      this.hideLoader(); this.enable();
      const els = document.querySelectorAll('.tool-output');
      if (els.length) { const contentEl = els[els.length - 1].querySelector('.content'); if (contentEl) contentEl.insertAdjacentHTML('beforeend', content); }
    }
    // Replace inner HTML for the latest tool-output content area.
    update(content) {
      this.hideLoader(); this.enable();
      const els = document.querySelectorAll('.tool-output');
      if (els.length) { const contentEl = els[els.length - 1].querySelector('.content'); if (contentEl) contentEl.innerHTML = content; }
    }
    // Remove children from the latest tool-output content area.
    clear() {
      this.hideLoader(); this.enable();
      const els = document.querySelectorAll('.tool-output');
      if (els.length) { const contentEl = els[els.length - 1].querySelector('.content'); if (contentEl) contentEl.replaceChildren(); }
    }
    // Toggle visibility of a specific tool output block by message id.
    toggle(id) {
      const el = document.getElementById('msg-bot-' + id); if (!el) return;
      const outputEl = el.querySelector('.tool-output'); if (!outputEl) return;
      const contentEl = outputEl.querySelector('.content');
      if (contentEl) contentEl.style.display = (contentEl.style.display === 'none') ? 'block' : 'none';
      const toggleEl = outputEl.querySelector('.toggle-cmd-output img'); if (toggleEl) toggleEl.classList.toggle('toggle-expanded');
    }
  }

  class NodesManager {
    constructor(dom, renderer, highlighter, math) { this.dom = dom; this.renderer = renderer; this.highlighter = highlighter; this.math = math; }
    // Check if HTML contains only user messages without any markdown or code features.
    _isUserOnlyContent(html) {
      try {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        const hasBot = !!tmp.querySelector('.msg-box.msg-bot');
        const hasUser = !!tmp.querySelector('.msg-box.msg-user');
        const hasMD64 = !!tmp.querySelector('[data-md64]');
        const hasMDNative = !!tmp.querySelector('[md-block-markdown]');
        const hasCode = !!tmp.querySelector('pre code');
        const hasMath = !!tmp.querySelector('script[type^="math/tex"]');
        return hasUser && !hasBot && !hasMD64 && !hasMDNative && !hasCode && !hasMath;
      } catch (_) { return false; }
    }
    // Convert user markdown placeholders into plain text nodes.
    _materializeUserMdAsPlainText(scopeEl) {
      try {
        const nodes = scopeEl.querySelectorAll('.msg-box.msg-user [data-md64], .msg-box.msg-user [md-block-markdown]');
        nodes.forEach(el => {
          let txt = '';
          if (el.hasAttribute('data-md64')) {
            const b64 = el.getAttribute('data-md64') || '';
            el.removeAttribute('data-md64');
            try { txt = this.renderer.b64ToUtf8(b64); } catch (_) { txt = ''; }
          } else {
            // Native Markdown block in user message: keep as plain text (no markdown-it)
            try { txt = el.textContent || ''; } catch (_) { txt = ''; }
            try { el.removeAttribute('md-block-markdown'); } catch (_) {}
          }
          const span = document.createElement('span'); span.textContent = txt; el.replaceWith(span);
        });
      } catch (_) {}
    }
    // Append HTML into message input container.
    appendToInput(content) {
      // Synchronous DOM update – message input must reflect immediately with no waiting.
      const el = this.dom.get('_append_input_'); if (!el) return; el.insertAdjacentHTML('beforeend', content);
    }
    // Append nodes into messages list and perform post-processing (markdown, code, math).
    appendNode(content, scrollMgr) {
      // Keep scroll behavior consistent with existing logic
      scrollMgr.userInteracted = false; scrollMgr.prevScroll = 0;
      this.dom.clearStreamBefore();

      const el = this.dom.get('_nodes_'); if (!el) return;
      el.classList.remove('empty_list');

      const userOnly = this._isUserOnlyContent(content);
      if (userOnly) {
        el.insertAdjacentHTML('beforeend', content);
        this._materializeUserMdAsPlainText(el);
        scrollMgr.scrollToBottom(false);
        scrollMgr.scheduleScrollFabUpdate();
        return;
      }

      el.insertAdjacentHTML('beforeend', content);

      try {
        // Schedule all post-processing strictly after Markdown is materialized.
        const maybePromise = this.renderer.renderPendingMarkdown(el);
        const post = () => {
          try { this.highlighter.scheduleScanVisibleCodes(null); } catch (_) {}

          // In finalize-only mode we must explicitly schedule KaTeX,
          // and do it AFTER Markdown has produced <script type="math/tex"> nodes.
          try { if (getMathMode() === 'finalize-only') this.math.schedule(el, 0, true); } catch (_) {}
        };

        if (maybePromise && typeof maybePromise.then === 'function') {
          maybePromise.then(post);
        } else {
          post();
        }
      } catch (_) { /* swallow to keep append path resilient */ }

      // Keep scroll/fab logic identical (immediate; rendering completes shortly after)
      scrollMgr.scrollToBottom(false);
      scrollMgr.scheduleScrollFabUpdate();
    }
    // Replace messages list content entirely and re-run post-processing.
    replaceNodes(content, scrollMgr) {
      // Same semantics as appendNode, but using a hard clone reset
      scrollMgr.userInteracted = false; scrollMgr.prevScroll = 0;
      this.dom.clearStreamBefore();

      const el = this.dom.hardReplaceByClone('_nodes_'); if (!el) return;
      el.classList.remove('empty_list');

      const userOnly = this._isUserOnlyContent(content);
      if (userOnly) {
        el.insertAdjacentHTML('beforeend', content);
        this._materializeUserMdAsPlainText(el);
        scrollMgr.scrollToBottom(false, true);
        scrollMgr.scheduleScrollFabUpdate();
        return;
      }

      el.insertAdjacentHTML('beforeend', content);

      try {
        // Defer KaTeX schedule to post-Markdown to avoid races.
        const maybePromise = this.renderer.renderPendingMarkdown(el);
        const post = () => {
          try { this.highlighter.scheduleScanVisibleCodes(null); } catch (_) {}
          try { if (getMathMode() === 'finalize-only') this.math.schedule(el, 0, true); } catch (_) {}
        };

        if (maybePromise && typeof maybePromise.then === 'function') {
          maybePromise.then(post);
        } else {
          post();
        }
      } catch (_) { /* swallow */ }

      scrollMgr.scrollToBottom(false, true);
      scrollMgr.scheduleScrollFabUpdate();
    }
    // Append "extra" content into a specific bot message and post-process locally.
    appendExtra(id, content, scrollMgr) {
      const el = document.getElementById('msg-bot-' + id); if (!el) return;
      const extra = el.querySelector('.msg-extra'); if (!extra) return;

      extra.insertAdjacentHTML('beforeend', content);

      try {
        const maybePromise = this.renderer.renderPendingMarkdown(extra);

        const post = () => {
          const activeCode = (typeof runtime !== 'undefined' && runtime.stream) ? runtime.stream.activeCode : null;

          // Attach observers after Markdown produced the nodes
          try {
            this.highlighter.observeNewCode(extra, {
              deferLastIfStreaming: true,
              minLinesForLast: this.renderer.cfg.PROFILE_CODE.minLinesForHL,
              minCharsForLast: this.renderer.cfg.PROFILE_CODE.minCharsForHL
            }, activeCode);
            this.highlighter.observeMsgBoxes(extra, (box) => this._onBox(box));
          } catch (_) {}

          // KaTeX: honor stream mode; in finalize-only force immediate schedule,
          // now guaranteed to find <script type="math/tex"> nodes.
          try {
            const mm = getMathMode();
            if (mm === 'finalize-only') this.math.schedule(extra, 0, true);
            else this.math.schedule(extra);
          } catch (_) {}
        };

        if (maybePromise && typeof maybePromise.then === 'function') {
          maybePromise.then(post);
        } else {
          post();
        }
      } catch (_) { /* swallow */ }

      scrollMgr.scheduleScroll(true);
    }
    // When a new message box appears, hook up code/highlight handlers.
    _onBox(box) {
      const activeCode = (typeof runtime !== 'undefined' && runtime.stream) ? runtime.stream.activeCode : null;
      this.highlighter.observeNewCode(box, {
        deferLastIfStreaming: true,
        minLinesForLast: this.renderer.cfg.PROFILE_CODE.minLinesForHL,
        minCharsForLast: this.renderer.cfg.PROFILE_CODE.minCharsForHL
      }, activeCode);
      this.renderer.hooks.codeScrollInit(box);
    }
    // Remove message by id and keep scroll consistent.
    removeNode(id, scrollMgr) {
      scrollMgr.prevScroll = 0;
      let el = document.getElementById('msg-user-' + id); if (el) el.remove();
      el = document.getElementById('msg-bot-' + id); if (el) el.remove();
      this.dom.resetEphemeral();
      try { this.renderer.renderPendingMarkdown(); } catch (_) {}
      scrollMgr.scheduleScroll(true);
    }
    // Remove all messages from (and including) a given message id.
    removeNodesFromId(id, scrollMgr) {
      scrollMgr.prevScroll = 0;
      const container = this.dom.get('_nodes_'); if (!container) return;
      const elements = container.querySelectorAll('.msg-box');
      let remove = false;
      elements.forEach((element) => {
        if (element.id && element.id.endsWith('-' + id)) remove = true;
        if (remove) element.remove();
      });
      this.dom.resetEphemeral();
      try { this.renderer.renderPendingMarkdown(container); } catch (_) {}
      scrollMgr.scheduleScroll(true);
    }
  }

  // ==========================================================================
  // 10) UI manager
  // ==========================================================================

  class UIManager {
    // Replace or insert app-level CSS in a <style> tag.
    updateCSS(styles) {
      let style = document.getElementById('app-style');
      if (!style) { style = document.createElement('style'); style.id = 'app-style'; document.head.appendChild(style); }
      style.textContent = styles;
    }
    // Ensure base styles for code header sticky behavior exist.
    ensureStickyHeaderStyle() {
      let style = document.getElementById('code-sticky-style');
      if (style) return;
      style = document.createElement('style'); style.id = 'code-sticky-style';
      style.textContent = [
        '.code-wrapper { position: relative; }',
        '.code-wrapper .code-header-wrapper { position: sticky; top: var(--code-header-sticky-top, 0px); z-index: 2; box-shadow: 0 1px 0 rgba(0,0,0,.06); }',
        '.code-wrapper pre { overflow: visible; margin-top: 0; }',
        '.code-wrapper pre code { display: block; white-space: pre; max-height: 100dvh; overflow: auto;',
        '  overscroll-behavior: contain; -webkit-overflow-scrolling: touch; overflow-anchor: none; scrollbar-gutter: stable both-edges; scroll-behavior: auto; }',
        '#_loader_.hidden { display: none !important; visibility: hidden !important; }',
        '#_loader_.visible { display: block; visibility: visible; }'
      ].join('\n');
      document.head.appendChild(style);
    }
    // Toggle classes controlling optional UI features.
    enableEditIcons() { document.body && document.body.classList.add('display-edit-icons'); }
    disableEditIcons() { document.body && document.body.classList.remove('display-edit-icons'); }
    enableTimestamp() { document.body && document.body.classList.add('display-timestamp'); }
    disableTimestamp() { document.body && document.body.classList.remove('display-timestamp'); }
    enableBlocks() { document.body && document.body.classList.add('display-blocks'); }
    disableBlocks() { document.body && document.body.classList.remove('display-blocks'); }
  }

  // ==========================================================================
  // 11) Stream snapshot engine + incremental code streaming
  // ==========================================================================

  class StreamEngine {
    constructor(cfg, dom, renderer, math, highlighter, codeScroll, scrollMgr, raf, asyncer, logger) {
      this.cfg = cfg; this.dom = dom; this.renderer = renderer; this.math = math;
      this.highlighter = highlighter; this.codeScroll = codeScroll; this.scrollMgr = scrollMgr; this.raf = raf;
      this.asyncer = asyncer;
      this.logger = logger || new Logger(cfg);

      // Streaming buffer (rope-like) – avoids O(n^2) string concatenation when many small chunks arrive.
      // streamBuf holds the already materialized prefix; _sbParts keeps recent tail parts; _sbLen tracks their length.
      this.streamBuf = '';     // materialized prefix (string used by render)
      this._sbParts = [];      // pending string chunks (array) not yet joined
      this._sbLen = 0;         // length of pending chunks

      this.fenceOpen = false; this.fenceMark = '`'; this.fenceLen = 3;
      this.fenceTail = ''; this.fenceBuf = '';
      this.lastSnapshotTs = 0; this.nextSnapshotStep = cfg.PROFILE_TEXT.base;
      this.snapshotScheduled = false; this.snapshotRAF = 0;

      this.codeStream = { open: false, lines: 0, chars: 0 };
      this.activeCode = null;

      this.suppressPostFinalizePass = false;

      this._promoteScheduled = false;

      // Guard to ensure first fence-open is materialized immediately when stream starts with code.
      this._firstCodeOpenSnapDone = false;

      // Streaming mode flag – controls reduced rendering (no linkify etc.) on hot path.
      this.isStreaming = false;
    }
    _d(tag, data) { this.logger.debug('STREAM', tag, data); }

    // --- Rope buffer helpers (internal) ---

    // Append a chunk into the rope without immediately touching the large string.
    _appendChunk(s) {
      if (!s) return;
      this._sbParts.push(s);
      this._sbLen += s.length;
    }
    // Current logical length of the stream text (materialized prefix + pending tail).
    getStreamLength() {
      return (this.streamBuf.length + this._sbLen);
    }
    // Materialize the rope into a single string for rendering (cheap if nothing pending).
    getStreamText() {
      if (this._sbLen > 0) {
        // Join pending parts into the materialized prefix and clear the tail.
        // Single-part fast path avoids a temporary array join.
        this.streamBuf += (this._sbParts.length === 1 ? this._sbParts[0] : this._sbParts.join(''));
        this._sbParts.length = 0;
        this._sbLen = 0;
      }
      return this.streamBuf;
    }
    // Reset the rope to an empty state.
    _clearStreamBuffer() {
      this.streamBuf = '';
      this._sbParts.length = 0;
      this._sbLen = 0;
    }

    // Reset all streaming state and counters.
    reset() {
      this._clearStreamBuffer();
      this.fenceOpen = false; this.fenceMark = '`'; this.fenceLen = 3;
      this.fenceTail = ''; this.fenceBuf = '';
      this.lastSnapshotTs = 0; this.nextSnapshotStep = this.profile().base;
      this.snapshotScheduled = false; this.snapshotRAF = 0;
      this.codeStream = { open: false, lines: 0, chars: 0 };
      this.activeCode = null; this.suppressPostFinalizePass = false;
      this._promoteScheduled = false;
      this._firstCodeOpenSnapDone = false;
      this._d('RESET', { });
    }
    // Turn active streaming code block into plain text (safety on abort).
    defuseActiveToPlain() {
      if (!this.activeCode || !this.activeCode.codeEl || !this.activeCode.codeEl.isConnected) return;
      const codeEl = this.activeCode.codeEl;
      const fullText = (this.activeCode.frozenEl?.textContent || '') + (this.activeCode.tailEl?.textContent || '');
      try {
        codeEl.textContent = fullText;
        codeEl.removeAttribute('data-highlighted');
        codeEl.classList.remove('hljs');
        codeEl.dataset._active_stream = '0';
        const st = this.codeScroll.state(codeEl); st.autoFollow = false;
      } catch (_) {}
      this._d('DEFUSE_ACTIVE_TO_PLAIN', { len: fullText.length });
      this.activeCode = null;
    }
    // If there are orphan streaming code blocks in DOM, finalize them as plain text.
    defuseOrphanActiveBlocks(root) {
      try {
        const scope = root || document;
        const nodes = scope.querySelectorAll('pre code[data-_active_stream="1"]');
        let n = 0;
        nodes.forEach(codeEl => {
          if (!codeEl.isConnected) return;
          let text = '';
          const frozen = codeEl.querySelector('.hl-frozen');
          const tail = codeEl.querySelector('.hl-tail');
          if (frozen || tail) text = (frozen?.textContent || '') + (tail?.textContent || '');
          else text = codeEl.textContent || '';
          codeEl.textContent = text;
          codeEl.removeAttribute('data-highlighted');
          codeEl.classList.remove('hljs');
          codeEl.dataset._active_stream = '0';
          try { this.codeScroll.attachHandlers(codeEl); } catch (_) {}
          n++;
        });
        if (n) this._d('DEFUSE_ORPHAN_ACTIVE_BLOCKS', { count: n });
      } catch (e) { this._d('DEFUSE_ORPHAN_ACTIVE_ERR', String(e)); }
    }
    // Abort streaming and clear state with options.
    abortAndReset(opts) {
      const o = Object.assign({
        finalizeActive: true,
        clearBuffer: true,
        clearMsg: false,
        defuseOrphans: true,
        reason: '',
        suppressLog: false
      }, (opts || {}));

      try { this.raf.cancelGroup('StreamEngine'); } catch (_) {}
      try { this.raf.cancel('SE:snapshot'); } catch (_) {}
      this.snapshotScheduled = false; this.snapshotRAF = 0;

      const hadActive = !!this.activeCode;
      try {
        if (this.activeCode) {
          if (o.finalizeActive === true) this.finalizeActiveCode();
          else this.defuseActiveToPlain();
        }
      } catch (e) {
        this._d('ABORT_FINALIZE_ERR', String(e));
      }

      if (o.defuseOrphans) {
        try { this.defuseOrphanActiveBlocks(); }
        catch (e) { this._d('ABORT_DEFUSE_ORPHANS_ERR', String(e)); }
      }

      if (o.clearBuffer) {
        this._clearStreamBuffer();
        this.fenceOpen = false; this.fenceMark = '`'; this.fenceLen = 3;
        this.fenceTail = ''; this.fenceBuf = '';
        this.codeStream.open = false; this.codeStream.lines = 0; this.codeStream.chars = 0;
        window.__lastSnapshotLen = 0;
      }
      if (o.clearMsg === true) {
        try { this.dom.resetEphemeral(); } catch (_) {}
      }
      if (!o.suppressLog) this._d('ABORT_AND_RESET', { hadActive, ...o });
    }
    // Select profile for current stream state (code vs text).
    profile() { return this.fenceOpen ? this.cfg.PROFILE_CODE : this.cfg.PROFILE_TEXT; }
    // Reset adaptive snapshot budget to base.
    resetBudget() { this.nextSnapshotStep = this.profile().base; }
    // Check whether [from, end) contains only spaces/tabs.
    onlyTrailingWhitespace(s, from, end) {
      for (let i = from; i < end; i++) { const c = s.charCodeAt(i); if (c !== 0x20 && c !== 0x09) return false; }
      return true;
    }
    // Update fence state based on a fresh chunk and buffer tail; detect openings and closings.
    updateFenceHeuristic(chunk) {
      const prev = (this.fenceBuf || '');
      const s = prev + (chunk || '');
      const preLen = prev.length;
      const n = s.length; let i = 0;
      let opened = false; let closed = false; let splitAt = -1;
      let atLineStart = (preLen === 0) ? true : /[\n\r]$/.test(prev);

      const inNewOrCrosses = (j, k) => (j >= preLen) || (k > preLen);

      while (i < n) {
        const ch = s[i];
        if (ch === '\r' || ch === '\n') { atLineStart = true; i++; continue; }
        if (!atLineStart) { i++; continue; }
        atLineStart = false;

        let j = i;
        while (j < n) {
          let localSpaces = 0;
          while (j < n && (s[j] === ' ' || s[j] === '\t')) { localSpaces += (s[j] === '\t') ? 4 : 1; j++; if (localSpaces > 3) break; }
          if (j < n && s[j] === '>') { j++; if (j < n && s[j] === ' ') j++; continue; }
          let saved = j;
          if (j < n && (s[j] === '-' || s[j] === '*' || s[j] === '+')) {
            let jj = j + 1; if (jj < n && s[jj] === ' ') { j = jj + 1; } else { j = saved; }
          } else {
            let k2 = j; let hasDigit = false;
            while (k2 < n && s[k2] >= '0' && s[k2] <= '9') { hasDigit = true; k2++; }
            if (hasDigit && k2 < n && (s[k2] === '.' || s[k2] === ')')) {
              k2++; if (k2 < n && s[k2] === ' ') { j = k2 + 1; } else { j = saved; }
            } else { j = saved; }
          }
          break;
        }

        let indent = 0;
        while (j < n && (s[j] === ' ' || s[j] === '\t')) {
          indent += (s[j] === '\t') ? 4 : 1; j++; if (indent > 3) break;
        }
        if (indent > 3) { i = j; continue; }

        if (j < n && (s[j] === '`' || s[j] === '~')) {
          const mark = s[j]; let k = j; while (k < n && s[k] === mark) k++; const run = k - j;

          if (!this.fenceOpen) {
            if (run >= 3) {
              if (!inNewOrCrosses(j, k)) { i = k; continue; }
              this.fenceOpen = true; this.fenceMark = mark; this.fenceLen = run; opened = true; i = k;
              this._d('FENCE_OPEN_DETECTED', { mark, run, idxStart: j, idxEnd: k, bufTail: this.fenceTail, region: (j >= preLen) ? 'new' : 'cross' });
              continue;
            }
          } else {
            if (mark === this.fenceMark && run >= this.fenceLen) {
              if (!inNewOrCrosses(j, k)) { i = k; continue; }
              let eol = k; while (eol < n && s[eol] !== '\n' && s[eol] !== '\r') eol++;
              if (this.onlyTrailingWhitespace(s, k, eol)) {
                this.fenceOpen = false; closed = true;
                const endInS = k;
                const rel = endInS - preLen;
                const split = Math.max(0, Math.min((chunk ? chunk.length : 0), rel));
                splitAt = split; i = k;
                this._d('FENCE_CLOSE_DETECTED', { mark, run, idxStart: j, idxEnd: k, splitAt, region: (j >= preLen) ? 'new' : 'cross' });
                continue;
              } else {
                this._d('FENCE_CLOSE_REJECTED_NON_WS_AFTER', { mark, run, idxStart: j, idxEnd: k, region: (j >= preLen) ? 'new' : (k > preLen ? 'cross' : 'old') });
              }
            }
          }
        }
        i = j + 1;
      }

      const MAX_TAIL = 512;
      this.fenceBuf = s.slice(-MAX_TAIL);
      this.fenceTail = s.slice(-3);
      return { opened, closed, splitAt };
    }
    // Ensure message snapshot container exists.
    getMsgSnapshotRoot(msg) {
      if (!msg) return null;
      let snap = msg.querySelector('.md-snapshot-root');
      if (!snap) { snap = document.createElement('div'); snap.className = 'md-snapshot-root'; msg.appendChild(snap); }
      return snap;
    }
    // Detect structural boundaries in a chunk (for snapshot decisions).
    hasStructuralBoundary(chunk) { if (!chunk) return false; return /\n(\n|[-*]\s|\d+\.\s|#{1,6}\s|>\s)/.test(chunk); }
    // Decide whether we should snapshot on this chunk.
    shouldSnapshotOnChunk(chunk, chunkHasNL, hasBoundary) {
      const prof = this.profile(); const now = Utils.now();
      if (this.activeCode && this.fenceOpen) return false;
      if ((now - this.lastSnapshotTs) < prof.minInterval) return false;
      if (hasBoundary) return true;

      const delta = Math.max(0, this.getStreamLength() - (window.__lastSnapshotLen || 0));
      if (this.fenceOpen) { if (chunkHasNL && delta >= this.nextSnapshotStep) return true; return false; }
      if (delta >= this.nextSnapshotStep) return true;
      return false;
    }
    // If we are getting slow, schedule a soft snapshot based on time.
    maybeScheduleSoftSnapshot(msg, chunkHasNL) {
      const prof = this.profile(); const now = Utils.now();
      if (this.activeCode && this.fenceOpen) return;
      if (this.fenceOpen && this.codeStream.lines < 1 && !chunkHasNL) return;
      if ((now - this.lastSnapshotTs) >= prof.softLatency) this.scheduleSnapshot(msg);
    }
    // Schedule snapshot rendering (coalesced via rAF).
    scheduleSnapshot(msg, force = false) {
      if (this.snapshotScheduled && !this.raf.isScheduled('SE:snapshot')) this.snapshotScheduled = false;
      if (!force) {
        if (this.snapshotScheduled) return;
        if (this.activeCode && this.fenceOpen) return;
      } else {
        if (this.snapshotScheduled && this.raf.isScheduled('SE:snapshot')) return;
      }
      this.snapshotScheduled = true;
      this.raf.schedule('SE:snapshot', () => { this.snapshotScheduled = false; this.renderSnapshot(msg); }, 'StreamEngine', 0);
    }
    // Split code element into frozen and tail spans if needed.
    ensureSplitCodeEl(codeEl) {
      if (!codeEl) return null;
      let frozen = codeEl.querySelector('.hl-frozen'); let tail = codeEl.querySelector('.hl-tail');
      if (frozen && tail) return { codeEl, frozenEl: frozen, tailEl: tail };
      const text = codeEl.textContent || ''; codeEl.innerHTML = '';
      frozen = document.createElement('span'); frozen.className = 'hl-frozen';
      tail = document.createElement('span'); tail.className = 'hl-tail';
      codeEl.appendChild(frozen); codeEl.appendChild(tail);
      if (text) tail.textContent = text; return { codeEl, frozenEl: frozen, tailEl: tail };
    }
    // Create active code context from the latest snapshot.
    setupActiveCodeFromSnapshot(snap) {
      const codes = snap.querySelectorAll('pre code'); if (!codes.length) return null;
      const last = codes[codes.length - 1];
      const cls = Array.from(last.classList).find(c => c.startsWith('language-')) || 'language-plaintext';
      const lang = (cls.replace('language-', '') || 'plaintext');
      const parts = this.ensureSplitCodeEl(last); if (!parts) return null;
      const st = this.codeScroll.state(parts.codeEl); st.autoFollow = true; st.userInteracted = false;
      parts.codeEl.dataset._active_stream = '1';
      const baseFrozenNL = Utils.countNewlines(parts.frozenEl.textContent || ''); const baseTailNL = Utils.countNewlines(parts.tailEl.textContent || '');
      const ac = { codeEl: parts.codeEl, frozenEl: parts.frozenEl, tailEl: parts.tailEl, lang, frozenLen: parts.frozenEl.textContent.length, lastPromoteTs: 0,
                   lines: 0, tailLines: baseTailNL, linesSincePromote: 0, initialLines: baseFrozenNL + baseTailNL, haltHL: false, plainStream: false };
      this._d('ACTIVE_CODE_SETUP', { lang, frozenLen: ac.frozenLen, tailLines: ac.tailLines, initialLines: ac.initialLines });
      return ac;
    }
    // Copy previous active code state into the new one (after snapshot).
    rehydrateActiveCode(oldAC, newAC) {
      if (!oldAC || !newAC) return;
      newAC.frozenEl.innerHTML = oldAC.frozenEl ? oldAC.frozenEl.innerHTML : '';
      const fullText = newAC.codeEl.textContent || ''; const remainder = fullText.slice(oldAC.frozenLen);
      newAC.tailEl.textContent = remainder;
      newAC.frozenLen = oldAC.frozenLen; newAC.lang = oldAC.lang;
      newAC.lines = oldAC.lines; newAC.tailLines = Utils.countNewlines(remainder);
      newAC.lastPromoteTs = oldAC.lastPromoteTs; newAC.linesSincePromote = oldAC.linesSincePromote || 0;
      newAC.initialLines = oldAC.initialLines || 0; newAC.haltHL = !!oldAC.haltHL;
      newAC.plainStream = !!oldAC.plainStream;
      this._d('ACTIVE_CODE_REHYDRATE', { lang: newAC.lang, frozenLen: newAC.frozenLen, tailLines: newAC.tailLines, initialLines: newAC.initialLines, halted: newAC.haltHL, plainStream: newAC.plainStream });
    }
    // Append text to active tail span and update counters.
    appendToActiveTail(text) {
      if (!this.activeCode || !this.activeCode.tailEl || !text) return;
      this.activeCode.tailEl.insertAdjacentText('beforeend', text);
      const nl = Utils.countNewlines(text);
      this.activeCode.tailLines += nl; this.activeCode.linesSincePromote += nl;
      this.codeScroll.scheduleScroll(this.activeCode.codeEl, true, false);
      if (this.logger.isEnabled('STREAM') && (nl > 0 || text.length >= 64)) {
        this._d('TAIL_APPEND', { addLen: text.length, addNL: nl, totalTailNL: this.activeCode.tailLines });
      }
    }
    // Enforce budgets: stop incremental hljs and switch to plain streaming if needed.
    enforceHLStopBudget() {
      if (!this.activeCode) return;
      // If global disable was requested, halt early and switch to plain streaming.
      if (this.cfg.HL.DISABLE_ALL) { this.activeCode.haltHL = true; this.activeCode.plainStream = true; return; }
      const stop = (this.cfg.PROFILE_CODE.stopAfterLines | 0);
      const streamPlainLines = (this.cfg.PROFILE_CODE.streamPlainAfterLines | 0);
      const streamPlainChars = (this.cfg.PROFILE_CODE.streamPlainAfterChars | 0);
      const maxFrozenChars = (this.cfg.PROFILE_CODE.maxFrozenChars | 0);

      const totalLines = (this.activeCode.initialLines || 0) + (this.activeCode.lines || 0);
      const frozenChars = this.activeCode.frozenLen | 0;
      const tailChars = (this.activeCode.tailEl?.textContent || '').length | 0;
      const totalStreamedChars = frozenChars + tailChars;

      // Switch to plain streaming after budgets – no incremental hljs
      if ((streamPlainLines > 0 && totalLines >= streamPlainLines) ||
          (streamPlainChars > 0 && totalStreamedChars >= streamPlainChars) ||
          (maxFrozenChars > 0 && frozenChars >= maxFrozenChars)) {
        this.activeCode.haltHL = true;
        this.activeCode.plainStream = true;
        try { this.activeCode.codeEl.dataset.hlStreamSuspended = '1'; } catch (_) {}
        this._d('STREAM_HL_SUSPENDED', { totalLines, totalStreamedChars, frozenChars, reason: 'budget' });
        return;
      }

      if (stop > 0 && totalLines >= stop) {
        this.activeCode.haltHL = true;
        this.activeCode.plainStream = true;
        try { this.activeCode.codeEl.dataset.hlStreamSuspended = '1'; } catch (_) {}
        this._d('STREAM_HL_SUSPENDED', { totalLines, stopAfter: stop, reason: 'stopAfterLines' });
      }
    }
    _aliasLang(token) {
      const ALIAS = {
        txt: 'plaintext', text: 'plaintext', plaintext: 'plaintext',
        sh: 'bash', shell: 'bash', zsh: 'bash', 'shell-session': 'bash',
        py: 'python', python3: 'python', py3: 'python',
        js: 'javascript', node: 'javascript', nodejs: 'javascript',
        ts: 'typescript', 'ts-node': 'typescript',
        yml: 'yaml', kt: 'kotlin', rs: 'rust',
        csharp: 'csharp', 'c#': 'csharp', 'c++': 'cpp',
        ps: 'powershell', ps1: 'powershell', pwsh: 'powershell', powershell7: 'powershell',
        docker: 'dockerfile'
      };
      const v = String(token || '').trim().toLowerCase();
      return ALIAS[v] || v;
    }
    _isHLJSSupported(lang) {
      try { return !!(window.hljs && hljs.getLanguage && hljs.getLanguage(lang)); } catch (_) { return false; }
    }
    // Try to detect language from a "language: X" style first line directive.
    _detectDirectiveLangFromText(text) {
      if (!text) return null;
      let s = String(text);
      if (s.charCodeAt(0) === 0xFEFF) s = s.slice(1);
      const lines = s.split(/\r?\n/);
      let i = 0; while (i < lines.length && !lines[i].trim()) i++;
      if (i >= lines.length) return null;
      let first = lines[i].trim();
      first = first.replace(/^\s*lang(?:uage)?\s*[:=]\s*/i, '').trim();
      let token = first.split(/\s+/)[0].replace(/:$/, '');
      if (!/^[A-Za-z][\w#+\-\.]{0,30}$/.test(token)) return null;

      let cand = this._aliasLang(token);
      const rest = lines.slice(i + 1).join('\n');
      if (!rest.trim()) return null;

      let pos = 0, seen = 0;
      while (seen < i && pos < s.length) { const nl = s.indexOf('\n', pos); if (nl === -1) return null; pos = nl + 1; seen++; }
      let end = s.indexOf('\n', pos);
      if (end === -1) end = s.length; else end = end + 1;
      return { lang: cand, deleteUpto: end };
    }
    // Update code element class to reflect new lang (language-xxx).
    _updateCodeLangClass(codeEl, newLang) {
      try {
        Array.from(codeEl.classList).forEach(c => { if (c.startsWith('language-')) codeEl.classList.remove(c); });
        codeEl.classList.add('language-' + (newLang || 'plaintext'));
      } catch (_) {}
    }
    // Update code header label and data attribute.
    _updateCodeHeaderLabel(codeEl, newLabel, newLangToken) {
      try {
        const wrap = codeEl.closest('.code-wrapper');
        if (!wrap) return;
        const span = wrap.querySelector('.code-header-lang');
        if (span) span.textContent = newLabel || (newLangToken || 'code');
        wrap.setAttribute('data-code-lang', newLangToken || '');
      } catch (_) {}
    }
    // Try to promote language from a directive and remove its header line.
    maybePromoteLanguageFromDirective() {
      if (!this.activeCode || !this.activeCode.codeEl) return;
      if (this.activeCode.lang && this.activeCode.lang !== 'plaintext') return;

      const frozenTxt = this.activeCode.frozenEl ? this.activeCode.frozenEl.textContent : '';
      const tailTxt = this.activeCode.tailEl ? this.activeCode.tailEl.textContent : '';
      const combined = frozenTxt + tailTxt;
      if (!combined) return;

      const det = this._detectDirectiveLangFromText(combined);
      if (!det || !det.lang) return;

      const newLang = det.lang;
      const newCombined = combined.slice(det.deleteUpto);

      try {
        const codeEl = this.activeCode.codeEl;
        codeEl.innerHTML = '';
        const frozen = document.createElement('span'); frozen.className = 'hl-frozen';
        const tail = document.createElement('span'); tail.className = 'hl-tail';
        tail.textContent = newCombined;
        codeEl.appendChild(frozen); codeEl.appendChild(tail);
        this.activeCode.frozenEl = frozen; this.activeCode.tailEl = tail;
        this.activeCode.frozenLen = 0;
        this.activeCode.tailLines = Utils.countNewlines(newCombined);
        this.activeCode.linesSincePromote = 0;

        this.activeCode.lang = newLang;
        this._updateCodeLangClass(codeEl, newLang);
        this._updateCodeHeaderLabel(codeEl, newLang, newLang);

        this._d('LANG_PROMOTE', { to: newLang, removedChars: det.deleteUpto, tailLines: this.activeCode.tailLines });
        this.schedulePromoteTail(true);
      } catch (e) {
        this._d('LANG_PROMOTE_ERR', String(e));
      }
    }
    // Highlight a small piece of text based on language (safe fallback to escapeHtml).
    highlightDeltaText(lang, text) {
      if (this.cfg.HL.DISABLE_ALL) return Utils.escapeHtml(text);
      if (window.hljs && lang && hljs.getLanguage && hljs.getLanguage(lang)) {
        try { return hljs.highlight(text, { language: lang, ignoreIllegals: true }).value; }
        catch (_) { return Utils.escapeHtml(text); }
      }
      return Utils.escapeHtml(text);
    }
    // Schedule cooperative tail promotion (async) to avoid blocking UI on each chunk.
    schedulePromoteTail(force = false) {
      if (!this.activeCode || !this.activeCode.tailEl) return;
      if (this._promoteScheduled) return;
      this._promoteScheduled = true;
      this.raf.schedule('SE:promoteTail', () => {
        this._promoteScheduled = false;
        this._promoteTailWork(force);
      }, 'StreamEngine', 1);
    }
    // Move a full-line part of tail into frozen region (with highlight if budgets allow).
    async _promoteTailWork(force = false) {
      if (!this.activeCode || !this.activeCode.tailEl) return;

      // If plain streaming mode is on, or incremental hljs is disabled, promote as plain text only.
      const now = Utils.now(); const prof = this.cfg.PROFILE_CODE;
      const tailText0 = this.activeCode.tailEl.textContent || ''; if (!tailText0) return;

      if (!force) {
        if ((now - this.activeCode.lastPromoteTs) < prof.promoteMinInterval) return;
        const enoughLines = (this.activeCode.linesSincePromote || 0) >= (prof.promoteMinLines || 10);
        const enoughChars = tailText0.length >= prof.minCharsForHL;
        if (!enoughLines && !enoughChars) return;
      }

      // Cut at last full line to avoid moving partial tokens
      const idx = tailText0.lastIndexOf('\n');
      if (idx <= -1 && !force) return;
      const cut = (idx >= 0) ? (idx + 1) : tailText0.length;
      const delta = tailText0.slice(0, cut); if (!delta) return;

      // Re-evaluate budgets before performing any heavy work
      this.enforceHLStopBudget();
      const usePlain = this.activeCode.haltHL || this.activeCode.plainStream || !this._isHLJSSupported(this.activeCode.lang);

      // Cooperative rAF yield before heavy highlight
      if (!usePlain) await this.asyncer.yield();

      // If tail changed since we captured it, validate prefix to avoid duplication
      if (!this.activeCode || !this.activeCode.tailEl) return;
      const tailNow = this.activeCode.tailEl.textContent || '';
      if (!tailNow.startsWith(delta)) {
        // New data arrived; reschedule for next frame without touching DOM
        this.schedulePromoteTail(false);
        return;
      }

      // Apply DOM updates: either highlighted HTML delta or plain text
      if (usePlain) {
        // Plain text promotion – extremely cheap, no spans created.
        this.activeCode.frozenEl.insertAdjacentText('beforeend', delta);
      } else {
        // Highlighted promotion – still capped by budgets above.
        let html = Utils.escapeHtml(delta);
        try { html = this.highlightDeltaText(this.activeCode.lang, delta); } catch (_) { html = Utils.escapeHtml(delta); }
        this.activeCode.frozenEl.insertAdjacentHTML('beforeend', html);
      }

      // Update tail and counters
      this.activeCode.tailEl.textContent = tailNow.slice(delta.length);
      this.activeCode.frozenLen += delta.length;
      const promotedLines = Utils.countNewlines(delta);
      this.activeCode.tailLines = Math.max(0, (this.activeCode.tailLines || 0) - promotedLines);
      this.activeCode.linesSincePromote = Math.max(0, (this.activeCode.linesSincePromote || 0) - promotedLines);
      this.activeCode.lastPromoteTs = Utils.now();
      this.codeScroll.scheduleScroll(this.activeCode.codeEl, true, false);
      this._d(usePlain ? 'TAIL_PROMOTE_PLAIN' : 'TAIL_PROMOTE_ASYNC', { cut, promotedLines, lang: this.activeCode.lang, plain: usePlain });
    }
    // Finalize the current active code block. Keep it plain for now and schedule highlight lazily.
    finalizeActiveCode() {
      if (!this.activeCode) return;
      const codeEl = this.activeCode.codeEl;
      const fromBottomBefore = Math.max(0, codeEl.scrollHeight - codeEl.clientHeight - codeEl.scrollTop);
      const wasNearBottom = this.codeScroll.isNearBottomEl(codeEl, this.cfg.CODE_SCROLL.NEAR_MARGIN_PX);
      const fullText = (this.activeCode.frozenEl.textContent || '') + (this.activeCode.tailEl.textContent || '');

      // Non-blocking finalize: place plain text now, schedule highlight via Highlighter later.
      try {
        codeEl.innerHTML = '';
        codeEl.textContent = fullText;
        codeEl.classList.add('hljs');           // keep visual parity until highlight applies
        codeEl.removeAttribute('data-highlighted');
      } catch (_) {}

      const st = this.codeScroll.state(codeEl); st.autoFollow = false;
      const maxScrollTop = Math.max(0, codeEl.scrollHeight - codeEl.clientHeight);
      const target = wasNearBottom ? maxScrollTop : Math.max(0, maxScrollTop - fromBottomBefore);
      try { codeEl.scrollTop = target; } catch (_) {}
      st.lastScrollTop = codeEl.scrollTop;
      codeEl.dataset._active_stream = '0';

      try { codeEl.dataset.justFinalized = '1'; } catch (_) {}
      this.codeScroll.scheduleScroll(codeEl, false, true);

      // Schedule async highlight on the finalized element (viewport-aware).
      try { if (!this.cfg.HL.DISABLE_ALL) this.highlighter.queue(codeEl, null); } catch (_) {}

      this.suppressPostFinalizePass = true;

      this._d('FINALIZE_CODE_NONBLOCK', { lang: this.activeCode.lang, len: fullText.length, highlighted: false });
      this.activeCode = null;
    }
    // Make a simple fingerprint to reuse identical closed code blocks between snapshots.
    codeFingerprint(codeEl) {
      const cls = Array.from(codeEl.classList).find(c => c.startsWith('language-')) || 'language-plaintext';
      const lang = cls.replace('language-', '') || 'plaintext';
      const t = codeEl.textContent || ''; const len = t.length; const head = t.slice(0, 64); const tail = t.slice(-64);
      return `${lang}|${len}|${head}|${tail}`;
    }
    // fingerprint using precomputed meta on wrapper (avoids .textContent for heavy blocks).
    codeFingerprintFromWrapper(codeEl) {
      try {
        const wrap = codeEl.closest('.code-wrapper'); if (!wrap) return null;
        const cls = Array.from(codeEl.classList).find(c => c.startsWith('language-')) || 'language-plaintext';
        const lang = (cls.replace('language-', '') || 'plaintext');
        const len = wrap.getAttribute('data-code-len') || '';
        const head = wrap.getAttribute('data-code-head') || '';
        const tail = wrap.getAttribute('data-code-tail') || '';
        if (!len) return null; // ensure at least length exists
        return `${lang}|${len}|${head}|${tail}`;
      } catch (_) {
        return null;
      }
    }
    // Try to reuse old finalized code block DOM nodes to avoid re-highlighting.
    preserveStableClosedCodes(oldSnap, newRoot, skipLastIfStreaming) {
      try {
        const oldCodes = Array.from(oldSnap.querySelectorAll('pre code')); if (!oldCodes.length) return;
        // Safety guard: avoid heavy fingerprint work on extremely large outputs
        const newCodesPre = Array.from(newRoot.querySelectorAll('pre code'));
        if (newCodesPre.length > this.cfg.STREAM.PRESERVE_CODES_MAX || oldCodes.length > this.cfg.STREAM.PRESERVE_CODES_MAX) return;

        const map = new Map();
        for (const el of oldCodes) {
          if (el.querySelector('.hl-frozen')) continue;               // skip streaming blocks
          if (this.activeCode && el === this.activeCode.codeEl) continue;
          // Try wrapper-based fingerprint first, fallback to text-based
          let fp = this.codeFingerprintFromWrapper(el);
          if (!fp) fp = el.dataset.fp || (el.dataset.fp = this.codeFingerprint(el));
          const arr = map.get(fp) || []; arr.push(el); map.set(fp, arr);
        }
        const newCodes = newCodesPre;
        const end = (skipLastIfStreaming && newCodes.length > 0) ? (newCodes.length - 1) : newCodes.length;
        let reuseCount = 0;
        for (let i = 0; i < end; i++) {
          const nc = newCodes[i];
          if (nc.getAttribute('data-highlighted') === 'yes') continue;
          // Fingerprint new code: prefer wrapper meta (no .textContent read)
          let fp = this.codeFingerprintFromWrapper(nc);
          if (!fp) fp = this.codeFingerprint(nc);
          const arr = map.get(fp);
          if (arr && arr.length) {
            const oldEl = arr.shift();
            if (oldEl && oldEl.isConnected) {
              try {
                nc.replaceWith(oldEl);
                this.codeScroll.attachHandlers(oldEl);
                // Preserve whatever final state the old element had
                if (!oldEl.getAttribute('data-highlighted')) oldEl.setAttribute('data-highlighted', 'yes');
                const st = this.codeScroll.state(oldEl); st.autoFollow = false;
                reuseCount++;
              } catch (_) {}
            }
            if (!arr.length) map.delete(fp);
          }
        }
        if (reuseCount) this._d('PRESERVE_CODES_REUSED', { reuseCount, skipLastIfStreaming });
      } catch (e) {
        this._d('PRESERVE_CODES_ERROR', String(e));
      }
    }
    // Ensure blocks marked as just-finalized are scrolled to bottom.
    _ensureBottomForJustFinalized(root) {
      try {
        const scope = root || document;
        const nodes = scope.querySelectorAll('pre code[data-just-finalized="1"]');
        if (!nodes || !nodes.length) return;
        nodes.forEach((codeEl) => {
          this.codeScroll.scheduleScroll(codeEl, false, true);
          const key = { t: 'JF:forceBottom', el: codeEl, n: Math.random() };
          this.raf.schedule(key, () => {
            this.codeScroll.scrollToBottom(codeEl, false, true);
            try { codeEl.dataset.justFinalized = '0'; } catch (_) {}
          }, 'CodeScroll', 2);
        });
      } catch (_) {}
    }
    // If stream is visible but something got stuck, force a quick refresh.
    kickVisibility() {
      const msg = this.getMsg(false, '');
      if (!msg) return;
      if (this.codeStream.open && !this.activeCode) {
        this.scheduleSnapshot(msg, true);
        return;
      }
      const needSnap = (this.getStreamLength() !== (window.__lastSnapshotLen || 0));
      if (needSnap) this.scheduleSnapshot(msg, true);
      if (this.activeCode && this.activeCode.codeEl) {
        this.codeScroll.scheduleScroll(this.activeCode.codeEl, true, false);
        this.schedulePromoteTail(true);
      }
    }
    // Render a snapshot of current stream buffer into the DOM.
    renderSnapshot(msg) {
      const streaming = !!this.isStreaming;
      const snap = this.getMsgSnapshotRoot(msg); if (!snap) return;

      // No-op if nothing changed and no active code
      const prevLen = (window.__lastSnapshotLen || 0);
      const curLen = this.getStreamLength();
      if (!this.fenceOpen && !this.activeCode && curLen === prevLen) {
        this.lastSnapshotTs = Utils.now();
        this._d('SNAPSHOT_SKIPPED_NO_DELTA', { bufLen: curLen });
        return;
      }

      const t0 = Utils.now();

      // Slightly adjusted: when fence is open we append '\n' to ensure stable fence-close detection
      const allText = this.getStreamText();
      const src = this.fenceOpen ? (allText + '\n') : allText;

      // Use streaming renderer (no linkify) on hot path to reduce CPU/allocs
      const html = streaming ? this.renderer.renderStreamingSnapshot(src) : this.renderer.renderFinalSnapshot(src);

      // parse HTML into a DocumentFragment directly to avoid intermediate container allocations.
      let frag = null;
      try {
        const range = document.createRange();
        range.selectNodeContents(snap);
        frag = range.createContextualFragment(html);
      } catch (_) {
        // Fallback: safe temporary container
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        frag = document.createDocumentFragment();
        while (tmp.firstChild) frag.appendChild(tmp.firstChild);
      }

      // Reuse closed, stable code blocks from previous snapshot to avoid re-highlighting
      this.preserveStableClosedCodes(snap, frag, this.fenceOpen === true);

      // Replace content
      snap.replaceChildren(frag);

      // Restore code UI state and ensure bottoming for freshly finalized elements
      this.renderer.restoreCollapsedCode(snap);
      this._ensureBottomForJustFinalized(snap);

      // Setup active streaming code if fence is open, otherwise clear active state
      if (this.fenceOpen) {
        const newAC = this.setupActiveCodeFromSnapshot(snap);
        this.activeCode = newAC || null;
      } else {
        this.activeCode = null;
      }

      // Attach scroll/highlight observers (viewport aware)
      if (!this.fenceOpen) {
        this.codeScroll.initScrollableBlocks(snap);
      }
      this.highlighter.observeNewCode(snap, {
        deferLastIfStreaming: true,
        minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
        minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
      }, this.activeCode);
      this.highlighter.observeMsgBoxes(snap, (box) => {
        this.highlighter.observeNewCode(box, {
          deferLastIfStreaming: true,
          minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
          minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
        }, this.activeCode);
        this.codeScroll.initScrollableBlocks(box);
      });

      // Schedule math render according to mode; keep "finalize-only" cheap on hot path
      const mm = getMathMode();
      if (!this.suppressPostFinalizePass) {
        if (mm === 'idle') this.math.schedule(snap);
        else if (mm === 'always') this.math.schedule(snap, 0, true);
      }

      // If streaming code is visible, keep it glued to bottom
      if (this.fenceOpen && this.activeCode && this.activeCode.codeEl) {
        this.codeScroll.attachHandlers(this.activeCode.codeEl);
        this.codeScroll.scheduleScroll(this.activeCode.codeEl, true, false);
      } else if (!this.fenceOpen) {
        this.codeScroll.initScrollableBlocks(snap);
      }

      // Advance snapshot budget and remember progress
      window.__lastSnapshotLen = this.getStreamLength();
      this.lastSnapshotTs = Utils.now();

      const prof = this.profile();
      if (prof.adaptiveStep) {
        const maxStep = this.cfg.STREAM.SNAPSHOT_MAX_STEP || 8000;
        this.nextSnapshotStep = Math.min(Math.ceil(this.nextSnapshotStep * prof.growth), maxStep);
      } else {
        this.nextSnapshotStep = prof.base;
      }

      // Keep page scroll/fab in sync
      this.scrollMgr.scheduleScroll(true);
      this.scrollMgr.fabFreezeUntil = Utils.now() + this.cfg.FAB.TOGGLE_DEBOUNCE_MS;
      this.scrollMgr.scheduleScrollFabUpdate();

      if (this.suppressPostFinalizePass) this.suppressPostFinalizePass = false;

      const dt = Utils.now() - t0;
      this._d('SNAPSHOT', { fenceOpen: this.fenceOpen, activeCode: !!this.activeCode, bufLen: this.getStreamLength(), timeMs: Math.round(dt), streaming });
    }
    // Get current message container (.msg) or create if allowed.
    getMsg(create, name_header) { return this.dom.getStreamMsg(create, name_header); }
    // Start a new streaming session (clear state and display loader, if any).
    beginStream(chunk = false) {
      this.isStreaming = true; // engage streaming mode (no linkify etc.)
      if (chunk) runtime.loading.hide();
      this.scrollMgr.userInteracted = false;
      this.dom.clearOutput();
      this.reset();
      this.scrollMgr.forceScrollToBottomImmediate();
      this.scrollMgr.scheduleScroll();
      this._d('BEGIN_STREAM', { chunkFlag: !!chunk });
    }
    // End streaming session, finalize active code if present, and complete math/highlight.
    endStream() {
      // Switch to final mode before the last snapshot to allow full renderer (linkify etc.)
      this.isStreaming = false;

      const msg = this.getMsg(false, '');
      if (msg) this.renderSnapshot(msg);

      this.snapshotScheduled = false;
      try { this.raf.cancel('SE:snapshot'); } catch (_) {}
      this.snapshotRAF = 0;

      const hadActive = !!this.activeCode;
      if (this.activeCode) this.finalizeActiveCode();

      if (!hadActive) {
        if (this.highlighter.hlQueue && this.highlighter.hlQueue.length) {
          this.highlighter.flush(this.activeCode);
        }
        const snap = msg ? this.getMsgSnapshotRoot(msg) : null;
        if (snap) this.math.renderAsync(snap); // ensure math completes eagerly but async
      }

      this.fenceOpen = false; this.codeStream.open = false; this.activeCode = null; this.lastSnapshotTs = Utils.now();
      this.suppressPostFinalizePass = false;
      this._d('END_STREAM', { hadActive });
    }
    // Apply incoming chunk to stream buffer and update DOM when needed.
    applyStream(name_header, chunk, alreadyBuffered = false) {
      if (!this.activeCode && !this.fenceOpen) {
        try { if (document.querySelector('pre code[data-_active_stream="1"]')) this.defuseOrphanActiveBlocks(); } catch (_) {}
      }
      if (this.snapshotScheduled && !this.raf.isScheduled('SE:snapshot')) this.snapshotScheduled = false;

      const msg = this.getMsg(true, name_header); if (!msg || !chunk) return;
      const s = String(chunk);
      if (!alreadyBuffered) this._appendChunk(s);

      const change = this.updateFenceHeuristic(s);
      const nlCount = Utils.countNewlines(s); const chunkHasNL = nlCount > 0;

      this._d('APPLY_CHUNK', { len: s.length, nl: nlCount, opened: change.opened, closed: change.closed, splitAt: change.splitAt, fenceOpenBefore: this.fenceOpen || false, codeOpenBefore: this.codeStream.open || false, rebroadcast: !!alreadyBuffered });

      // Track if we just materialized the first code-open snapshot synchronously.
      let didImmediateOpenSnap = false;

      if (change.opened) {
        this.codeStream.open = true; this.codeStream.lines = 0; this.codeStream.chars = 0;
        this.resetBudget();
        this.scheduleSnapshot(msg);
        this._d('CODE_STREAM_OPEN', { });

        // Fast-path: if stream starts with a code fence and no snapshot was made yet,
        // immediately materialize the code block so tail streaming can proceed without click.
        if (!this._firstCodeOpenSnapDone && !this.activeCode && ((window.__lastSnapshotLen || 0) === 0)) {
          try {
            this.renderSnapshot(msg);
            try { this.raf.cancel('SE:snapshot'); } catch (_) {}
            this.snapshotScheduled = false;
            this._firstCodeOpenSnapDone = true;
            didImmediateOpenSnap = true;
            this._d('CODE_OPEN_IMMEDIATE_SNAPSHOT', { bufLen: this.getStreamLength() });
          } catch (_) {
            // Keep going; normal scheduled snapshot will land soon.
          }
        }
      }

      if (this.codeStream.open) {
        this.codeStream.lines += nlCount; this.codeStream.chars += s.length;

        if (this.activeCode && this.activeCode.codeEl && this.activeCode.codeEl.isConnected) {
          let partForCode = s; let remainder = '';

          if (didImmediateOpenSnap) {
            partForCode = '';
          } else {
            if (change.closed && change.splitAt >= 0 && change.splitAt <= s.length) {
              partForCode = s.slice(0, change.splitAt); remainder = s.slice(change.splitAt);
            }
          }

          if (partForCode) {
            this.appendToActiveTail(partForCode);
            this.activeCode.lines += Utils.countNewlines(partForCode);

            this.maybePromoteLanguageFromDirective();
            this.enforceHLStopBudget();

            if (!this.activeCode.haltHL) {
              if (partForCode.indexOf('\n') >= 0 || (this.activeCode.tailEl.textContent || '').length >= this.cfg.PROFILE_CODE.minCharsForHL) {
                this.schedulePromoteTail(false);
              }
            }
          }
          this.scrollMgr.scrollFabUpdateScheduled = false;
          this.scrollMgr.scheduleScroll(true);
          this.scrollMgr.fabFreezeUntil = Utils.now() + this.cfg.FAB.TOGGLE_DEBOUNCE_MS;
          this.scrollMgr.scheduleScrollFabUpdate();

          if (change.closed) {
            this.finalizeActiveCode();
            this.codeStream.open = false; this.resetBudget(); this.scheduleSnapshot(msg);
            this._d('CODE_STREAM_CLOSE_FINALIZED', { remainderLen: remainder.length });
            if (remainder && remainder.length) { this.applyStream(name_header, remainder, true); }
          }
          return;
        } else {
          if (!this.activeCode && (this.codeStream.lines >= 2 || this.codeStream.chars >= 80)) {
            this.scheduleSnapshot(msg, true);
            return;
          }
          if (change.closed) {
            this.codeStream.open = false; this.resetBudget(); this.scheduleSnapshot(msg);
            this._d('CODE_CLOSED_WITHOUT_ACTIVE', { sinceLastSnapMs: Math.round(Utils.now() - this.lastSnapshotTs), snapshotScheduled: this.snapshotScheduled });
          } else {
            const boundary = this.hasStructuralBoundary(s);
            if (this.shouldSnapshotOnChunk(s, chunkHasNL, boundary)) this.scheduleSnapshot(msg);
            else this.maybeScheduleSoftSnapshot(msg, chunkHasNL);
          }
          return;
        }
      }

      if (change.closed) {
        this.codeStream.open = false; this.resetBudget(); this.scheduleSnapshot(msg);
        this._d('CODE_STREAM_CLOSE', { });
      } else {
        const boundary = this.hasStructuralBoundary(s);
        if (this.shouldSnapshotOnChunk(s, chunkHasNL, boundary)) {
          this.scheduleSnapshot(msg);
          this._d('SCHEDULE_SNAPSHOT_BOUNDARY', { boundary });
        } else {
          this.maybeScheduleSoftSnapshot(msg, chunkHasNL);
        }
      }
    }
  }

  // ==========================================================================
  // 12) Stream queue
  // ==========================================================================

  class StreamQueue {
    constructor(cfg, engine, scrollMgr, raf) {
      this.cfg = cfg; this.engine = engine; this.scrollMgr = scrollMgr; this.raf = raf;
      this.q = []; this.drainScheduled = false;
      this.batching = false; this.needScroll = false;
    }
    // Coalesce contiguous entries for the same header to reduce overhead.
    _compactContiguousSameName() {
      // Coalesce contiguous entries for the same message header to reduce string objects count.
      if (this.q.length < 2) return;
      const out = [];
      let last = this.q[0];
      for (let i = 1; i < this.q.length; i++) {
        const cur = this.q[i];
        if (cur.name_header === last.name_header) {
          // Merge payloads; reduce object overhead without changing semantics
          last.chunk = (last.chunk || '') + (cur.chunk || '');
        }
        else {
          out.push(last);
          last = cur;
        }
      }
      out.push(last);
      this.q = out;
    }
    // Push new chunk into the queue and schedule drain.
    enqueue(name_header, chunk) {
      this.q.push({ name_header, chunk });
      // Guard against unbounded growth during bursts
      if (this.q.length > this.cfg.STREAM.EMERGENCY_COALESCE_LEN) this._compactContiguousSameName();
      if (this.q.length > this.cfg.STREAM.QUEUE_MAX_ITEMS) this._compactContiguousSameName();
      if (!this.drainScheduled) {
        this.drainScheduled = true;
        this.raf.schedule('SQ:drain', () => this.drain(), 'StreamQueue', 0);
      }
    }
    // Drain a limited number of chunks per frame (adaptive if configured).
    drain() {
      this.drainScheduled = false; let processed = 0;
      const adaptive = (this.cfg.STREAM.COALESCE_MODE === 'adaptive');
      const coalesceAggressive = adaptive && (this.q.length >= this.cfg.STREAM.EMERGENCY_COALESCE_LEN);

      // Adaptive per-frame budget: increase throughput if queue is long
      const basePerFrame = this.cfg.STREAM.MAX_PER_FRAME | 0;
      const perFrame = adaptive ? Math.min(basePerFrame + Math.floor(this.q.length / 20), basePerFrame * 4) : basePerFrame;

      this.batching = true;
      while (this.q.length && processed < perFrame) {
        let { name_header, chunk } = this.q.shift();
        if (chunk && chunk.length > 0) {
          const chunks = [chunk];
          while (this.q.length) {
            const next = this.q[0];
            if (next.name_header === name_header) {
              chunks.push(next.chunk); this.q.shift();
              if (!coalesceAggressive) break;
            } else break;
          }
          chunk = chunks.join('');
        }
        this.engine.applyStream(name_header, chunk);
        processed++;
      }
      this.batching = false;
      if (this.needScroll) { this.scrollMgr.scheduleScroll(true); this.needScroll = false; }
      if (this.q.length) {
        this.drainScheduled = true;
        this.raf.schedule('SQ:drain', () => this.drain(), 'StreamQueue', 0);
      }
    }
    // Force a drain soon.
    kick() {
      if (this.q.length || this.drainScheduled) {
        this.drainScheduled = true;
        this.raf.schedule('SQ:drain', () => this.drain(), 'StreamQueue', 0);
      }
    }
    // Clear queued work and cancel scheduled drains.
    clear() {
      this.q.length = 0;
      try { this.raf.cancelGroup('StreamQueue'); } catch (_) {}
      this.drainScheduled = false;
    }
  }

  // ==========================================================================
  // 13) Bridge manager (QWebChannel)
  // ==========================================================================

  class BridgeManager {
    constructor(cfg, logger) {
      this.cfg = cfg; this.logger = logger || new Logger(cfg);
      this.bridge = null; this.connected = false;
    }
    // Low-level log via bridge if available.
    log(text) { try { if (this.bridge && this.bridge.log) this.bridge.log(text); } catch (_) {} }
    // Wire JS callbacks to QWebChannel signals.
    connect(onChunk, onNode, onNodeReplace, onNodeInput) {
      if (!this.bridge) return false; if (this.connected) return true;
      try {
        if (this.bridge.chunk) this.bridge.chunk.connect(onChunk);
        if (this.bridge.node) this.bridge.node.connect(onNode);
        if (this.bridge.nodeReplace) this.bridge.nodeReplace.connect(onNodeReplace);
        if (this.bridge.nodeInput) this.bridge.nodeInput.connect(onNodeInput);
        this.connected = true; return true;
      } catch (e) { this.log(e); return false; }
    }
    // Detach callbacks.
    disconnect() {
      if (!this.bridge) return false; if (!this.connected) return true;
      try {
        if (this.bridge.chunk) this.bridge.chunk.disconnect();
        if (this.bridge.node) this.bridge.node.disconnect();
        if (this.bridge.nodeReplace) this.bridge.nodeReplace.disconnect();
        if (this.bridge.nodeInput) this.bridge.nodeInput.disconnect();
      } catch (_) {}
      this.connected = false; return true;
    }
    // Initialize QWebChannel and notify Python side that JS is ready.
    initQWebChannel(pid, onReady) {
      try {
        new QWebChannel(qt.webChannelTransport, (channel) => {
          this.bridge = channel.objects.bridge;
          try { this.logger.bindBridge(this.bridge); } catch (_) {}
          onReady && onReady(this.bridge);
          if (this.bridge && this.bridge.js_ready) this.bridge.js_ready(pid);
        });
      } catch (e) { /* swallow: logger will flush when bridge arrives later */ }
    }
    // Convenience wrappers for host actions.
    copyCode(text) { if (this.bridge && this.bridge.copy_text) this.bridge.copy_text(text); }
    previewCode(text) { if (this.bridge && this.bridge.preview_text) this.bridge.preview_text(text); }
    runCode(text) { if (this.bridge && this.bridge.run_text) this.bridge.run_text(text); }
    updateScrollPosition(pos) { if (this.bridge && this.bridge.update_scroll_position) this.bridge.update_scroll_position(pos); }
  }

  // ==========================================================================
  // 14) Loading indicator
  // ==========================================================================

  class Loading {
    constructor(dom) { this.dom = dom; }
    // Show loader element (and hide tips if visible).
    show() { if (typeof window.hideTips === 'function') { window.hideTips(); } const el = this.dom.get('_loader_'); if (!el) return; if (el.classList.contains('hidden')) el.classList.remove('hidden'); el.classList.add('visible'); }
    // Hide loader element.
    hide() { const el = this.dom.get('_loader_'); if (!el) return; if (el.classList.contains('visible')) el.classList.remove('visible'); el.classList.add('hidden'); }
  }

  // ==========================================================================
  // 15) Event manager
  // ==========================================================================

  class EventManager {
    constructor(cfg, dom, scrollMgr, highlighter, codeScroll, toolOutput, bridge) {
      this.cfg = cfg; this.dom = dom; this.scrollMgr = scrollMgr; this.highlighter = highlighter;
      this.codeScroll = codeScroll; this.toolOutput = toolOutput; this.bridge = bridge;
      this.handlers = { wheel: null, scroll: null, resize: null, fabClick: null, mouseover: null, mouseout: null, click: null, keydown: null, docClickFocus: null, visibility: null, focus: null, pageshow: null };
    }
    _findWrapper(target) { if (!target || typeof target.closest !== 'function') return null; return target.closest('.code-wrapper'); }
    _getCodeEl(wrapper) { if (!wrapper) return null; return wrapper.querySelector('pre > code'); }
    _collectCodeText(codeEl) {
      if (!codeEl) return '';
      const frozen = codeEl.querySelector('.hl-frozen'); const tail = codeEl.querySelector('.hl-tail');
      if (frozen || tail) return (frozen?.textContent || '') + (tail?.textContent || '');
      return codeEl.textContent || '';
    }
    // Copy to clipboard via bridge if available, otherwise use browser APIs.
    async _copyTextRobust(text) {
      try { if (this.bridge && typeof this.bridge.copyCode === 'function') { this.bridge.copyCode(text); return true; } } catch (_) {}
      try { if (navigator && navigator.clipboard && navigator.clipboard.writeText) { await navigator.clipboard.writeText(text); return true; } } catch (_) {}
      try {
        const ta = document.createElement('textarea');
        ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.top = '-9999px'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select(); const ok = document.execCommand && document.execCommand('copy'); document.body.removeChild(ta); return !!ok;
      } catch (_) { return false; }
    }
    // Flash "Copied" feedback on the copy button.
    _flashCopied(btn, wrapper) {
      if (!btn || !wrapper) return;
      const span = btn.querySelector('span'); if (!span) return;
      const L_COPY = wrapper.getAttribute('data-locale-copy') || 'Copy';
      const L_COPIED = wrapper.getAttribute('data-locale-copied') || 'Copied';
      try { if (btn.__copyTimer) { clearTimeout(btn.__copyTimer); btn.__copyTimer = 0; } } catch (_) {}
      span.textContent = L_COPIED; btn.classList.add('copied');
      btn.__copyTimer = setTimeout(() => { try { span.textContent = L_COPY; btn.classList.remove('copied'); } catch (_) {} btn.__copyTimer = 0; }, 1200);
    }
    // Toggle code collapse/expand and remember collapsed indices.
    _toggleCollapse(wrapper) {
      if (!wrapper) return;
      const codeEl = this._getCodeEl(wrapper); if (!codeEl) return;
      const btn = wrapper.querySelector('.code-header-collapse');
      const span = btn ? btn.querySelector('span') : null;
      const L_COLLAPSE = wrapper.getAttribute('data-locale-collapse') || 'Collapse';
      const L_EXPAND = wrapper.getAttribute('data-locale-expand') || 'Expand';
      const idx = String(wrapper.getAttribute('data-index') || '');
      const arr = window.__collapsed_idx || (window.__collapsed_idx = []);
      const isHidden = (codeEl.style.display === 'none');

      if (isHidden) {
        codeEl.style.display = 'block';
        if (span) span.textContent = L_COLLAPSE;
        const p = arr.indexOf(idx); if (p !== -1) arr.splice(p, 1);
      } else {
        codeEl.style.display = 'none';
        if (span) span.textContent = L_EXPAND;
        if (!arr.includes(idx)) arr.push(idx);
      }
    }
    // Attach global UI event handlers and container-level interactions.
    install() {
      try { history.scrollRestoration = "manual"; } catch (_) {}

      this.handlers.keydown = (event) => {
        if (event.ctrlKey && event.key === 'f') { window.location.href = 'bridge://open_find:' + runtime.cfg.PID; event.preventDefault(); }
        if (event.key === 'Escape') { window.location.href = 'bridge://escape'; event.preventDefault(); }
      };
      document.addEventListener('keydown', this.handlers.keydown, { passive: false });

      // Removed global click-to-focus navigation and visibility/focus wakeups to keep the pump rAF-only and click-agnostic.

      const container = this.dom.get('container');
      const addClassToMsg = (id, className) => { const el = document.getElementById('msg-bot-' + id); if (el) el.classList.add(className); };
      const removeClassFromMsg = (id, className) => { const el = document.getElementById('msg-bot-' + id); if (el) el.classList.remove(className); };

      this.handlers.mouseover = (event) => { if (event.target.classList.contains('action-img')) { const id = event.target.getAttribute('data-id'); addClassToMsg(id, 'msg-highlight'); } };
      this.handlers.mouseout = (event) => { if (event.target.classList.contains('action-img')) { const id = event.target.getAttribute('data-id'); const el = document.getElementById('msg-bot-' + id); if (el) el.classList.remove('msg-highlight'); } };
      if (container) {
        container.addEventListener('mouseover', this.handlers.mouseover, { passive: true });
        container.addEventListener('mouseout', this.handlers.mouseout, { passive: true });
      }

      this.handlers.click = async (ev) => {
        const a = ev.target && (ev.target.closest ? ev.target.closest('a.code-header-action') : null);
        if (!a) return;
        const wrapper = this._findWrapper(a);
        if (!wrapper) return;

        ev.preventDefault();
        ev.stopPropagation();

        const isCopy = a.classList.contains('code-header-copy');
        const isCollapse = a.classList.contains('code-header-collapse');
        const isRun = a.classList.contains('code-header-run');
        const isPreview = a.classList.contains('code-header-preview');

        let codeEl = null, text = '';
        if (isCopy || isRun || isPreview) {
          codeEl = this._getCodeEl(wrapper);
          text = this._collectCodeText(codeEl);
        }

        try {
          if (isCopy) {
            const ok = await this._copyTextRobust(text);
            if (ok) this._flashCopied(a, wrapper);
          } else if (isCollapse) {
            this._toggleCollapse(wrapper);
          } else if (isRun) {
            if (this.bridge && typeof this.bridge.runCode === 'function') this.bridge.runCode(text);
          } else if (isPreview) {
            if (this.bridge && typeof this.bridge.previewCode === 'function') this.bridge.previewCode(text);
          }
        } catch (_) { /* swallow */ }
      };
      if (container) container.addEventListener('click', this.handlers.click, { passive: false });

      this.handlers.wheel = (ev) => {
        runtime.scrollMgr.userInteracted = true;
        if (ev.deltaY < 0) runtime.scrollMgr.autoFollow = false;
        else runtime.scrollMgr.maybeEnableAutoFollowByProximity();
        this.highlighter.scheduleScanVisibleCodes(runtime.stream.activeCode);
      };
      document.addEventListener('wheel', this.handlers.wheel, { passive: true });

      this.handlers.scroll = () => {
        const el = Utils.SE; const top = el.scrollTop;
        if (top + 1 < runtime.scrollMgr.lastScrollTop) runtime.scrollMgr.autoFollow = false;
        runtime.scrollMgr.maybeEnableAutoFollowByProximity();
        runtime.scrollMgr.lastScrollTop = top;
        const action = runtime.scrollMgr.computeFabAction();
        if (action !== runtime.scrollMgr.currentFabAction) runtime.scrollMgr.updateScrollFab(false, action, true);
        this.highlighter.scheduleScanVisibleCodes(runtime.stream.activeCode);
      };
      window.addEventListener('scroll', this.handlers.scroll, { passive: true });

      const fab = this.dom.get('scrollFab');
      if (fab) {
        this.handlers.fabClick = (ev) => {
          ev.preventDefault(); ev.stopPropagation();
          const action = runtime.scrollMgr.computeFabAction();
          if (action === 'up') runtime.scrollMgr.scrollToTopUser();
          else if (action === 'down') runtime.scrollMgr.scrollToBottomUser();
          runtime.scrollMgr.fabFreezeUntil = Utils.now() + this.cfg.FAB.TOGGLE_DEBOUNCE_MS;
          runtime.scrollMgr.updateScrollFab(true);
        };
        fab.addEventListener('click', this.handlers.fabClick, { passive: false });
      }

      this.handlers.resize = () => {
        runtime.scrollMgr.maybeEnableAutoFollowByProximity();
        runtime.scrollMgr.scheduleScrollFabUpdate();
        this.highlighter.scheduleScanVisibleCodes(runtime.stream.activeCode);
      };
      window.addEventListener('resize', this.handlers.resize, { passive: true });

      // Note: visibility/focus/pageshow kickers removed intentionally.
    }
    // Detach all installed handlers and reset local refs.
    cleanup() {
      const container = this.dom.get('container');
      if (this.handlers.wheel) document.removeEventListener('wheel', this.handlers.wheel);
      if (this.handlers.scroll) window.removeEventListener('scroll', this.handlers.scroll);
      if (this.handlers.resize) window.removeEventListener('resize', this.handlers.resize);
      const fab = this.dom.get('scrollFab'); if (fab && this.handlers.fabClick) fab.removeEventListener('click', this.handlers.fabClick);
      if (container && this.handlers.mouseover) container.removeEventListener('mouseover', this.handlers.mouseover);
      if (container && this.handlers.mouseout) container.removeEventListener('mouseout', this.handlers.mouseout);
      if (container && this.handlers.click) container.removeEventListener('click', this.handlers.click);
      if (this.handlers.keydown) document.removeEventListener('keydown', this.handlers.keydown);
      if (this.handlers.docClickFocus) document.removeEventListener('click', this.handlers.docClickFocus);
      if (this.handlers.visibility) document.removeEventListener('visibilitychange', this.handlers.visibility);
      if (this.handlers.focus) window.removeEventListener('focus', this.handlers.focus);
      if (this.handlers.pageshow) window.removeEventListener('pageshow', this.handlers.pageshow);
      this.handlers = {};
    }
  }

  // ==========================================================================
  // 16) Orchestrator runtime
  // ==========================================================================

  class Runtime {
    constructor() {
      this.cfg = new Config();
      this.logger = new Logger(this.cfg);

      this.dom = new DOMRefs();
      this.customMarkup = new CustomMarkup(this.cfg, this.logger);
      this.raf = new RafManager(this.cfg);

      // Ensure logger uses central RafManager for its internal tick pump.
      try { this.logger.bindRaf(this.raf); } catch (_) {}

      this.async = new AsyncRunner(this.cfg, this.raf);
      this.renderer = new MarkdownRenderer(this.cfg, this.customMarkup, this.logger, this.async, this.raf);

      this.math = new MathRenderer(this.cfg, this.raf, this.async);
      this.codeScroll = new CodeScrollState(this.cfg, this.raf);
      this.highlighter = new Highlighter(this.cfg, this.codeScroll, this.raf);
      this.scrollMgr = new ScrollManager(this.cfg, this.dom, this.raf);
      this.toolOutput = new ToolOutput();
      this.loading = new Loading(this.dom);
      this.nodes = new NodesManager(this.dom, this.renderer, this.highlighter, this.math);
      this.bridge = new BridgeManager(this.cfg, this.logger);
      this.ui = new UIManager();
      this.stream = new StreamEngine(this.cfg, this.dom, this.renderer, this.math, this.highlighter, this.codeScroll, this.scrollMgr, this.raf, this.async, this.logger);
      this.streamQ = new StreamQueue(this.cfg, this.stream, this.scrollMgr, this.raf);
      this.events = new EventManager(this.cfg, this.dom, this.scrollMgr, this.highlighter, this.codeScroll, this.toolOutput, this.bridge);

      this.tips = null;
      this._lastHeavyResetMs = 0;

      // Bridge hooks between renderer and other subsystems.
      this.renderer.hooks.observeNewCode = (root, opts) => this.highlighter.observeNewCode(root, opts, this.stream.activeCode);
      this.renderer.hooks.observeMsgBoxes = (root) => this.highlighter.observeMsgBoxes(root, (box) => {
        this.highlighter.observeNewCode(box, {
          deferLastIfStreaming: true,
          minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
          minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
        }, this.stream.activeCode);
        this.codeScroll.initScrollableBlocks(box);
      });
      this.renderer.hooks.scheduleMathRender = (root) => {
        const mm = getMathMode();
        if (mm === 'idle') this.math.schedule(root);
        else if (mm === 'always') this.math.schedule(root, 0, true);
      };
      this.renderer.hooks.codeScrollInit = (root) => this.codeScroll.initScrollableBlocks(root);
    }
    // Reset stream state and optionally perform a heavy reset of schedulers and observers.
    resetStreamState(origin, opts) {
      try { this.streamQ.clear(); } catch (_) {}

      const def = Object.assign({
        finalizeActive: true, clearBuffer: true, clearMsg: false, defuseOrphans: true, forceHeavy: false, reason: String(origin || 'external-op')
      }, (opts || {}));

      const now = Utils.now();
      const withinDebounce = (now - (this._lastHeavyResetMs || 0)) <= (this.cfg.RESET.HEAVY_DEBOUNCE_MS || 24);
      const mustHeavyByOrigin =
        def.forceHeavy === true || def.clearMsg === true ||
        origin === 'beginStream' || origin === 'nextStream' ||
        origin === 'clearStream' || origin === 'replaceNodes' ||
        origin === 'clearNodes' || origin === 'clearOutput' ||
        origin === 'clearLive' || origin === 'clearInput';
      const shouldHeavy = mustHeavyByOrigin || !withinDebounce;
      const suppressLog = withinDebounce && origin !== 'beginStream';

      try { this.stream.abortAndReset({ ...def, suppressLog }); } catch (_) {}

      if (shouldHeavy) {
        try { this.highlighter.cleanup(); } catch (_) {}
        try { this.math.cleanup(); } catch (_) {}
        try { this.codeScroll.cancelAllScrolls(); } catch (_) {}
        try { this.scrollMgr.cancelPendingScroll(); } catch (_) {}
        try { this.raf.cancelAll(); } catch (_) {}
        this._lastHeavyResetMs = now;
      } else {
        try { this.raf.cancelGroup('StreamQueue'); } catch (_) {}
      }

      try { this.tips && this.tips.hide(); } catch (_) {}
    }
    // API: begin stream.
    api_beginStream = (chunk = false) => { this.tips && this.tips.hide(); this.resetStreamState('beginStream', { clearMsg: true, finalizeActive: false, forceHeavy: true }); this.stream.beginStream(chunk); };
    // API: end stream.
    api_endStream = () => { this.stream.endStream(); };
    // API: apply chunk.
    api_applyStream = (name, chunk) => { this.stream.applyStream(name, chunk); };
    // API: enqueue chunk (drained on rAF).
    api_appendStream = (name, chunk) => { this.streamQ.enqueue(name, chunk); };
    // API: move current output to "before" area and prepare for next stream.
    api_nextStream = () => {
      this.tips && this.tips.hide();
      const element = this.dom.get('_append_output_'); const before = this.dom.get('_append_output_before_');
      if (element && before) {
        const frag = document.createDocumentFragment();
        while (element.firstChild) frag.appendChild(element.firstChild);
        before.appendChild(frag);
      }
      this.resetStreamState('nextStream', { clearMsg: true, finalizeActive: false, forceHeavy: true });
      this.scrollMgr.scheduleScroll();
    };
    // API: clear streaming output area entirely.
    api_clearStream = () => { this.tips && this.tips.hide(); this.resetStreamState('clearStream', { clearMsg: true, forceHeavy: true }); const el = this.dom.getStreamContainer(); if (!el) return; el.replaceChildren(); };

    // API: append rendered nodes (messages).
    api_appendNode = (html) => { this.resetStreamState('appendNode'); this.nodes.appendNode(html, this.scrollMgr); };
    // API: replace messages list.
    api_replaceNodes = (html) => { this.resetStreamState('replaceNodes', { clearMsg: true, forceHeavy: true }); this.dom.clearNodes(); this.nodes.replaceNodes(html, this.scrollMgr); };
    // API: append to input area.
    api_appendToInput = (html) => { this.nodes.appendToInput(html); this.scrollMgr.userInteracted = false; this.scrollMgr.scheduleScroll(); this.resetStreamState('appendToInput'); };

    // API: clear messages list.
    api_clearNodes = () => { this.dom.clearNodes(); this.resetStreamState('clearNodes', { clearMsg: true, forceHeavy: true }); };
    // API: clear input area.
    api_clearInput = () => { this.resetStreamState('clearInput', { forceHeavy: true }); this.dom.clearInput(); };
    // API: clear output area.
    api_clearOutput = () => { this.dom.clearOutput(); this.resetStreamState('clearOutput', { clearMsg: true, forceHeavy: true }); };
    // API: clear live area.
    api_clearLive = () => { this.dom.clearLive(); this.resetStreamState('clearLive', { forceHeavy: true }); };

    // API: tool output helpers.
    api_appendToolOutput = (c) => this.toolOutput.append(c);
    api_updateToolOutput = (c) => this.toolOutput.update(c);
    api_clearToolOutput = () => this.toolOutput.clear();
    api_beginToolOutput = () => this.toolOutput.begin();
    api_endToolOutput = () => this.toolOutput.end();
    api_enableToolOutput = () => this.toolOutput.enable();
    api_disableToolOutput = () => this.toolOutput.disable();
    api_toggleToolOutput = (id) => this.toolOutput.toggle(id);

    // API: append extra content to a bot message.
    api_appendExtra = (id, c) => this.nodes.appendExtra(id, c, this.scrollMgr);
    // API: remove one message by id.
    api_removeNode = (id) => this.nodes.removeNode(id, this.scrollMgr);
    // API: remove all messages starting from id.
    api_removeNodesFromId = (id) => this.nodes.removeNodesFromId(id, this.scrollMgr);

    // API: replace live area content (with local post-processing).
    api_replaceLive = (content) => {
      const el = this.dom.get('_append_live_'); if (!el) return;
      if (el.classList.contains('hidden')) { el.classList.remove('hidden'); el.classList.add('visible'); }
      el.innerHTML = content;

      try {
        const maybePromise = this.renderer.renderPendingMarkdown(el);

        const post = () => {
          try {
            this.highlighter.observeNewCode(el, {
              deferLastIfStreaming: true,
              minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
              minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
            }, this.stream.activeCode);

            this.highlighter.observeMsgBoxes(el, (box) => {
              this.highlighter.observeNewCode(box, {
                deferLastIfStreaming: true,
                minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
                minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
              }, this.stream.activeCode);
              this.codeScroll.initScrollableBlocks(box);
            });
          } catch (_) {}

          try {
            const mm = getMathMode();
            // In finalize-only we must force now; otherwise normal schedule is fine.
            if (mm === 'finalize-only') this.math.schedule(el, 0, true);
            else this.math.schedule(el);
          } catch (_) {}

          this.scrollMgr.scheduleScroll();
        };

        if (maybePromise && typeof maybePromise.then === 'function') {
          maybePromise.then(post);
        } else {
          post();
        }
      } catch (_) {
        // Worst-case: keep UX responsive even if something throws before post-processing
        this.scrollMgr.scheduleScroll();
      }
    };

    // API: update footer content.
    api_updateFooter = (html) => { const el = this.dom.get('_footer_'); if (el) el.innerHTML = html; };

    // API: toggle UI features.
    api_enableEditIcons = () => this.ui.enableEditIcons();
    api_disableEditIcons = () => this.ui.disableEditIcons();
    api_enableTimestamp = () => this.ui.enableTimestamp();
    api_disableTimestamp = () => this.ui.disableTimestamp();
    api_enableBlocks = () => this.ui.enableBlocks();
    api_disableBlocks = () => this.ui.disableBlocks();
    api_updateCSS = (styles) => this.ui.updateCSS(styles);

    // API: sync scroll position with host.
    api_getScrollPosition = () => { this.bridge.updateScrollPosition(window.scrollY); };
    api_setScrollPosition = (pos) => { try { window.scrollTo(0, pos); this.scrollMgr.prevScroll = parseInt(pos); } catch (_) {} };

    // API: show/hide loading overlay.
    api_showLoading = () => this.loading.show();
    api_hideLoading = () => this.loading.hide();

    // API: restore collapsed state of codes in a given root.
    api_restoreCollapsedCode = (root) => this.renderer.restoreCollapsedCode(root);
    // API: user-triggered page scroll.
    api_scrollToTopUser = () => this.scrollMgr.scrollToTopUser();
    api_scrollToBottomUser = () => this.scrollMgr.scrollToBottomUser();

    // API: tips visibility control.
    api_showTips = () => this.tips.show();
    api_hideTips = () => this.tips.hide();

    // API: custom markup rules control.
    api_getCustomMarkupRules = () => this.customMarkup.getRules();
    api_setCustomMarkupRules = (rules) => { this.customMarkup.setRules(rules); };

    // Initialize runtime (called on DOMContentLoaded).
    init() {
      this.highlighter.initHLJS();
      this.dom.init();
      this.ui.ensureStickyHeaderStyle();

      // Tips manager with rAF-based centering and rotation
      this.tips = new TipsManager(this.dom);

      this.events.install();

      this.bridge.initQWebChannel(this.cfg.PID, (bridge) => {
        const onChunk = (name, chunk) => this.api_appendStream(name, chunk);
        const onNode = (html) => this.api_appendNode(html);
        const onNodeReplace = (html) => this.api_replaceNodes(html);
        const onNodeInput = (html) => this.api_appendToInput(html);
        this.bridge.connect(onChunk, onNode, onNodeReplace, onNodeInput);
        try { this.logger.bindBridge(this.bridge.bridge || this.bridge); } catch (_) {}
      });

      this.renderer.init();
      try { this.renderer.renderPendingMarkdown(document); } catch (_) {}

      this.highlighter.observeMsgBoxes(document, (box) => {
        this.highlighter.observeNewCode(box, {
          deferLastIfStreaming: true,
          minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
          minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
        }, this.stream.activeCode);
        this.codeScroll.initScrollableBlocks(box);
      });
      this.highlighter.observeNewCode(document, {
        deferLastIfStreaming: true,
        minLinesForLast: this.cfg.PROFILE_CODE.minLinesForHL,
        minCharsForLast: this.cfg.PROFILE_CODE.minCharsForHL
      }, this.stream.activeCode);
      this.highlighter.scheduleScanVisibleCodes(this.stream.activeCode);

      // Start tips rotation; internal delay matches legacy timing (TIPS_INIT_DELAY_MS)
      this.tips.cycle();
      this.scrollMgr.updateScrollFab(true);
    }

    // Cleanup runtime and detach from DOM/bridge.
    cleanup() {
      this.tips.cleanup();
      try { this.bridge.disconnect(); } catch (_) {}
      this.events.cleanup();
      this.highlighter.cleanup();
      this.math.cleanup();
      this.streamQ.clear();
      this.dom.cleanup();
    }
  }

  // Ensure RafManager.cancel uses the correct group key cleanup.
  if (typeof RafManager !== 'undefined' && RafManager.prototype && typeof RafManager.prototype.cancel === 'function') {
    RafManager.prototype.cancel = function(key) {
      const t = this.tasks.get(key);
      if (!t) return;
      this.tasks.delete(key);
      if (t.group) {
        const set = this.groups.get(t.group);
        if (set) { set.delete(key); if (set.size === 0) this.groups.delete(t.group); }
      }
    };
  }

  const runtime = new Runtime();

  document.addEventListener('DOMContentLoaded', () => runtime.init());

  Object.defineProperty(window, 'SE', { get() { return Utils.SE; } });

  window.beginStream = (chunk) => runtime.api_beginStream(chunk);
  window.endStream = () => runtime.api_endStream();
  window.applyStream = (name, chunk) => runtime.api_applyStream(name, chunk);
  window.appendStream = (name, chunk) => runtime.api_appendStream(name, chunk);
  window.nextStream = () => runtime.api_nextStream();
  window.clearStream = () => runtime.api_clearStream();

  window.appendNode = (html) => runtime.api_appendNode(html);
  window.replaceNodes = (html) => runtime.api_replaceNodes(html);
  window.appendToInput = (html) => runtime.api_appendToInput(html);

  window.clearNodes = () => runtime.api_clearNodes();
  window.clearInput = () => runtime.api_clearInput();
  window.clearOutput = () => runtime.api_clearOutput();
  window.clearLive = () => runtime.api_clearLive();

  window.appendToolOutput = (c) => runtime.api_appendToolOutput(c);
  window.updateToolOutput = (c) => runtime.api_updateToolOutput(c);
  window.clearToolOutput = () => runtime.api_clearToolOutput();
  window.beginToolOutput = () => runtime.api_beginToolOutput();
  window.endToolOutput = () => runtime.api_endToolOutput();
  window.enableToolOutput = () => runtime.api_enableToolOutput();
  window.disableToolOutput = () => runtime.api_disableToolOutput();
  window.toggleToolOutput = (id) => runtime.api_toggleToolOutput(id);

  window.appendExtra = (id, c) => runtime.api_appendExtra(id, c);
  window.removeNode = (id) => runtime.api_removeNode(id);
  window.removeNodesFromId = (id) => runtime.api_removeNodesFromId(id);

  window.replaceLive = (c) => runtime.api_replaceLive(c);
  window.updateFooter = (c) => runtime.api_updateFooter(c);

  window.enableEditIcons = () => runtime.api_enableEditIcons();
  window.disableEditIcons = () => runtime.api_disableEditIcons();
  window.enableTimestamp = () => runtime.api_enableTimestamp();
  window.disableTimestamp = () => runtime.api_disableTimestamp();
  window.enableBlocks = () => runtime.api_enableBlocks();
  window.disableBlocks = () => runtime.api_disableBlocks();
  window.updateCSS = (s) => runtime.api_updateCSS(s);

  window.getScrollPosition = () => runtime.api_getScrollPosition();
  window.setScrollPosition = (pos) => runtime.api_setScrollPosition(pos);

  window.showLoading = () => runtime.api_showLoading();
  window.hideLoading = () => runtime.api_hideLoading();

  window.restoreCollapsedCode = (root) => runtime.api_restoreCollapsedCode(root);
  window.scrollToTopUser = () => runtime.api_scrollToTopUser();
  window.scrollToBottomUser = () => runtime.api_scrollToBottomUser();

  window.showTips = () => runtime.api_showTips();
  window.hideTips = () => runtime.api_hideTips();

  window.getCustomMarkupRules = () => runtime.api_getCustomMarkupRules();
  window.setCustomMarkupRules = (rules) => runtime.api_setCustomMarkupRules(rules);

  window.__pygpt_cleanup = () => runtime.cleanup();

})();