(function () {
  var root = document.documentElement;

  document.getElementById("theme-toggle").addEventListener("click", function () {
    var next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) {}
  });

  document.getElementById("menu-toggle").addEventListener("click", function () {
    document.body.classList.toggle("nav-open");
  });
  document.querySelector(".content").addEventListener("click", function () {
    document.body.classList.remove("nav-open");
  });

  var active = document.querySelector(".sidebar a.active");
  if (active) active.scrollIntoView({ block: "center" });

  document.querySelectorAll(".codehilite").forEach(function (block) {
    var btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      var text = block.querySelector("pre").innerText;
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = "Copied";
        setTimeout(function () { btn.textContent = "Copy"; }, 1200);
      });
    });
    block.appendChild(btn);
  });
})();
