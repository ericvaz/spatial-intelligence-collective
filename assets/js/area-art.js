/* Research-area artwork.

   The five drawings ship as static SVG files. Here they are pulled in and
   inlined so the card can reach into them on hover: contour lines travel as a
   wave, the point cloud drifts, signals run the network edges, a ripple leaves
   the centre of the complexity graph, and the quantum orbitals spin. If the
   fetch fails the original <img> simply stays put. */
(function () {
  var thumbs = document.querySelectorAll('.card .thumb img[src*="area-"]');
  if (!thumbs.length || !window.fetch) return;

  function rnd(a, b) { return a + Math.random() * (b - a); }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  /* Per-drawing seeding: the phases, offsets and speeds that make the motion
     read as a field rather than one synchronised twitch. */
  var seed = {
    /* contours: one wave, phase-shifted down the stack */
    geocomputation: function (svg) {
      each(svg.querySelectorAll('path'), function (p, i) {
        p.style.setProperty('--i', i);
      });
    },
    /* points: every other one drifts its own way, the rest hold the frame */
    spatial: function (svg) {
      each(svg.querySelectorAll('circle'), function (c, i) {
        if (i % 2) return;
        c.classList.add('drift');
        c.style.setProperty('--x', rnd(-3, 3).toFixed(2) + 'px');
        c.style.setProperty('--y', rnd(-3, 3).toFixed(2) + 'px');
        c.style.setProperty('--t', rnd(1.7, 3.6).toFixed(2) + 's');
        c.style.setProperty('--d', (-rnd(0, 3)).toFixed(2) + 's');
      });
    },
    /* network: signals leave along the edges, nodes answer behind them */
    geoai: function (svg) {
      each(svg.querySelectorAll('line'), function (l, i) {
        l.style.setProperty('--d', (-i * 0.09).toFixed(2) + 's');
      });
      each(svg.querySelectorAll('circle'), function (c, i) {
        c.style.setProperty('--d', (-i * 0.13).toFixed(2) + 's');
      });
    },
    /* graph: the ripple is timed by distance from the centre node */
    complexity: function (svg) {
      each(svg.querySelectorAll('circle'), function (c) {
        var dx = +c.getAttribute('cx') - 150, dy = +c.getAttribute('cy') - 75;
        c.style.setProperty('--d', (-Math.sqrt(dx * dx + dy * dy) / 90).toFixed(2) + 's');
      });
      each(svg.querySelectorAll('line'), function (l, i) {
        l.style.setProperty('--o', l.getAttribute('opacity') || 1);
        l.style.setProperty('--d', (-i * 0.04).toFixed(2) + 's');
      });
    },
    /* orbitals: each shell keeps its own angle and turns at its own rate */
    quantum: function (svg) {
      each(svg.querySelectorAll('ellipse'), function (e, i) {
        e.style.setProperty('--base', (i * 60) + 'deg');
        e.style.setProperty('--t', (9 + i * 3) + 's');
        e.removeAttribute('transform');
      });
      each(svg.querySelectorAll('circle'), function (c, i) {
        c.style.setProperty('--o', c.getAttribute('opacity') || 1);
        c.style.setProperty('--d', (-(i % 23) * 0.13).toFixed(2) + 's');
      });
    }
  };

  each(thumbs, function (img) {
    var src = img.getAttribute('src'),
        kind = (src.match(/area-([a-z]+)\.svg/) || [])[1];
    if (!kind || !seed[kind]) return;

    fetch(src)
      .then(function (r) { return r.ok ? r.text() : Promise.reject(r.status); })
      .then(function (markup) {
        var host = document.createElement('div');
        host.innerHTML = markup;
        var svg = host.querySelector('svg');
        if (!svg || !img.parentNode) return;
        svg.setAttribute('aria-hidden', 'true');
        svg.setAttribute('preserveAspectRatio', 'xMidYMid slice');
        svg.setAttribute('class', 'art art-' + kind);
        seed[kind](svg);
        img.parentNode.replaceChild(svg, img);
      })
      .catch(function () { /* the static drawing stays */ });
  });
})();
