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
  var on = false, layer, panel, fab, badge;

  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = txt;
    return n;
  }

  /* ---------- rendering ------------------------------------------------ */
  function render() {
    layer.innerHTML = "";
    var list = notes();
    list.forEach(function (n, i) {
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
        "No notes on this page yet. Click anywhere on the page to drop a pin."));
    }
    list.forEach(function (n, i) {
      var row = el("div", "pr-row");
      var num = el("span", "pr-num", String(i + 1));
      var txt = el("div", "pr-txt", n.text);
      var del = el("button", "pr-del", "×");
      del.title = "Delete this note";
      del.addEventListener("click", function () {
        var l = notes(); l.splice(i, 1); setNotes(l); render();
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
    badge.textContent = t ? String(t) : "";
    badge.style.display = t ? "grid" : "none";
  }

  function openNote(i) {
    var list = notes();
    var v = prompt("Edit this note (clear the box to delete it):", list[i].text);
    if (v === null) return;
    if (!v.trim()) list.splice(i, 1); else list[i].text = v.trim();
    setNotes(list); render();
  }

  /* ---------- adding --------------------------------------------------- */
  function onClick(e) {
    if (!on) return;
    if (e.target.closest(".pr-ui")) return;             // our own chrome
    e.preventDefault();
    e.stopPropagation();
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
    render();
  }

  /* ---------- export --------------------------------------------------- */
  function asText() {
    var d = loadAll(), out = ["PEPPER DRAFT SITE — REVIEW NOTES",
      new Date().toLocaleString(), ""];
    Object.keys(d).sort().forEach(function (p) {
      if (!d[p].length) return;
      out.push("── " + p + " ──");
      d[p].forEach(function (n, i) { out.push((i + 1) + ". " + n.text); });
      out.push("");
    });
    return out.join("\n");
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
      "body.pr-on{cursor:crosshair}",
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
    var bList = el("button", null, "Notes");
    bToggle.addEventListener("click", function () {
      on = !on;
      document.body.classList.toggle("pr-on", on);
      bToggle.classList.toggle("on", on);
      bToggle.textContent = on ? "Reviewing — click the page" : "Review mode";
      if (on) panel.classList.add("open");
    });
    bList.addEventListener("click", function () { panel.classList.toggle("open"); });
    fab.appendChild(wrap); fab.appendChild(bList);
    document.body.appendChild(fab);

    document.addEventListener("click", onClick, true);
    window.addEventListener("resize", render);
    window.addEventListener("load", render);
    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
