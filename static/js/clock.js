/*
 * Minimal ES5 clock. Updates the #clock element's text every second so the
 * time ticks smoothly between full-page meta-refreshes. No dependencies.
 */
(function () {
  function pad_with_zero(n) {
    var pad = n < 10 ? "0" : "";
    return pad += n
  }

  function tick() {
    var el = document.getElementById("clock");
    if (!el) {
      return;
    }

    var now = new Date();
    var text = pad_with_zero(now.getHours()) + ":" + pad_with_zero(now.getMinutes());

    if (el.firstChild && el.firstChild.nodeType === 3) {
      el.firstChild.nodeValue = text;
    } else {
      el.innerHTML = text;
    }
  }

  tick();
  setInterval(tick, 1000);
})();
