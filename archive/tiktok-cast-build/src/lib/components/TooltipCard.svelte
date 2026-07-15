<script>
  import * as d3 from 'd3';

  let { node, onclose } = $props();

  const REGISTER_LABELS = {
    '-3': 'Highly negative',
    '-2': 'Negative',
    '-1': 'Slightly negative',
    '0': 'Neutral',
    '1': 'Slightly positive',
    '2': 'Positive',
    '3': 'Highly positive'
  };

  function registerColor(val) {
    if (val === null || val === undefined) return '#888';
    if (val < 0) return '#c0392b';
    if (val > 0) return '#27ae60';
    return '#888';
  }

  function registerLabel(val) {
    if (val === null || val === undefined) return 'unclassified';
    return REGISTER_LABELS[String(val)] ?? 'unclassified';
  }
</script>

{#if node}
  <div class="tooltip-card">
    <button class="close-btn" onclick={() => onclose?.()}>✕</button>

    <strong class="claim">{node.claim}</strong>
    <p class="intent">{node.intent}</p>

    <span
      class="register-chip"
      style="background:{registerColor(node.register)}"
    >
      {registerLabel(node.register)}
    </span>

    <p class="meta">
      @{node.account}&nbsp;·&nbsp;{node.date}&nbsp;·&nbsp;{d3.format('.2s')(node.views ?? 0)} views
    </p>

    {#if node.dunk}
      <p class="dunk">"{node.dunk}"</p>
    {/if}

    <a
      href="https://www.tiktok.com/@{node.account}/video/{node.id}"
      target="_blank"
      rel="noopener noreferrer"
      class="tiktok-link"
    >Watch on TikTok ↗</a>
  </div>
{/if}

<style>
  .tooltip-card {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    max-height: 55vh;
    max-height: 55svh;
    overflow-y: auto;
    overscroll-behavior: contain;
    background: #fff;
    border-radius: 16px 16px 0 0;
    padding: 20px 16px env(safe-area-inset-bottom, 0px);
    box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.3);
    z-index: 1100;
  }

  .close-btn {
    position: absolute;
    top: 12px;
    right: 12px;
    min-width: 44px;
    min-height: 44px;
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #333;
  }

  .claim {
    display: block;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.4;
    margin: 0 0 10px;
    padding-right: 48px;
    color: #111;
  }

  .intent {
    font-size: 14px;
    line-height: 1.5;
    color: #444;
    margin: 0 0 12px;
  }

  .register-chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 10px;
  }

  .meta {
    font-size: 12px;
    color: #777;
    margin: 8px 0 10px;
  }

  .dunk {
    font-size: 13px;
    color: #555;
    font-style: italic;
    margin: 0 0 10px;
    border-left: 3px solid #ddd;
    padding-left: 10px;
  }

  .tiktok-link {
    display: inline-block;
    font-size: 14px;
    color: #0066cc;
    text-decoration: none;
    margin-top: 4px;
  }

  .tiktok-link:hover {
    text-decoration: underline;
  }
</style>
