<script>
  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import TooltipCard from './TooltipCard.svelte';
  import { nearestNode, emotionCentroids } from '$lib/interior-utils.js';

  let { data, onclose } = $props();

  let container = $state(null);
  let canvas = $state(null);
  let selected = $state(null);

  // These are set in onMount — not reactive state (canvas internals)
  let ctx = null;
  let W = 0;
  let H = 0;
  let transform = null;
  let dirty = false;
  let atlasImages = [];
  let atlasLoaded = [];
  let zoomBehavior = null;
  let d3Selection = null;
  let resizeHandler = null;
  let bodyOverflowWas = '';
  let onPointerDown = null;
  let onClick = null;

  // Cache centroids for label drawing
  let centroids = null;

  // Pointer tracking for tap vs drag
  let pointerDownX = 0;
  let pointerDownY = 0;

  function setupCanvas() {
    if (!canvas || !container) return;
    const dpr = window.devicePixelRatio || 1;
    W = container.offsetWidth;
    H = container.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function drawFrame() {
    if (!ctx || !transform) return;
    dirty = false;

    ctx.clearRect(0, 0, W, H);

    const nodes = data.nodes;
    const k = transform.k;
    const margin = Math.ceil(7 * k) + 10;

    if (k < 3) {
      // Smoke plume mode
      ctx.filter = 'blur(6px)';
      ctx.globalAlpha = 0.55;
      for (const n of nodes) {
        const sx = transform.applyX(n.x * W);
        const sy = transform.applyY(n.y * H);
        // Offscreen culling
        if (sx < -margin || sx > W + margin || sy < -margin || sy > H + margin) continue;
        ctx.beginPath();
        ctx.arc(sx, sy, 10, 0, 2 * Math.PI);
        ctx.fillStyle = n.color;
        ctx.fill();
      }
      ctx.filter = 'none';
      ctx.globalAlpha = 1;

      // Emotion cluster labels
      if (!centroids) {
        centroids = emotionCentroids(nodes);
      }
      ctx.font = '600 12px system-ui';
      ctx.fillStyle = 'rgba(255,255,255,0.8)';
      ctx.textAlign = 'center';
      for (const [emotion, c] of centroids) {
        const sx = transform.applyX(c.x * W);
        const sy = transform.applyY(c.y * H);
        ctx.fillText(emotion, sx, sy);
      }
    } else {
      // Thumbnail mode
      ctx.filter = 'none';
      ctx.globalAlpha = 1;
      const s = 14 * k;
      for (const n of nodes) {
        const sx = transform.applyX(n.x * W);
        const sy = transform.applyY(n.y * H);
        // Offscreen culling
        if (sx < -margin || sx > W + margin || sy < -margin || sy > H + margin) continue;
        if (atlasLoaded[n.ai]) {
          ctx.drawImage(atlasImages[n.ai], n.ax, n.ay, 96, 96, sx - s / 2, sy - s / 2, s, s);
          ctx.strokeStyle = n.side === 'dem' ? '#5588d5' : '#d5564c';
          ctx.lineWidth = 2;
          ctx.strokeRect(sx - s / 2, sy - s / 2, s, s);
        } else {
          ctx.fillStyle = n.color;
          ctx.globalAlpha = 0.55;
          ctx.fillRect(sx - s / 2, sy - s / 2, s, s);
          ctx.globalAlpha = 1;
        }
      }
    }
  }

  function scheduleRedraw() {
    if (!dirty) {
      dirty = true;
      requestAnimationFrame(drawFrame);
    }
  }

  onMount(() => {
    setupCanvas();

    // Load atlas images
    atlasImages = (data.atlases ?? []).map((path, i) => {
      atlasLoaded[i] = false;
      const img = new Image();
      img.onload = () => {
        atlasLoaded[i] = true;
        scheduleRedraw();
      };
      img.src = `${base}/${path}`;
      return img;
    });

    // Cache centroids early
    centroids = emotionCentroids(data.nodes);

    // Set up d3 zoom
    transform = d3.zoomIdentity;

    zoomBehavior = d3
      .zoom()
      .scaleExtent([1, 8])
      .on('zoom', (e) => {
        transform = e.transform;
        scheduleRedraw();
      });

    d3Selection = d3.select(canvas);
    d3Selection.call(zoomBehavior);

    // Pointer tracking for tap detection
    onPointerDown = (e) => {
      pointerDownX = e.offsetX;
      pointerDownY = e.offsetY;
    };

    onClick = (e) => {
      const dx = e.offsetX - pointerDownX;
      const dy = e.offsetY - pointerDownY;
      const moved = Math.sqrt(dx * dx + dy * dy);
      if (moved >= 8) return; // was a drag, not a tap

      const [dataX, dataY] = transform.invert([e.offsetX, e.offsetY]);
      const nx = dataX / W;
      const ny = dataY / H;
      const kW = transform.k * W;
      const kH = transform.k * H;
      const found = nearestNode(data.nodes, nx, ny, 24, kW, kH);
      selected = found || null;
    };

    canvas.addEventListener('pointerdown', onPointerDown);
    canvas.addEventListener('click', onClick);

    // Initial draw
    scheduleRedraw();

    // Body overflow
    bodyOverflowWas = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Resize handler
    resizeHandler = () => {
      setupCanvas();
      scheduleRedraw();
    };
    window.addEventListener('resize', resizeHandler);
  });

  onDestroy(() => {
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler);
    }
    if (d3Selection && zoomBehavior) {
      d3Selection.on('.zoom', null);
    }
    if (canvas && onPointerDown) {
      canvas.removeEventListener('pointerdown', onPointerDown);
    }
    if (canvas && onClick) {
      canvas.removeEventListener('click', onClick);
    }
    document.body.style.overflow = bodyOverflowWas;
  });
</script>

<div class="interior-overlay" bind:this={container}>
  <canvas bind:this={canvas}></canvas>

  <button class="close-btn" onclick={() => onclose?.()}>✕</button>

  <TooltipCard node={selected} onclose={() => (selected = null)} />
</div>

<style>
  .interior-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: #0b0b12;
    overflow: hidden;
  }

  canvas {
    display: block;
    width: 100%;
    height: 100%;
    touch-action: none;
  }

  .close-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    min-width: 44px;
    min-height: 44px;
    background: rgba(255, 255, 255, 0.15);
    border: none;
    border-radius: 22px;
    color: #fff;
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1010;
  }

  .close-btn:hover {
    background: rgba(255, 255, 255, 0.25);
  }
</style>
