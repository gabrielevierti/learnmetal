(function () {
  var root = document.documentElement;
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
    btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(block.querySelector("pre").innerText).then(function () {
        btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = "Copy"; }, 1200);
      });
    });
    block.appendChild(btn);
  });
})();
