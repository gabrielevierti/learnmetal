(function () {
  var root = document.documentElement;
  var T = window.LM_T || {};
  var store = function (key, value) { try { localStorage.setItem(key, value); } catch (e) {} };

  document.getElementById("theme-toggle").addEventListener("click", function () {
    var next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    store("theme", next);
  });

  // Swift / C++ switch: keep the reader's place on the page when blocks change height.
  document.querySelectorAll("[data-set-lang]").forEach(function (btn) {
    btn.setAttribute("aria-pressed", String(root.dataset.lang === btn.dataset.setLang));
    btn.addEventListener("click", function () {
      var anchor = null, top = 0;
      document.querySelectorAll("article h2, article h3, article p").forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (!anchor && r.height && r.bottom > 70) { anchor = el; top = r.top; }
      });
      root.dataset.lang = btn.dataset.setLang;
      store("lang", btn.dataset.setLang);
      document.querySelectorAll("[data-set-lang]").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b === btn));
      });
      if (anchor && anchor.getBoundingClientRect().height) window.scrollBy(0, anchor.getBoundingClientRect().top - top);
    });
  });

  var menu = document.getElementById("menu-toggle");
  menu.addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
  document.querySelector(".content").addEventListener("click", function () { document.body.classList.remove("nav-open"); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") document.body.classList.remove("nav-open"); });

  var active = document.querySelector(".sidebar a.active");
  if (active) active.scrollIntoView({ block: "center" });

  document.querySelectorAll(".codehilite").forEach(function (block) {
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = T.copy;
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(block.querySelector("pre").innerText).then(function () {
        btn.textContent = T.copied;
        setTimeout(function () { btn.textContent = T.copy; }, 1200);
      });
    });
    block.appendChild(btn);
  });

  // ---- Reading progress: a chapter counts as read once its end has been on screen.
  var readKey = "lm-read";
  var loadRead = function () { try { return JSON.parse(localStorage.getItem(readKey)) || {}; } catch (e) { return {}; } };
  var paintRead = function () {
    var read = loadRead(), links = document.querySelectorAll("a[data-key]"), total = {}, done = 0;
    links.forEach(function (a) {
      var on = !!read[a.dataset.key];
      a.classList.toggle("read", on);
      if (on) a.setAttribute("title", T.read); else a.removeAttribute("title");
      total[a.dataset.key] = on;
    });
    var box = document.getElementById("progress");
    if (!box) return;
    Object.keys(total).forEach(function (k) { if (total[k]) done++; });
    box.hidden = done === 0;
    box.textContent = T.progress.replace("{n}", done).replace("{total}", Object.keys(total).length) + " ";
    var reset = document.createElement("button");
    reset.type = "button";
    reset.textContent = T.reset;
    reset.addEventListener("click", function () { try { localStorage.removeItem(readKey); } catch (e) {} paintRead(); });
    box.appendChild(reset);
  };
  paintRead();
  var pager = document.getElementById("pager"), pageKey = document.body.dataset.key;
  if (pager && pageKey && "IntersectionObserver" in window) {
    var seen = new IntersectionObserver(function (entries) {
      if (!entries.some(function (e) { return e.isIntersecting; })) return;
      var read = loadRead();
      read[pageKey] = 1;
      store(readKey, JSON.stringify(read));
      paintRead();
      seen.disconnect();
    });
    seen.observe(pager);
  }

  // ---- Search: the index is a separate file, loaded the first time the box is used.
  var input = document.getElementById("search"), results = document.getElementById("search-results");
  var site = root.dataset.site || "", index = null, loading = false, picked = -1;
  var esc = function (s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var fold = function (s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); };
  var loadIndex = function (then) {
    if (index) return then();
    if (loading) return;
    loading = true;
    results.hidden = false;
    results.innerHTML = '<p class="search-empty">' + esc(T.loading) + "…</p>";
    var s = document.createElement("script");
    s.src = site + "search-index.js";
    s.onload = function () {
      index = (window.LM_SEARCH || []).map(function (e) { return { url: e[0], title: e[1], head: e[2], text: e[3], ft: fold(e[1]), fh: fold(e[2]), fx: fold(e[3]) }; });
      then();
    };
    document.head.appendChild(s);
  };
  var mark = function (text, words) {
    var out = esc(text);
    words.forEach(function (w) {
      out = out.replace(new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig"), "<mark>$1</mark>");
    });
    return out;
  };
  var run = function () {
    var q = input.value.trim(), words = fold(q).split(/\s+/).filter(Boolean);
    picked = -1;
    if (!words.length) { results.hidden = true; results.innerHTML = ""; return; }
    var hits = [];
    index.forEach(function (e) {
      var score = 0;
      for (var i = 0; i < words.length; i++) {
        var w = words[i], s = 0;
        if (e.ft.indexOf(w) >= 0) s += 12;
        if (e.fh.indexOf(w) >= 0) s += 8;
        var at = e.fx.indexOf(w);
        if (at >= 0) s += 1 + Math.min(e.fx.split(w).length - 1, 5);
        if (!s) return;
        score += s;
      }
      hits.push({ e: e, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    results.hidden = false;
    if (!hits.length) { results.innerHTML = '<p class="search-empty">' + esc(T.none) + " “" + esc(q) + "”</p>"; return; }
    results.innerHTML = hits.slice(0, 12).map(function (h) {
      var e = h.e, at = e.fx.indexOf(words[0]), from = Math.max(0, at - 50);
      var snippet = (from > 0 ? "…" : "") + e.text.slice(from, from + 150) + (e.text.length > from + 150 ? "…" : "");
      return '<a href="' + site + e.url + '"><strong>' + mark(e.title, words) + (e.head ? " <span>" + mark(e.head, words) + "</span>" : "") +
             "</strong><small>" + mark(snippet, words) + "</small></a>";
    }).join("");
  };
  var pick = function (step) {
    var links = results.querySelectorAll("a");
    if (!links.length) return;
    picked = (picked + step + links.length) % links.length;
    links.forEach(function (a, i) { a.classList.toggle("picked", i === picked); });
    links[picked].scrollIntoView({ block: "nearest" });
  };
  if (input) {
    input.addEventListener("focus", function () { loadIndex(run); });
    input.addEventListener("input", function () { loadIndex(run); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); pick(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); pick(-1); }
      else if (e.key === "Enter") { var a = results.querySelectorAll("a")[Math.max(picked, 0)]; if (a) location.href = a.href; }
      else if (e.key === "Escape") { input.value = ""; results.hidden = true; input.blur(); document.body.classList.remove("search-open"); }
    });
    document.addEventListener("click", function (e) { if (!e.target.closest(".search, #search-toggle")) results.hidden = true; });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
        e.preventDefault(); document.body.classList.add("search-open"); input.focus();
      }
    });
    document.getElementById("search-toggle").addEventListener("click", function () {
      document.body.classList.toggle("search-open");
      if (document.body.classList.contains("search-open")) input.focus();
    });
  }
})();
