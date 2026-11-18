/* Eclipse globe. The globe sits at the top of the page, so everything it needs (two small d3 files,
   the eclipse data and the land map) is requested at once, in parallel, as soon as this script runs.
   Until it is all here the Play button is disabled and the time line says "Loading globe…".
   The canvas repaints only when something changes, so an idle page costs nothing. */
(function () {
  const root = document.getElementById('globe');
  if (!root) return;

  const playBtn = root.querySelector('[data-play]');
  const timeEl = root.querySelector('[data-time]');
  playBtn.disabled = true;
  timeEl.textContent = root.dataset.loading || 'Loading globe…';

  // async=false: both scripts download in parallel but run in order (d3-geo needs d3-array).
  const loadScript = src => new Promise((ok, fail) => {
    const s = document.createElement('script');
    s.src = src; s.async = false; s.onload = ok; s.onerror = fail;
    document.head.appendChild(s);
  });
  const getJson = url => fetch(url).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });

  Promise.all([
    getJson(root.dataset.json),
    getJson(root.dataset.land),
    loadScript(root.dataset.d3a),
    loadScript(root.dataset.d3g),
  ]).then(([data, land]) => {
    playBtn.disabled = false;
    draw(data, land);
  }).catch(() => {
    timeEl.textContent = root.dataset.failed || 'The globe could not load. Please refresh the page.';
  });

  function draw(data, land) {
    const d3 = window.d3;
    const canvas = root.querySelector('canvas');
    const ctx = canvas.getContext('2d');
    const slider = root.querySelector('input[type=range]');
    const playLabel = playBtn.textContent.trim(), pauseLabel = root.dataset.pause || '❚❚ Pause';
    const city = [parseFloat(root.dataset.lon), parseFloat(root.dataset.lat)];
    const fmt = new Intl.DateTimeFormat('en-IN', {
      timeZone: root.dataset.tz, day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
    });
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const projection = d3.geoOrthographic().clipAngle(90).precision(0.6);
    const path = d3.geoPath(projection, ctx);
    const graticule = d3.geoGraticule10();
    const circle = d3.geoCircle();
    let size = 0, frameIndex = Math.round(data.frames.length / 2);
    slider.max = data.frames.length - 1;

    function resize() {
      size = Math.min(canvas.parentElement.clientWidth, 640);
      canvas.width = canvas.height = size * dpr;
      canvas.style.width = canvas.style.height = size + 'px';
      projection.scale(size / 2 - 10).translate([size / 2, size / 2]);
      render();
    }

    function focus(point) { projection.rotate([-point[0], -Math.max(-55, Math.min(55, point[1]))]); }

    function render() {
      if (!size) return;
      const frame = data.frames[frameIndex];
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, size, size);
      const r = projection.scale(), c = size / 2;

      const ocean = ctx.createRadialGradient(c - r * .35, c - r * .4, r * .1, c, c, r);
      ocean.addColorStop(0, '#2a5a97'); ocean.addColorStop(.7, '#123565'); ocean.addColorStop(1, '#081a3a');
      ctx.beginPath(); ctx.arc(c, c, r, 0, 2 * Math.PI); ctx.fillStyle = ocean; ctx.fill();

      ctx.beginPath(); path(graticule); ctx.strokeStyle = 'rgba(255,255,255,.07)'; ctx.lineWidth = .6; ctx.stroke();
      ctx.beginPath(); path(land); ctx.fillStyle = '#3f7d5c'; ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,.2)'; ctx.lineWidth = .5; ctx.stroke();

      if (data.kind === 'solar') {
        const rotation = projection.rotate(), center = [-rotation[0], -rotation[1]];
        const dot = r * .044;
        for (const [lon, lat, value] of data.grid) {
          if (d3.geoDistance([lon, lat], center) > 1.5) continue;
          const [x, y] = projection([lon, lat]);
          ctx.fillStyle = `rgba(255,179,64,${.35 + value * .55})`;
          ctx.beginPath(); ctx.arc(x, y, dot * (.45 + value * .55), 0, 2 * Math.PI); ctx.fill();
        }
        if (frame.shadow) {
          ctx.beginPath(); path(circle.center(frame.shadow).radius(16)());
          ctx.fillStyle = 'rgba(5,6,15,.42)'; ctx.fill();
          ctx.beginPath(); path(circle.center(frame.shadow).radius(4)());
          ctx.fillStyle = 'rgba(5,6,15,.8)'; ctx.fill();
        }
      } else if (frame.moon) {
        ctx.beginPath(); path(circle.center(frame.moon).radius(90)());
        ctx.fillStyle = 'rgba(255,210,122,.22)'; ctx.fill();
        ctx.strokeStyle = 'rgba(255,210,122,.75)'; ctx.lineWidth = 1.2; ctx.stroke();
      }

      const night = [(frame.sun[0] + 360) % 360 - 180, -frame.sun[1]];
      ctx.beginPath(); path(circle.center(night).radius(90)());
      ctx.fillStyle = 'rgba(4,8,32,.5)'; ctx.fill();

      if (data.path.length) {
        ctx.beginPath(); path({ type: 'LineString', coordinates: data.path });
        ctx.strokeStyle = '#ff3b30'; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.stroke();
      }

      const rotation = projection.rotate();
      if (d3.geoDistance(city, [-rotation[0], -rotation[1]]) < 1.5) {
        const [x, y] = projection(city);
        ctx.beginPath(); ctx.arc(x, y, 4.5, 0, 2 * Math.PI); ctx.fillStyle = '#fff'; ctx.fill();
        ctx.strokeStyle = '#d2691e'; ctx.lineWidth = 2; ctx.stroke();
      }

      const halo = ctx.createRadialGradient(c, c, r * .96, c, c, r);
      halo.addColorStop(0, 'rgba(140,190,255,0)'); halo.addColorStop(1, 'rgba(140,190,255,.5)');
      ctx.beginPath(); ctx.arc(c, c, r, 0, 2 * Math.PI); ctx.fillStyle = halo; ctx.fill();

      slider.value = frameIndex;
      timeEl.textContent = fmt.format(new Date(frame.t));
    }

    let playing = false, last = 0;
    function tick(now) {
      if (!playing) return;
      if (now - last > 45) {
        last = now;
        frameIndex = (frameIndex + 1) % data.frames.length;
        render();
        if (frameIndex === data.frames.length - 1) setPlaying(false);
      }
      requestAnimationFrame(tick);
    }
    function setPlaying(on) {
      playing = on;
      playBtn.textContent = on ? pauseLabel : playLabel;
      if (on) requestAnimationFrame(tick);
    }
    playBtn.addEventListener('click', () => setPlaying(!playing));
    slider.addEventListener('input', () => { setPlaying(false); frameIndex = +slider.value; render(); });

    let dragging = null;
    canvas.addEventListener('pointerdown', e => {
      dragging = { x: e.clientX, y: e.clientY, r: projection.rotate() };
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove', e => {
      if (!dragging) return;
      const k = 90 / projection.scale();
      projection.rotate([dragging.r[0] + (e.clientX - dragging.x) * k,
                         Math.max(-85, Math.min(85, dragging.r[1] - (e.clientY - dragging.y) * k))]);
      render();
    });
    ['pointerup', 'pointercancel'].forEach(n => canvas.addEventListener(n, () => { dragging = null; }));

    let resizeTimer;
    window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(resize, 150); });

    focus(data.peak);
    resize();
    if (!reduceMotion) { frameIndex = 0; setPlaying(true); }
  }
})();
