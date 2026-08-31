/* ==========================================================================
   Pepper draft site — REVIEW MODE
   --------------------------------------------------------------------------
   Beau, 31 Aug: "what's the best way to have Darren help mark up this site?
   Can we make it so he can put pins throughout and add comments? It's too hard
   to note this all down."

   So: click anywhere in review mode to drop a numbered pin and type a note.
   Pins persist per page, survive reloads, and "Copy all feedback" puts every
   comment across every page on the clipboard in one go — ready to paste into
   an email.

   WHY IT WORKS THIS WAY
   The draft is static hosting (GitHub Pages), so there is no server to post
   comments to. Notes live in the reviewer's own browser (localStorage) until
   they hit Copy or Email. That means:
     · no account, no login, no tool for Darren to learn — the thing that
       actually kills review loops;
     · but the notes are on HIS machine until he sends them. The panel says so
       plainly, and nags with an unsent count, because a silent loss of an
       hour's feedback would be much worse than a bit of nagging.

   Pins anchor to an element, not to page coordinates: we store a structural
   selector plus the offset as a percentage inside that element, so a pin stays
   on the thing it was pointing at when the page reflows on a different screen.

   Nothing here ships to the real site — it is review scaffolding for the draft
   only, and is excluded when these pages are rebuilt in Elementor.
   ========================================================================== */
(function () {
  "use strict";

  var KEY = "pepper-review-v1";
  var MAILTO = "bblake@pepperproductions.com.au";

  /* =====================================================================
     LIVE SYNC — where Darren's notes go
     ---------------------------------------------------------------------
     Beau, 31 Aug: "I want him to be able to look over this in his own time
     and make required comments and not have to send them to me."

     Paste an endpoint below and every note posts itself the moment it is
     written. Darren does nothing; Beau watches them arrive.

     MODE "appsscript"  (recommended — see apps-script.gs in this folder)
       A Google Apps Script web app bound to a Sheet Beau owns. No third
       party, no submission cap, no account for Darren, and the Sheet
       updates live. Posts go as text/plain on purpose: an application/json
       body triggers a CORS preflight that Apps Script does not answer, and
       the request dies before it arrives. text/plain is a "simple request",
       so no preflight happens. This is the single most common reason an
       Apps Script endpoint appears to silently fail.

     MODE "json"  (Web3Forms / Formspree / Basin)
       Standard JSON POST. Easier signup, but the free tiers cap monthly
       submissions and a thorough review can produce a lot of notes.

     WHY NOT GITHUB DIRECTLY: this is static hosting, so writing to the repo
     would mean shipping a token in a public file. GitHub's secret scanning
     revokes those within minutes, so it would break as fast as it shipped.
     ===================================================================== */
  var ENDPOINT = "";              // <— paste the web app / form URL here
  var ENDPOINT_MODE = "appsscript";   // "appsscript" | "json"

  var page = location.pathname.split("/").pop() || "index.html";

  /* ---------- storage ------------------------------------------------- */
  function loadAll() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
    catch (e) { return {}; }
  }
  function saveAll(d) {
    try { localStorage.setItem(KEY, JSON.stringify(d)); }
    catch (e) { alert("Couldn't save that note — the browser is blocking storage.\n\nCopy your feedback out now so you don't lose it."); }
  }
  function notes() { return (loadAll()[page] || []); }

  /* Outbound queue. A note is written to localStorage first and only cleared
     from the queue once the server has taken it, so a dropped connection, a
     closed laptop or a sleeping endpoint costs nothing — the next page load
     flushes whatever is still pending. Without this, "it sends automatically"
     quietly becomes "it sent, except the ones that didn't". */
  var QKEY = "pepper-review-queue-v1";
  function queue() {
    try { return JSON.parse(localStorage.getItem(QKEY)) || []; } catch (e) { return []; }
  }
  function setQueue(q) {
    try { localStorage.setItem(QKEY, JSON.stringify(q)); } catch (e) {}
  }
  function push(note) {
    if (!ENDPOINT) { renderPanel(); return; }
    var q = queue();
    q.push({ page: page, kind: note.kind || "pin", note: note.text,
             before: note.before || "", after: note.after || "",
             where: note.sel, at: note.ts, site: location.href });
    setQueue(q);
    flush();
  }
  var flushing = false, sentState = null;
  function flush() {
    if (!ENDPOINT || flushing) return;
    var q = queue();
    if (!q.length) { sentState = true; renderPanel(); return; }
    flushing = true;
    var item = q[0];
    var opts = ENDPOINT_MODE === "appsscript"
      ? { method: "POST", headers: { "Content-Type": "text/plain;charset=utf-8" },
          body: JSON.stringify(item) }
      : { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(item) };
    fetch(ENDPOINT, opts).then(function (r) {
      flushing = false;
      if (r.ok) {
        var cur = queue(); cur.shift(); setQueue(cur);
        sentState = true; renderPanel();
        if (cur.length) flush();
      } else { sentState = false; renderPanel(); }
    }, function () { flushing = false; sentState = false; renderPanel(); });
  }
  function pending() { return queue().length; }

  function setNotes(list) { var d = loadAll(); d[page] = list; saveAll(d); }
  function totalAll() {
    var d = loadAll(), n = 0;
    for (var k in d) if (Object.prototype.hasOwnProperty.call(d, k)) n += d[k].length;
    return n;
  }

  /* ---------- anchoring ------------------------------------------------ */
  function selectorFor(el) {
    var parts = [];
    while (el && el.nodeType === 1 && el !== document.body && parts.length < 6) {
      var p = el.parentNode, i = 1, sib = el;
      while ((sib = sib.previousElementSibling)) {
        if (sib.tagName === el.tagName) i++;
      }
      parts.unshift(el.tagName.toLowerCase() + ":nth-of-type(" + i + ")");
      el = p;
    }
    return parts.join(">");
  }
  function resolve(sel) {
    try { return document.body.querySelector(sel); } catch (e) { return null; }
  }

  /* ---------- state ---------------------------------------------------- */
  var on = false, mode = "pin", layer, panel, fab, badge, bMode;

  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = txt;
    return n;
  }

  /* ---------- text edits ----------------------------------------------- */
  var EDITABLE = "h1,h2,h3,p,li,.lbl,.stand,.big,.cap,.tag,.v,.k,blockquote";

  /* Paint saved rewrites back into the page so Darren sees his own version on
     return, not the original. Note this sets textContent, so a two-tone
     heading (black + grey halves) goes flat once it has been rewritten — the
     colour split lives in a child <span> that free-text editing can't preserve.
     Acceptable on a review draft; the recorded before/after is what matters. */
  function applyEdits() {
    notes().forEach(function (n) {
      if (n.kind !== "edit") return;
      var t = resolve(n.sel);
      if (!t) return;
      if (t.textContent.trim() !== n.after.trim()) t.textContent = n.after;
      t.classList.add("pr-edited");
      t.title = "Was: " + n.before;
    });
  }

  function beginEdit(t) {
    if (t.isContentEditable) return;
    var before = t.textContent.trim();
    var prior = notes().filter(function (n) {
      return n.kind === "edit" && n.sel === selectorFor(t);
    })[0];
    t.contentEditable = "true";
    t.classList.add("pr-editing");
    t.focus();
    function finish() {
      t.contentEditable = "false";
      t.classList.remove("pr-editing");
      t.removeEventListener("blur", finish);
      var after = t.textContent.trim();
      if (!after) { t.textContent = before; return; }
      if (after === before) return;
      var list = notes();
      var sel = selectorFor(t);
      var existing = list.filter(function (n) { return n.kind === "edit" && n.sel === sel; })[0];
      if (existing) {
        existing.after = after;
      } else {
        var rec = { kind: "edit", sel: sel,
                    before: (prior ? prior.before : before), after: after,
                    text: "", ts: new Date().toISOString() };
        rec.text = "TEXT: “" + rec.before + "” → “" + after + "”";
        list.push(rec);
        push(rec);
      }
      setNotes(list);
      t.classList.add("pr-edited");
      render();
    }
    t.addEventListener("blur", finish);
    t.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); t.blur(); }
      if (e.key === "Escape") { t.textContent = before; t.blur(); }
    });
  }

  /* ---------- rendering ------------------------------------------------ */
  function render() {
    layer.innerHTML = "";
    applyEdits();
    var list = notes();
    list.forEach(function (n, i) {
      if (n.kind === "edit") return;           // edits show in the text itself
      var host = resolve(n.sel);
      if (!host) return;                       // section changed since the note
      var r = host.getBoundingClientRect();
      var pin = el("button", "pr-pin", String(i + 1));
      pin.style.left = (r.left + window.scrollX + r.width * n.rx) + "px";
      pin.style.top = (r.top + window.scrollY + r.height * n.ry) + "px";
      pin.title = n.text;
      pin.addEventListener("click", function (ev) {
        ev.stopPropagation();
        openNote(i);
      });
      layer.appendChild(pin);
    });
    renderPanel();
  }

  function renderPanel() {
    var list = notes(), body = panel.querySelector(".pr-list");
    body.innerHTML = "";
    if (!list.length) {
      body.appendChild(el("p", "pr-empty",
        "Nothing on this page yet. In review mode: Pins drops a marker anywhere, Text lets you rewrite a heading or paragraph in place."));
    }
    list.forEach(function (n, i) {
      var row = el("div", "pr-row");
      var isEdit = n.kind === "edit";
      var num = el("span", "pr-num" + (isEdit ? " edit" : ""), isEdit ? "✎" : String(i + 1));
      var txt = el("div", "pr-txt");
      if (isEdit) {
        var was = el("span", "pr-was", n.before);
        var now = el("span", "pr-now", n.after);
        txt.appendChild(was); txt.appendChild(now);
      } else {
        txt.textContent = n.text;
      }
      var del = el("button", "pr-del", "×");
      del.title = "Delete this note";
      del.addEventListener("click", function () {
        var l = notes();
        if (l[i].kind === "edit") {
          var t = resolve(l[i].sel);
          if (t) { t.textContent = l[i].before; t.classList.remove("pr-edited"); t.title = ""; }
        }
        l.splice(i, 1); setNotes(l); render();
      });
      row.appendChild(num); row.appendChild(txt); row.appendChild(del);
      row.addEventListener("click", function (e) {
        if (e.target === del) return;
        var host = resolve(n.sel);
        if (host) host.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      body.appendChild(row);
    });
    var t = totalAll();
    panel.querySelector(".pr-count").textContent =
      list.length + " on this page · " + t + " in total";
    var note = panel.querySelector(".pr-note");
    if (note) {
      if (ENDPOINT && pending() === 0 && t) {
        note.textContent = "✓ Sent to Beau automatically — nothing for you to do.";
        note.style.color = "#3F6B5E";
      } else if (ENDPOINT && pending() > 0) {
        note.textContent = pending() + " note(s) still to send. They'll go automatically when the connection is back — leave the tab open a moment.";
        note.style.color = "#8C4A32";
      } else if (t) {
        note.textContent = "⚠ These " + t + " notes are saved in THIS browser only. Beau cannot see them until you hit Copy all or Email to Beau.";
        note.style.color = "#8C4A32";
      }
    }
    badge.textContent = t ? String(t) : "";
    badge.style.display = t ? "grid" : "none";
  }

  function openNote(i) {
    var list = notes();
    if (list[i].kind === "edit") { return; }
    var v = prompt("Edit this note (clear the box to delete it):", list[i].text);
    if (v === null) return;
    if (!v.trim()) list.splice(i, 1); else list[i].text = v.trim();
    setNotes(list); render();
  }

  /* ---------- adding --------------------------------------------------- */
  function onClick(e) {
    if (!on) return;
    if (e.target.closest(".pr-ui")) return;             // our own chrome
    if (e.target.isContentEditable) return;             // typing, not clicking
    e.preventDefault();
    e.stopPropagation();
    if (mode === "text") {
      var t = e.target.closest(EDITABLE);
      if (t && !t.closest(".pr-ui")) beginEdit(t);
      return;
    }
    var host = e.target.closest("section, .fcontact, .bar") || document.body;
    var r = host.getBoundingClientRect();
    var txt = prompt("What's the note here?");
    if (!txt || !txt.trim()) return;
    var list = notes();
    list.push({
      sel: selectorFor(host),
      rx: (e.clientX - r.left) / Math.max(r.width, 1),
      ry: (e.clientY - r.top) / Math.max(r.height, 1),
      text: txt.trim(),
      ts: new Date().toISOString()
    });
    setNotes(list);
    push(list[list.length - 1]);
    render();
  }

  /* ---------- export --------------------------------------------------- */
  function asText() {
    var d = loadAll(), out = ["PEPPER DRAFT SITE — REVIEW NOTES",
      new Date().toLocaleString(), ""];
    Object.keys(d).sort().forEach(function (p) {
      if (!d[p].length) return;
      out.push("── " + p + " ──");
      var pins = d[p].filter(function (n) { return n.kind !== "edit"; });
      var eds = d[p].filter(function (n) { return n.kind === "edit"; });
      pins.forEach(function (n, i) { out.push((i + 1) + ". " + n.text); });
      if (eds.length) {
        out.push(pins.length ? "" : null);
        out.push("  Text rewrites:");
        eds.forEach(function (n) {
          out.push("   WAS: " + n.before);
          out.push("   NOW: " + n.after);
          out.push("");
        });
      }
      out.push("");
    });
    return out.filter(function (l) { return l !== null; }).join("\n");
  }
  function copyAll() {
    var t = asText();
    if (totalAll() === 0) { alert("No notes to copy yet."); return; }
    navigator.clipboard.writeText(t).then(function () {
      alert("All feedback copied.\n\nPaste it into an email to Beau.");
    }, function () {
      prompt("Copy this and send it to Beau:", t);
    });
  }
  function emailAll() {
    if (totalAll() === 0) { alert("No notes to send yet."); return; }
    var body = encodeURIComponent(asText());
    if (body.length > 1800) {
      copyAll();
      return;
    }
    location.href = "mailto:" + MAILTO +
      "?subject=" + encodeURIComponent("Pepper draft site — review notes") +
      "&body=" + body;
  }

  /* ---------- UI ------------------------------------------------------- */
  function build() {
    var css = document.createElement("style");
    css.textContent = [
      ".pr-ui{font-family:'Montserrat',system-ui,sans-serif;box-sizing:border-box}",
      "#pr-layer{position:absolute;inset:0;pointer-events:none;z-index:9000}",
      ".pr-pin{position:absolute;pointer-events:auto;transform:translate(-50%,-50%);",
      "  width:26px;height:26px;border-radius:50%;border:2px solid #fff;background:#C8102E;",
      "  color:#fff;font:700 12px/1 'Montserrat',sans-serif;cursor:pointer;",
      "  box-shadow:0 2px 8px rgba(0,0,0,.35);display:grid;place-items:center}",
      ".pr-pin:hover{transform:translate(-50%,-50%) scale(1.15)}",
      "#pr-fab{position:fixed;right:18px;bottom:18px;z-index:9100;display:flex;gap:8px;align-items:center}",
      "#pr-fab button{border:0;cursor:pointer;font:600 12.5px/1 'Montserrat',sans-serif;",
      "  letter-spacing:.08em;text-transform:uppercase;padding:13px 18px;background:#0F1012;color:#fff;",
      "  box-shadow:0 6px 22px rgba(0,0,0,.28)}",
      "#pr-fab button.on{background:#C8102E}",
      "#pr-badge{position:absolute;top:-7px;left:-7px;min-width:20px;height:20px;border-radius:10px;",
      "  background:#C8102E;color:#fff;font:700 11px/1 'Montserrat',sans-serif;display:none;",
      "  place-items:center;padding:0 6px;border:2px solid #fff}",
      "#pr-panel{position:fixed;right:18px;bottom:74px;width:330px;max-height:62vh;z-index:9100;",
      "  background:#fff;border:1px solid #D3D4CF;box-shadow:0 18px 50px rgba(0,0,0,.22);",
      "  display:none;flex-direction:column}",
      "#pr-panel.open{display:flex}",
      ".pr-head{padding:14px 16px;border-bottom:1px solid #E4E5E1}",
      ".pr-head b{font-size:13px;letter-spacing:.06em;text-transform:uppercase}",
      ".pr-count{display:block;margin-top:4px;font-size:11.5px;color:#7C7E82}",
      ".pr-list{overflow:auto;padding:6px 0;flex:1}",
      ".pr-row{display:flex;gap:10px;align-items:flex-start;padding:10px 16px;cursor:pointer;font-size:13px}",
      ".pr-row:hover{background:#F3F3F0}",
      ".pr-num{flex:0 0 auto;width:20px;height:20px;border-radius:50%;background:#C8102E;color:#fff;",
      "  font:700 11px/20px 'Montserrat',sans-serif;text-align:center}",
      ".pr-txt{flex:1;line-height:1.45;color:#33353A;word-break:break-word}",
      ".pr-del{flex:0 0 auto;border:0;background:none;color:#9FA09C;font-size:17px;cursor:pointer;line-height:1}",
      ".pr-del:hover{color:#C8102E}",
      ".pr-empty{margin:0;padding:16px;font-size:13px;color:#7C7E82;line-height:1.5}",
      ".pr-foot{border-top:1px solid #E4E5E1;padding:12px 16px;display:flex;gap:8px;flex-wrap:wrap}",
      ".pr-foot button{flex:1;border:1px solid #D3D4CF;background:#fff;cursor:pointer;",
      "  font:600 11px/1 'Montserrat',sans-serif;letter-spacing:.08em;text-transform:uppercase;padding:11px 8px}",
      ".pr-foot button.primary{background:#0F1012;color:#fff;border-color:#0F1012}",
      ".pr-note{padding:0 16px 12px;font-size:11.5px;color:#8A8C90;line-height:1.5}",
      ".pr-num.edit{background:#3F6B5E;font-size:12px}",
      ".pr-was{display:block;color:#9FA09C;text-decoration:line-through;font-size:12px;line-height:1.4}",
      ".pr-now{display:block;color:#1F3D33;font-weight:600;margin-top:2px;line-height:1.4}",
      ".pr-edited{background:linear-gradient(transparent 62%,#BFE3D6 62%);cursor:text}",
      ".pr-editing{outline:2px solid #3F6B5E;outline-offset:3px;background:#F2F8F5;cursor:text}",
      "body.pr-text .pr-hoverable:hover{outline:2px dashed #3F6B5E;outline-offset:3px;cursor:text}",
      "body.pr-on{cursor:crosshair}",
      "body.pr-text{cursor:text}",
      "body.pr-text [contenteditable=true]{pointer-events:auto!important}",
      "body.pr-on a,body.pr-on button:not(.pr-ui *){pointer-events:none}",
      "@media print{#pr-fab,#pr-panel,#pr-layer{display:none!important}}"
    ].join("");
    document.head.appendChild(css);

    layer = el("div", "pr-ui"); layer.id = "pr-layer";
    document.body.appendChild(layer);

    panel = el("div", "pr-ui"); panel.id = "pr-panel";
    var head = el("div", "pr-head");
    head.appendChild(el("b", null, "Your notes"));
    head.appendChild(el("span", "pr-count", ""));
    panel.appendChild(head);
    panel.appendChild(el("div", "pr-list"));
    var note = el("p", "pr-note",
      "Notes are saved in this browser only. Copy or email them before you finish.");
    var foot = el("div", "pr-foot");
    var bCopy = el("button", null, "Copy all");
    var bMail = el("button", "primary", "Email to Beau");
    bCopy.addEventListener("click", copyAll);
    bMail.addEventListener("click", emailAll);
    foot.appendChild(bCopy); foot.appendChild(bMail);
    panel.appendChild(note);
    panel.appendChild(foot);
    document.body.appendChild(panel);

    fab = el("div", "pr-ui"); fab.id = "pr-fab";
    var wrap = el("div"); wrap.style.position = "relative";
    var bToggle = el("button", null, "Review mode");
    badge = el("span", "pr-ui"); badge.id = "pr-badge";
    wrap.appendChild(bToggle); wrap.appendChild(badge);
    bMode = el("button", null, "Pins");
    bMode.title = "Switch between dropping pins and rewriting text";
    bMode.addEventListener("click", function () {
      mode = mode === "pin" ? "text" : "pin";
      bMode.textContent = mode === "pin" ? "Pins" : "Text";
      document.body.classList.toggle("pr-text", mode === "text" && on);
      var t = document.querySelector("#pr-fab button");
      if (on && t) {
        t.textContent = mode === "pin"
          ? "Reviewing — click to pin"
          : "Reviewing — click text to edit";
      }
      if (mode === "text") {
        document.querySelectorAll(EDITABLE).forEach(function (n) {
          if (!n.closest(".pr-ui")) n.classList.add("pr-hoverable");
        });
      } else {
        document.querySelectorAll(".pr-hoverable").forEach(function (n) {
          n.classList.remove("pr-hoverable");
        });
      }
    });

    var bList = el("button", null, "Notes");
    bToggle.addEventListener("click", function () {
      on = !on;
      document.body.classList.toggle("pr-on", on);
      bToggle.classList.toggle("on", on);
      bToggle.textContent = on
        ? (mode === "pin" ? "Reviewing — click to pin" : "Reviewing — click text to edit")
        : "Review mode";
      document.body.classList.toggle("pr-text", mode === "text" && on);
      bMode.style.display = on ? "" : "none";
      if (on) panel.classList.add("open");
    });
    bList.addEventListener("click", function () { panel.classList.toggle("open"); });
    bMode.style.display = "none";
    fab.appendChild(wrap); fab.appendChild(bMode); fab.appendChild(bList);
    document.body.appendChild(fab);

    /* Losing an hour of Darren's feedback silently is the worst outcome here,
       so warn on the way out whenever anything is unsent. */
    window.addEventListener("beforeunload", function (e) {
      if ((!ENDPOINT && totalAll() > 0) || (ENDPOINT && pending() > 0)) {
        e.preventDefault();
        e.returnValue = "";
        return "";
      }
    });

    document.addEventListener("click", onClick, true);
    window.addEventListener("resize", render);
    window.addEventListener("load", function () { render(); flush(); });
    window.addEventListener("online", flush);
    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
