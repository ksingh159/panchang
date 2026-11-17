/*
 * Place autocomplete backed by /api/city-autocomplete/ (offline GeoNames).
 *
 * <input data-place-autocomplete
 *        data-lat="#lat" data-lon="#lon" data-tz="#tz" data-place-id="#place_id">
 * Fills the target fields when a suggestion is picked; names stay short:
 * "Varanasi, Uttar Pradesh, India".
 */
(function () {
  function $(sel) { return sel ? document.querySelector(sel) : null; }

  function attach(input) {
    const box = document.createElement('div');
    box.className = 'place-suggestions';
    input.parentNode.style.position = 'relative';
    input.parentNode.appendChild(box);
    let timer = null, items = [], active = -1;

    function set(field, value) { const el = $(input.dataset[field]); if (el) el.value = value; }

    function choose(c) {
      input.value = c.name;
      set('lat', c.lat); set('lon', c.lon); set('tz', c.timezone); set('placeId', c.id);
      box.style.display = 'none';
      input.dispatchEvent(new CustomEvent('place:selected', { detail: c, bubbles: true }));
    }

    function render() {
      box.innerHTML = '';
      items.forEach((c, i) => {
        const row = document.createElement('div');
        row.className = 'place-suggestion' + (i === active ? ' active' : '');
        const main = document.createElement('strong');
        main.textContent = c.city;
        const sub = document.createElement('span');
        sub.textContent = [c.state, c.country].filter(Boolean).join(', ') + (c.timezone ? ' · ' + c.timezone : '');
        row.append(main, sub);
        row.addEventListener('mousedown', e => { e.preventDefault(); choose(c); });
        box.appendChild(row);
      });
      box.style.display = items.length ? 'block' : 'none';
    }

    input.setAttribute('autocomplete', 'off');
    input.addEventListener('input', () => {
      set('placeId', '');
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { items = []; render(); return; }
      timer = setTimeout(async () => {
        try {
          const r = await fetch('/api/city-autocomplete/?q=' + encodeURIComponent(q));
          items = (await r.json()).suggestions || [];
        } catch (e) { items = []; }
        active = -1; render();
      }, 200);
    });
    input.addEventListener('keydown', e => {
      if (!items.length || box.style.display === 'none') return;
      if (e.key === 'ArrowDown') { active = (active + 1) % items.length; render(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { active = (active - 1 + items.length) % items.length; render(); e.preventDefault(); }
      else if (e.key === 'Enter' && active >= 0) { choose(items[active]); e.preventDefault(); }
      else if (e.key === 'Escape') { box.style.display = 'none'; }
    });
    input.addEventListener('blur', () => setTimeout(() => { box.style.display = 'none'; }, 150));
  }

  const css = document.createElement('style');
  css.textContent = '.place-suggestions{position:absolute;left:0;right:0;top:100%;z-index:50;background:#fff;' +
    'border:1px solid #e0d4c0;border-radius:6px;box-shadow:0 6px 16px rgba(0,0,0,.12);display:none;max-height:280px;overflow:auto}' +
    '.place-suggestion{padding:8px 12px;cursor:pointer;display:flex;flex-direction:column;gap:2px;color:#3a2410;text-align:left}' +
    '.place-suggestion strong{color:#3a2410;font-size:14px}' +
    '.place-suggestion span{font-size:12px;color:#777}.place-suggestion:hover,.place-suggestion.active{background:#fdf3e4}';
  document.head.appendChild(css);
  document.addEventListener('DOMContentLoaded', () =>
    document.querySelectorAll('[data-place-autocomplete]').forEach(attach));
})();
