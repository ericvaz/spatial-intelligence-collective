/* Hero background — a live cellular automaton.
 *
 * A Larger-than-Life growth rule runs on a lattice: each cell reads the mean
 * state of an isotropic gaussian neighbourhood (three box passes) and grows
 * when that mean falls inside a narrow band, otherwise it decays. Everything
 * drawn is read back out of that one field —
 *
 *   field (blurred) -> iso-contours, marching squares -> topographic lines
 *   field           -> cells above threshold, jittered -> particle cloud
 *   field           -> separated local maxima + 2-NN    -> node-link graph
 *
 * so the artwork builds itself from the rule rather than being drawn.
 *
 * Steadiness matters as much as motion here, so three things damp the flicker
 * a raw CA would produce:
 *   1. rendering reads an exponential moving average of the state, not the
 *      state itself, so cells drift across thresholds instead of snapping;
 *   2. graph nodes persist frame to frame — maxima are matched to existing
 *      nodes, eased toward their new positions, and faded in and out by a
 *      life value, so the network never blinks;
 *   3. edges carry hysteresis: they are added at a shorter distance than they
 *      are dropped, so links near the threshold hold instead of stuttering.
 *
 * The system is not perpetual. It grows, settles, and stops. Clicking the field
 * drops sugar: an attractant that diffuses, widens the growth band along its
 * gradient so structures bulge toward it, and is consumed on arrival — after
 * which everything settles again. A small panel prints the rule actually being
 * evaluated, with live counters.
 *
 * Falls back to the static SVG without canvas, or under reduced motion.
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
  var CELL   = 7,      // lattice pitch, CSS px
      R      = 2,      // neighbourhood radius (sets structure scale)
      B1     = 0.22,   // growth band lower bound
      B2     = 0.34,   // growth band upper bound
      DT     = 0.085,  // state change per step — gentle, so crossings are slow
      MS     = 200,    // ms per CA step — slow, so crossings read as drift
      FPS    = 40,     // ms between repaints (~25fps)
      EMA    = 0.075,  // render smoothing; ~0.5s time constant
      EASE   = 0.11,   // how fast a node slides to its new position
      FADE   = 0.055,  // node fade in/out per step
      ADD_D2 = 20000,  // link forms within this squared distance
      KEEP_D2 = 32000, // ...and only breaks beyond this one
      WARM   = 25,     // steps run before the first paint
      STOP_AT = 60,    // live steps; WARM+STOP_AT lands in the band where
                       // the field reads clean, before it elaborates into noise
      FEED_STEPS = 35, // extra steps a sugar drop buys
      TAIL   = 12,     // steps at the end spent easing to a halt
      F_LO   = 0.11,   // sugar widens the band downward...
      F_HI   = 0.24;   // ...and upward, so structure grows toward it

  var cols, rows, n, W, H, dpr,
      cur, nbr, rf, rfs, food, foodB, bufA, bufB, jx, jy;
  var nodes = [], edges = [], nextId = 1, meshPath = null;
  var steps = 0, sugar = 0, stopAt = 0, phase = 'growing',
      panel = null, hint = null, lastPanel = 0, fedOnce = false;

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
    cur = new Float32Array(n); nbr = new Float32Array(n);
    rf = new Float32Array(n); rfs = new Float32Array(n);
    food = new Float32Array(n); foodB = new Float32Array(n);
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

  function gaussian(src, dst, rad) {
    box(src, bufA, rad); box(bufA, dst, rad); box(dst, bufA, rad);
    dst.set(bufA);
  }

  function step() {
    gaussian(cur, nbr, R);
    var i, v, u, f, lo, hi, alive = 0, left = 0;

    if (sugar > 0) gaussian(food, foodB, 2);      // sugar spreads into a gradient

    for (i = 0; i < n; i++) {
      u = nbr[i];
      f = sugar > 0 ? foodB[i] : 0;
      lo = B1 - f * F_LO;                          // the attractant widens the
      hi = B2 + f * F_HI;                          // band, so cells grow into it
      v = cur[i] + DT * (u >= lo && u <= hi ? 1 : -1);
      v = v < 0 ? 0 : v > 1 ? 1 : v;
      cur[i] = v;
      if (v > .5) alive++;
      if (f > 0) {
        if (v > .5) food[i] -= food[i] * .14 * v;  // eaten on arrival
        food[i] *= .994;                            // and slowly evaporates
        if (food[i] < .004) food[i] = 0;
        left += food[i];
      }
    }
    sugar = left;
    if (alive < n * 0.03) seed(5);
    steps++;
    graph();
  }

  // a click drops sugar onto the lattice
  function feed(px, py) {
    var cx = px / CELL, cy = py / CELL, rad = 7, x, y, i, d2;
    for (y = Math.max(0, cy - rad | 0); y < Math.min(rows, cy + rad + 1); y++)
      for (x = Math.max(0, cx - rad | 0); x < Math.min(cols, cx + rad + 1); x++) {
        d2 = (x - cx) * (x - cx) + (y - cy) * (y - cy);
        if (d2 > rad * rad) continue;
        i = y * cols + x;
        food[i] = Math.min(1, food[i] + Math.exp(-d2 / 14));
      }
    // one relaxation pass sheds the fine texture that accumulates over a long
    // run, so repeated feeding doesn't degrade into noise
    box(cur, bufA, 1);
    for (i = 0; i < n; i++) cur[i] = cur[i] * .78 + bufA[i] * .22;

    sugar = 1;
    phase = 'feeding';
    if (!fedOnce) { fedOnce = true; if (hint) hint.className = 'hero-hint gone'; }
    stopAt = steps + FEED_STEPS;
    ensureLoop();
  }

  // ---- persistent node-link graph -----------------------------------------
  function graph() {
    // maxima of the smoothed field, separated by a 7x7 window
    var peaks = [], x, y, i, v, dx, dy, ok;
    for (y = 3; y < rows - 3 && peaks.length < 300; y++) {
      for (x = 3; x < cols - 3; x++) {
        i = y * cols + x; v = rf[i];
        if (v < .58) continue;
        ok = 1;
        for (dy = -3; dy <= 3 && ok; dy++)
          for (dx = -3; dx <= 3; dx++)
            if (rf[i + dy * cols + dx] > v) { ok = 0; break; }
        if (!ok) continue;
        peaks.push(x * CELL + jx[i] * .35, y * CELL + jy[i] * .35, v);
        x += 3;
      }
    }

    var j, k, nd, best, bi, d2;
    for (k = 0; k < nodes.length; k++) nodes[k].seen = false;

    // match each peak to the nearest unclaimed node; otherwise spawn one
    for (j = 0; j < peaks.length; j += 3) {
      best = 1e9; bi = -1;
      for (k = 0; k < nodes.length; k++) {
        nd = nodes[k];
        if (nd.seen) continue;
        dx = nd.tx - peaks[j]; dy = nd.ty - peaks[j + 1];
        d2 = dx * dx + dy * dy;
        if (d2 < best) { best = d2; bi = k; }
      }
      if (bi >= 0 && best < 900) {                 // within ~30px: same node
        nd = nodes[bi];
        nd.tx = peaks[j]; nd.ty = peaks[j + 1]; nd.v = peaks[j + 2]; nd.seen = true;
      } else if (nodes.length < 90) {
        nodes.push({ id: nextId++, x: peaks[j], y: peaks[j + 1],
                     tx: peaks[j], ty: peaks[j + 1], v: peaks[j + 2],
                     life: 0, seen: true });
      }
    }

    // fade unmatched nodes out, matched nodes in; retire the dead
    for (k = nodes.length - 1; k >= 0; k--) {
      nd = nodes[k];
      nd.life += nd.seen ? FADE : -FADE;
      if (nd.life <= 0) { nodes.splice(k, 1); continue; }
      if (nd.life > 1) nd.life = 1;
    }

    // links, with hysteresis so borderline pairs hold instead of stuttering
    var had = {};
    for (k = 0; k < edges.length; k += 2) had[edges[k] + '|' + edges[k + 1]] = 1;
    var next = [], seenE = {}, a, b, b1, b2, i1, i2;

    function link(ia, ib, d2) {
      if (ib < 0 || ib === ia) return;
      var lo = Math.min(nodes[ia].id, nodes[ib].id),
          hi = Math.max(nodes[ia].id, nodes[ib].id),
          key = lo + '|' + hi;
      if (seenE[key]) return;
      if (d2 >= (had[key] ? KEEP_D2 : ADD_D2)) return;
      seenE[key] = 1; next.push(lo, hi);
    }

    for (a = 0; a < nodes.length; a++) {
      b1 = b2 = 1e9; i1 = i2 = -1;
      for (b = 0; b < nodes.length; b++) {
        if (b === a) continue;
        dx = nodes[a].x - nodes[b].x; dy = nodes[a].y - nodes[b].y;
        d2 = dx * dx + dy * dy;
        if (d2 < b1) { b2 = b1; i2 = i1; b1 = d2; i1 = b; }
        else if (d2 < b2) { b2 = d2; i2 = b; }
      }
      link(a, i1, b1); link(a, i2, b2);
    }
    edges = next;
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
  function draw() {
    var i, x, y, v, tier, lo, hi, rad, px, py, nr, k, a, b, al;

    for (i = 0; i < n; i++) rf[i] += (cur[i] - rf[i]) * EMA;   // temporal damping
    gaussian(rf, rfs, 3);
    for (k = 0; k < nodes.length; k++) {
      nodes[k].x += (nodes[k].tx - nodes[k].x) * EASE;
      nodes[k].y += (nodes[k].ty - nodes[k].y) * EASE;
    }

    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = '#0f0f12';

    ctx.globalAlpha = .2; ctx.lineWidth = .45;
    if (meshPath) ctx.stroke(meshPath);

    ctx.globalAlpha = .36; ctx.lineWidth = .6;
    contours(rfs, .05, .62, .05);

    ctx.fillStyle = '#1a1a20';
    for (tier = 0; tier < 7; tier++) {          // finer tiers = gentler steps
      lo = .13 + tier * .124; hi = lo + .124; rad = .55 + tier * .32;
      ctx.globalAlpha = .18 + tier * .105;
      ctx.beginPath();
      for (y = 0; y < rows; y++)
        for (x = 0; x < cols; x++) {
          i = y * cols + x; v = rf[i];
          if (v < lo || v >= hi) continue;
          px = x * CELL + jx[i]; py = y * CELL + jy[i];
          ctx.moveTo(px + rad, py);
          ctx.arc(px, py, rad, 0, 6.2832);
        }
      ctx.fill();
    }

    // sugar grains, in the interaction blue so they read as a distinct substance
    if (sugar > 0) {
      ctx.fillStyle = '#007CBE';
      for (y = 0; y < rows; y++)
        for (x = 0; x < cols; x++) {
          i = y * cols + x; v = food[i];
          if (v < .05) continue;
          ctx.globalAlpha = Math.min(.7, v * .8);
          ctx.beginPath();
          ctx.arc(x * CELL + jx[i], y * CELL + jy[i], .5 + v * 1.7, 0, 6.2832);
          ctx.fill();
        }
      ctx.fillStyle = '#0f0f12';
    }

    var map = {};
    for (k = 0; k < nodes.length; k++) map[nodes[k].id] = nodes[k];
    ctx.lineWidth = .6;
    for (k = 0; k < edges.length; k += 2) {
      a = map[edges[k]]; b = map[edges[k + 1]];
      if (!a || !b) continue;
      al = Math.min(a.life, b.life) * .42;
      if (al <= 0) continue;
      ctx.globalAlpha = al;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      ctx.stroke();
    }

    ctx.fillStyle = '#0f0f12';
    for (k = 0; k < nodes.length; k++) {
      ctx.globalAlpha = nodes[k].life * .88;
      nr = (1.8 + nodes[k].v * 4) * (.45 + .55 * nodes[k].life);
      ctx.beginPath();
      ctx.arc(nodes[k].x, nodes[k].y, nr, 0, 6.2832);
      ctx.fill();
    }
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
    nodes.length = 0; edges.length = 0;
    seed(14, rand(4242));
    for (var i = 0; i < WARM; i++) {            // grow, then settle the EMA
      gaussian(cur, nbr, R);
      for (var j = 0; j < n; j++) {
        var u = nbr[j], v = cur[j] + DT * (u >= B1 && u <= B2 ? 1 : -1);
        cur[j] = v < 0 ? 0 : v > 1 ? 1 : v;
      }
    }
    rf.set(cur);
    for (i = 0; i < 12; i++) graph();            // let node lives reach full
    return true;
  }

  // ---- the little code window --------------------------------------------
  function buildPanel() {
    var hud = document.createElement('div');
    hud.className = 'hero-hud';

    // the invitation is built here, by the same script that makes clicking do
    // something — so it never advertises an interaction that isn't running
    hint = document.createElement('p');
    hint.className = 'hero-hint';
    var verb = (window.matchMedia && window.matchMedia('(hover: none)').matches)
             ? 'Tap' : 'Click';
    hint.innerHTML = '<span class="dot"></span>' + verb +
                     ' the field to drop sugar \u2014 the cells will grow toward it';
    hud.appendChild(hint);

    panel = document.createElement('pre');
    panel.className = 'hero-code';
    panel.setAttribute('aria-hidden', 'true');
    hud.appendChild(panel);

    host.appendChild(hud);
  }

  function updatePanel() {
    if (!panel) return;
    var alive = 0;
    for (var i = 0; i < n; i++) if (cur[i] > .5) alive++;
    panel.textContent =
      'larger-than-life \u00b7 lattice ' + cols + '\u00d7' + rows + '\n' +
      'u  = gaussian(v, r=' + R + ')\n' +
      '\u0394v = dt \u00b7 (b\u2081 \u2264 u \u2264 b\u2082 ? +1 : \u22121)\n' +
      'v  = clamp(v + \u0394v, 0, 1)\n' +
      'b\u2081=' + B1.toFixed(2) + '  b\u2082=' + B2.toFixed(2) + '  dt=' + DT.toFixed(3) + '\n' +
      '\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n' +
      'step ' + String(steps).padStart(3, '0') + '/' + stopAt +
      '   alive ' + (100 * alive / n).toFixed(1) + '%\n' +
      'nodes ' + String(nodes.length).padStart(4, ' ') +
      '    sugar ' + (sugar > 0 ? sugar.toFixed(2) : '0.00') + '\n' +
      phase + (sugar > 0 ? ' \u2014 growing toward it' : ' \u00b7 click to drop sugar');
  }

  // ---- lifecycle: grow, settle, stop --------------------------------------
  var last = 0, acc = 0, paint = 0, visible = true, looping = false;

  function ensureLoop() {
    if (looping || !visible || steps >= stopAt) return;
    looping = true; last = 0;
    requestAnimationFrame(frame);
  }

  function frame(now) {
    if (!visible) { looping = false; return; }

    var dt = last ? Math.min(140, now - last) : 0;
    last = now;

    var remain = stopAt - steps;

    if (remain <= 0) {
      // budget spent: let the EMA and node eases finish, then stop for good
      if (phase !== 'settled') { phase = 'settled'; paint = 0; }
      paint += dt;
      draw(); updatePanel();
      if (paint > 1400) { looping = false; return; }
      requestAnimationFrame(frame);
      return;
    }

    // ease the step rate down over the last few steps
    var slow = remain < TAIL ? 1 + 2.4 * (1 - remain / TAIL) : 1;
    phase = sugar > 0 ? 'feeding' : (remain < TAIL ? 'settling' : 'growing');

    acc += dt; paint += dt;
    while (acc >= MS * slow && steps < stopAt) { step(); acc -= MS * slow; }
    if (paint >= FPS) { paint = 0; draw(); }
    if (now - lastPanel > 220) { lastPanel = now; updatePanel(); }

    requestAnimationFrame(frame);
  }

  if (!resize()) { if (fallback) fallback.style.visibility = ''; return; }
  buildPanel();
  stopAt = STOP_AT;
  draw(); updatePanel();
  ensureLoop();

  // click (or tap) the field to drop sugar
  function at(ev) {
    var r = cv.getBoundingClientRect(),
        cx = (ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left,
        cy = (ev.touches ? ev.touches[0].clientY : ev.clientY) - r.top;
    feed(cx, cy);
  }
  cv.addEventListener('click', at);
  cv.addEventListener('touchstart', function (e) { at(e); }, { passive: true });

  var rt;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(function () {
      if (!resize()) return;
      stopAt = STOP_AT;
      draw(); updatePanel(); ensureLoop();
    }, 220);
  });

  if (window.IntersectionObserver) {
    new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        visible = e.isIntersecting;
        if (visible && steps < stopAt) ensureLoop();
      });
    }, { threshold: 0 }).observe(host);
  }
})();
