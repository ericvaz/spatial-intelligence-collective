/* Hero background — a live cellular automaton.
 *
 * A Larger-than-Life growth rule runs on a lattice: each cell reads the mean
 * state of its neighbourhood (an isotropic gaussian kernel, built from three
 * box passes) and grows when that mean falls inside a narrow band, otherwise
 * it decays. From that one rule the whole composition is derived —
 *
 *   field (blurred) -> iso-contours, via marching squares -> topographic lines
 *   field           -> cells above threshold, jittered     -> particle cloud
 *   field           -> separated local maxima + 2-NN links -> node-link graph
 *
 * so the artwork builds itself rather than being drawn. Parameters were tuned
 * offline for ~30% coverage: enough structure to read, enough white to breathe.
 *
 * Falls back to the static SVG when canvas is unavailable or the visitor has
 * asked for reduced motion.
 */
(function () {
  'use strict';

  var host = document.querySelector('.hero-art');
  if (!host) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var cv = document.createElement('canvas');
  var ctx = cv.getContext && cv.getContext('2d');
  if (!ctx) return;

  cv.className = 'hero-ca';
  cv.setAttribute('aria-hidden', 'true');
  host.appendChild(cv);
  var fallback = host.querySelector('img');
  if (fallback) fallback.style.visibility = 'hidden';

  // ---- rule ---------------------------------------------------------------
  var CELL = 7,      // lattice pitch, CSS px
      R    = 2,      // neighbourhood radius (sets structure scale)
      B1   = 0.22,   // growth band lower bound
      B2   = 0.34,   // growth band upper bound
      DT   = 0.13,   // state change per step
      MS   = 110,    // ms per CA step
      FPS  = 40;     // ms between repaints (~25fps)

  var cols, rows, n, W, H, dpr,
      cur, prev, nbr, smC, smP, disp, dispS, bufA, bufB, jx, jy;
  var nodes = [], edges = [], meshPath = null;

  function rand(s) {
    return function () {
      s |= 0; s = s + 0x6D2B79F5 | 0;
      var t = Math.imul(s ^ s >>> 15, 1 | s);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function alloc() {
    n = cols * rows;
    cur = new Float32Array(n); prev = new Float32Array(n); nbr = new Float32Array(n);
    smC = new Float32Array(n); smP = new Float32Array(n);
    disp = new Float32Array(n); dispS = new Float32Array(n);
    bufA = new Float32Array(n); bufB = new Float32Array(n);
    jx = new Float32Array(n); jy = new Float32Array(n);
    var r = rand(20260818);
    for (var i = 0; i < n; i++) { jx[i] = (r() - .5) * CELL * .92; jy[i] = (r() - .5) * CELL * .92; }
  }

  function seed(count, r) {
    r = r || rand((Math.random() * 1e9) | 0);
    for (var k = 0; k < count; k++) {
      var cx = r() * cols, cy = r() * rows, rad = 2 + r() * 3, x, y, i;
      for (y = Math.max(0, cy - rad | 0); y < Math.min(rows, cy + rad + 1); y++)
        for (x = Math.max(0, cx - rad | 0); x < Math.min(cols, cx + rad + 1); x++) {
          i = y * cols + x;
          if ((x - cx) * (x - cx) + (y - cy) * (y - cy) < rad * rad) cur[i] = .55 + r() * .45;
        }
    }
  }

  // one separable box pass
  function box(src, dst, rad) {
    var x, y, i, o, sum, d = 2 * rad + 1;
    for (y = 0; y < rows; y++) {
      o = y * cols; sum = 0;
      for (i = -rad; i <= rad; i++) sum += src[o + (i < 0 ? 0 : i > cols - 1 ? cols - 1 : i)];
      for (x = 0; x < cols; x++) {
        bufB[o + x] = sum / d;
        sum += src[o + Math.min(cols - 1, x + rad + 1)] - src[o + Math.max(0, x - rad)];
      }
    }
    for (x = 0; x < cols; x++) {
      sum = 0;
      for (i = -rad; i <= rad; i++) sum += bufB[(i < 0 ? 0 : i > rows - 1 ? rows - 1 : i) * cols + x];
      for (y = 0; y < rows; y++) {
        dst[y * cols + x] = sum / d;
        sum += bufB[Math.min(rows - 1, y + rad + 1) * cols + x] - bufB[Math.max(0, y - rad) * cols + x];
      }
    }
  }

  // three box passes ≈ gaussian: isotropic, so no grid-aligned striping
  function gaussian(src, dst, rad) {
    box(src, bufA, rad); box(bufA, dst, rad); box(dst, bufA, rad);
    dst.set(bufA);
  }

  function step() {
    prev.set(cur); smP.set(smC);
    gaussian(cur, nbr, R);
    var i, v, u, alive = 0;
    for (i = 0; i < n; i++) {
      u = nbr[i];
      v = cur[i] + DT * (u >= B1 && u <= B2 ? 1 : -1);
      v = v < 0 ? 0 : v > 1 ? 1 : v;
      cur[i] = v;
      if (v > .5) alive++;
    }
    if (alive < n * 0.03) seed(5);          // never let the system die out
    gaussian(cur, smC, 3);                  // smooth copy drives the contours
    graph();
  }

  // hubs = local maxima separated by a 7x7 window, so they spread out
  function graph() {
    nodes.length = 0;
    var x, y, i, v, dx, dy, ok;
    for (y = 3; y < rows - 3 && nodes.length < 180; y++) {
      for (x = 3; x < cols - 3; x++) {
        i = y * cols + x; v = cur[i];
        if (v < .62) continue;
        ok = 1;
        for (dy = -3; dy <= 3 && ok; dy++)
          for (dx = -3; dx <= 3; dx++)
            if (cur[i + dy * cols + dx] > v) { ok = 0; break; }
        if (!ok) continue;
        nodes.push(x * CELL + jx[i] * .35, y * CELL + jy[i] * .35, v);
        x += 3;
      }
    }
    edges.length = 0;
    var a, b, d2, b1, b2, i1, i2, cnt = nodes.length / 3;
    for (a = 0; a < cnt; a++) {
      b1 = b2 = 1e9; i1 = i2 = -1;
      for (b = 0; b < cnt; b++) {
        if (b === a) continue;
        dx = nodes[a * 3] - nodes[b * 3]; dy = nodes[a * 3 + 1] - nodes[b * 3 + 1];
        d2 = dx * dx + dy * dy;
        if (d2 < b1) { b2 = b1; i2 = i1; b1 = d2; i1 = b; }
        else if (d2 < b2) { b2 = d2; i2 = b; }
      }
      if (i1 > a && b1 < 26000) edges.push(a, i1);
      if (i2 > a && b2 < 26000) edges.push(a, i2);
    }
  }

  // ---- marching squares ---------------------------------------------------
  var TBL = [null, [3, 0], [0, 1], [3, 1], [1, 2], [3, 0, 1, 2], [0, 2], [3, 2],
             [2, 3], [2, 0], [0, 1, 2, 3], [2, 1], [1, 3], [1, 0], [0, 3], null];

  function contours(f, from, to, stepv) {
    var x, y, i, v0, v1, v2, v3, idx, e, k, L, t, ax, ay, bx, by, ox, oy, ec;
    ctx.beginPath();
    for (L = from; L < to; L += stepv) {
      for (y = 0; y < rows - 1; y++) {
        oy = y * CELL;
        for (x = 0; x < cols - 1; x++) {
          i = y * cols + x;
          v0 = f[i]; v1 = f[i + 1]; v2 = f[i + cols + 1]; v3 = f[i + cols];
          idx = (v0 > L ? 1 : 0) | (v1 > L ? 2 : 0) | (v2 > L ? 4 : 0) | (v3 > L ? 8 : 0);
          if (idx === 0 || idx === 15) continue;
          e = TBL[idx]; ox = x * CELL;
          for (k = 0; k < e.length; k += 2) {
            ec = e[k];
            if (ec === 0)      { t = (L - v0) / (v1 - v0 || 1e-6); ax = ox + t * CELL; ay = oy; }
            else if (ec === 1) { t = (L - v1) / (v2 - v1 || 1e-6); ax = ox + CELL; ay = oy + t * CELL; }
            else if (ec === 2) { t = (L - v3) / (v2 - v3 || 1e-6); ax = ox + t * CELL; ay = oy + CELL; }
            else               { t = (L - v0) / (v3 - v0 || 1e-6); ax = ox; ay = oy + t * CELL; }
            ec = e[k + 1];
            if (ec === 0)      { t = (L - v0) / (v1 - v0 || 1e-6); bx = ox + t * CELL; by = oy; }
            else if (ec === 1) { t = (L - v1) / (v2 - v1 || 1e-6); bx = ox + CELL; by = oy + t * CELL; }
            else if (ec === 2) { t = (L - v3) / (v2 - v3 || 1e-6); bx = ox + t * CELL; by = oy + CELL; }
            else               { t = (L - v0) / (v3 - v0 || 1e-6); bx = ox; by = oy + t * CELL; }
            ctx.moveTo(ax, ay); ctx.lineTo(bx, by);
          }
        }
      }
    }
    ctx.stroke();
  }

  function buildMesh() {
    meshPath = new Path2D();
    var x0 = W * .44, y0 = H * .46, cw = W * .024, ch = H * .026,
        c = 24, r = 20, sk = -.15, i, j;
    for (i = 0; i <= c; i++) {
      meshPath.moveTo(x0 + i * cw, y0);
      meshPath.lineTo(x0 + i * cw + sk * ch * r, y0 + ch * r);
    }
    for (j = 0; j <= r; j++) {
      meshPath.moveTo(x0 + sk * j * ch, y0 + j * ch);
      meshPath.lineTo(x0 + sk * j * ch + cw * c, y0 + j * ch);
    }
  }

  // ---- render -------------------------------------------------------------
  function draw(mix) {
    var i, x, y, v, tier, lo, hi, rad, px, py, nr;
    for (i = 0; i < n; i++) {
      disp[i]  = prev[i] + (cur[i] - prev[i]) * mix;
      dispS[i] = smP[i]  + (smC[i] - smP[i])  * mix;
    }

    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = '#0f0f12';

    ctx.globalAlpha = .2; ctx.lineWidth = .45;
    if (meshPath) ctx.stroke(meshPath);

    ctx.globalAlpha = .36; ctx.lineWidth = .6;
    contours(dispS, .05, .62, .05);

    ctx.fillStyle = '#1a1a20';
    for (tier = 0; tier < 5; tier++) {
      lo = .14 + tier * .172; hi = lo + .172; rad = .58 + tier * .46;
      ctx.globalAlpha = .2 + tier * .16;
      ctx.beginPath();
      for (y = 0; y < rows; y++)
        for (x = 0; x < cols; x++) {
          i = y * cols + x; v = disp[i];
          if (v < lo || v >= hi) continue;
          px = x * CELL + jx[i]; py = y * CELL + jy[i];
          ctx.moveTo(px + rad, py);
          ctx.arc(px, py, rad, 0, 6.2832);
        }
      ctx.fill();
    }

    ctx.globalAlpha = .42; ctx.lineWidth = .6;
    ctx.beginPath();
    for (i = 0; i < edges.length; i += 2) {
      ctx.moveTo(nodes[edges[i] * 3], nodes[edges[i] * 3 + 1]);
      ctx.lineTo(nodes[edges[i + 1] * 3], nodes[edges[i + 1] * 3 + 1]);
    }
    ctx.stroke();

    ctx.fillStyle = '#0f0f12'; ctx.globalAlpha = .88;
    ctx.beginPath();
    for (i = 0; i < nodes.length; i += 3) {
      nr = 1.8 + nodes[i + 2] * 4;
      ctx.moveTo(nodes[i] + nr, nodes[i + 1]);
      ctx.arc(nodes[i], nodes[i + 1], nr, 0, 6.2832);
    }
    ctx.fill();
    ctx.globalAlpha = 1;

    var g = ctx.createRadialGradient(W * .55, H * .46, 0, W * .55, H * .46, Math.max(W, H) * .64);
    g.addColorStop(0, 'rgba(255,255,255,0)');
    g.addColorStop(.55, 'rgba(255,255,255,0)');
    g.addColorStop(1, 'rgba(255,255,255,1)');
    ctx.globalCompositeOperation = 'destination-out';
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'source-over';
  }

  function resize() {
    W = host.clientWidth; H = host.clientHeight;
    if (!W || !H) return false;
    dpr = Math.min(2, window.devicePixelRatio || 1);
    cv.width = W * dpr; cv.height = H * dpr;
    cv.style.width = W + 'px'; cv.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    cols = Math.ceil(W / CELL) + 1; rows = Math.ceil(H / CELL) + 1;
    alloc(); buildMesh();
    seed(14, rand(4242));
    for (var i = 0; i < 40; i++) step();     // grow before the first paint
    return true;
  }

  var last = 0, acc = 0, paint = 0, running = true;
  function frame(now) {
    if (!running) return;
    requestAnimationFrame(frame);
    var dt = last ? Math.min(140, now - last) : 0;
    last = now;
    acc += dt; paint += dt;
    while (acc >= MS) { step(); acc -= MS; }
    if (paint >= FPS) { paint = 0; draw(acc / MS); }
  }

  if (!resize()) { if (fallback) fallback.style.visibility = ''; return; }
  draw(0);                                   // paint at once, don't wait on rAF
  requestAnimationFrame(frame);

  var rt;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(function () { if (resize()) draw(0); }, 220);
  });

  if (window.IntersectionObserver) {
    new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting && !running) { running = true; last = 0; requestAnimationFrame(frame); }
        else if (!e.isIntersecting) running = false;
      });
    }, { threshold: 0 }).observe(host);
  }
})();
