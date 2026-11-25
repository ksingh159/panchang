/* Install-as-app and the morning notification (core/views/app_views.py, partials/app_promo.html).
   Loaded on every page by partials/pwa_head.html; the buttons exist only where app_promo.html is included. */
(function () {
  "use strict";
  var me = document.currentScript;
  var KEY = me && me.getAttribute("data-key");
  var LANG = (document.documentElement.lang || "en").slice(0, 2) === "hi" ? "hi" : "en";
  var ua = navigator.userAgent || "";
  var IOS = /iPhone|iPad|iPod/.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  var STANDALONE = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  var PUSH_OK = "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
  var deferred = null;

  function store(k, v) { try { if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) {} }
  function read(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function $$(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }
  function show(sel, on) { $$(sel).forEach(function (el) { el.hidden = !on; }); }

  function b64ToBytes(s) {
    var pad = "=".repeat((4 - s.length % 4) % 4);
    var raw = atob((s + pad).replace(/-/g, "+").replace(/_/g, "/"));
    var out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }

  function post(url, body) {
    return fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
                       credentials: "same-origin"}).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  }

  /* ---- install ---- */
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
    show("[data-pwa-install]", true);
  });
  window.addEventListener("appinstalled", function () {
    deferred = null;
    show("[data-pwa-install]", false);
    show("[data-pwa-installed]", true);
  });

  /* ---- notification ---- */
  function promo() { return document.querySelector("[data-pwa-promo]"); }

  function setState(on, city) {
    var p = promo();
    if (!p) return;
    var here = p.getAttribute("data-city");
    $$("[data-pwa-notify]").forEach(function (b) {
      b.hidden = false;
      b.disabled = false;
      if (!on) b.textContent = b.getAttribute("data-off-text");
      else if (city && city !== here) b.textContent = b.getAttribute("data-switch-text");
      else { b.textContent = b.getAttribute("data-on-text"); b.disabled = true; }
    });
    show("[data-pwa-stop]", on);
  }

  function registration() {
    return navigator.serviceWorker.ready;
  }

  function subscribe() {
    var p = promo();
    var city = p ? p.getAttribute("data-city") : "";
    return Notification.requestPermission().then(function (perm) {
      if (perm !== "granted") { show("[data-pwa-denied]", true); throw new Error("denied"); }
      return registration();
    }).then(function (reg) {
      return reg.pushManager.getSubscription().then(function (s) {
        return s || reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: b64ToBytes(KEY)});
      });
    }).then(function (sub) {
      return post("/push/subscribe/", {subscription: sub.toJSON(), lang: LANG, city: city});
    }).then(function (res) {
      store("pushCity", res.city);
      setState(true, res.city);
      show("[data-pwa-done]", true);
    });
  }

  function unsubscribe() {
    return registration().then(function (reg) { return reg.pushManager.getSubscription(); }).then(function (sub) {
      if (!sub) return null;
      var endpoint = sub.endpoint;
      return sub.unsubscribe().then(function () { return post("/push/unsubscribe/", {endpoint: endpoint}); });
    }).then(function () {
      store("pushCity", null);
      setState(false);
      show("[data-pwa-done]", false);
    });
  }

  function initPromo() {
    if (!promo()) return;
    if (STANDALONE) show("[data-pwa-installed]", true);
    else if (IOS) show("[data-pwa-ios]", true);
    if (!KEY) return;
    if (!PUSH_OK) {                     // iPhone/iPad: Safari allows notifications only once added to the home screen
      if (IOS && !STANDALONE) show("[data-pwa-ios-push]", true);
      return;
    }
    if (Notification.permission === "denied") { show("[data-pwa-denied]", true); return; }
    registration().then(function (reg) { return reg.pushManager.getSubscription(); }).then(function (sub) {
      setState(!!sub, sub ? read("pushCity") : null);
    });
    $$("[data-pwa-notify]").forEach(function (b) {
      b.addEventListener("click", function () {
        b.disabled = true;
        subscribe().catch(function () { b.disabled = false; });
      });
    });
    $$("[data-pwa-stop]").forEach(function (a) {
      a.addEventListener("click", function (e) { e.preventDefault(); unsubscribe(); });
    });
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-pwa-install]");
    if (!b || !deferred) return;
    deferred.prompt();
    deferred.userChoice.finally(function () { deferred = null; show("[data-pwa-install]", false); });
  });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", {scope: "/"}).catch(function () {});
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initPromo);
  else initPromo();
})();
