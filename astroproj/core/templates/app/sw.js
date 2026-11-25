/* Service worker (core/views/app_views.py service_worker). Served at /sw.js so its scope is the whole site.
   - Daily pages: network first, so they are always today's; the last copy is kept for reading offline.
   - Static files: from the cache, refreshed in the background.
   - Anything personal (kundali, account, payments) is never stored.
   - Shows the morning panchang notification and opens its page on tap. */
const VERSION = "v{{ version }}";
const STATIC = "static-" + VERSION, PAGES = "pages-" + VERSION;
const OFFLINE = "/offline/";
const PRECACHE = [OFFLINE{% for u in precache %}, "{{ u }}"{% endfor %}];
const PAGE_PREFIXES = ["/aaj-ka-panchang/", "/rashifal/", "/aaj-ka-choghadiya/", "/aaj-ki-hora/", "/vrat/",
                       "/hindu-calendar/", "/festivals/", "/panchang/"];
const MAX_PAGES = 40;

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(STATIC).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((k) => k !== STATIC && k !== PAGES).map((k) => caches.delete(k))
  )).then(() => self.clients.claim()));
});

function savable(url) {
  const p = url.pathname.replace(/^\/hi(?=\/)/, "");
  return p === "/" || PAGE_PREFIXES.some((x) => p.startsWith(x));
}

async function trim(cache) {
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - MAX_PAGES; i++) await cache.delete(keys[i]);
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (req.mode === "navigate") {
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        if (res.ok && savable(url)) {
          const c = await caches.open(PAGES);
          await c.put(req, res.clone());
          trim(c);
        }
        return res;
      } catch (err) {
        return (await caches.match(req, {ignoreSearch: true})) || (await caches.match(OFFLINE));
      }
    })());
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    e.respondWith((async () => {
      const c = await caches.open(STATIC);
      const hit = await c.match(req);
      const fresh = fetch(req).then((res) => { if (res.ok) c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || fresh;
    })());
  }
});

self.addEventListener("push", (e) => {
  let m = {};
  try { m = e.data ? e.data.json() : {}; } catch (err) { m = {body: e.data ? e.data.text() : ""}; }
  e.waitUntil(self.registration.showNotification(m.title || "Aaj Ka Panchang", {
    body: m.body || "", tag: m.tag || "panchang", renotify: false, lang: m.lang || "",
    icon: "{{ icon }}", badge: "{{ badge }}", data: {url: m.url || "/aaj-ka-panchang/"},
  }));
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const target = new URL(e.notification.data.url, self.location.origin).href;
  e.waitUntil((async () => {
    const wins = await self.clients.matchAll({type: "window", includeUncontrolled: true});
    for (const w of wins) {
      if (w.url === target && "focus" in w) return w.focus();
    }
    return self.clients.openWindow(target);
  })());
});
