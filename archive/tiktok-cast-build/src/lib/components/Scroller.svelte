<script>
	import { onMount, untrack } from 'svelte';

	let {
		top = 0,
		bottom = 1,
		threshold = 0.5,
		/** CSS selector for scroll steps. Defaults to direct children of the foreground. */
		query = ':scope > *',
		parallax = false,
		debugger: showDebugger = false,
		index = $bindable(0),
		count = $bindable(0),
		offset = $bindable(0),
		progress = $bindable(0),
		visible = $bindable(false),
		background,
		foreground
	} = $props();

	let outer;
	let foregroundEl;
	let backgroundEl;
	let wh = $state(0);
	let fixed = $state(false);
	let offset_top = $state(0);
	let width = $state(1);

	let sections = [];

	const top_px = $derived(Math.round(top * wh));
	const bottom_px = $derived(Math.round(bottom * wh));
	const threshold_px = $derived(Math.round(threshold * wh));

	const style = $derived(
		`position: ${fixed ? 'fixed' : 'absolute'}; top: 0; transform: translate(0, ${offset_top}px); z-index: 1;`
	);

	const widthStyle = $derived(fixed ? `width:${width}px;` : '');

	const sectionProgress = $derived(count > 0 ? ((index + 1) / count) * 100 : 0);
	const offsetProgress = $derived(Math.min(100, Math.max(0, offset * 100)));
	const totalProgress = $derived(Math.min(100, Math.max(0, progress * 100)));

	function update() {
		if (!foregroundEl) return;

		const bcr = outer.getBoundingClientRect();
		width = bcr.right - bcr.left;

		const fg = foregroundEl.getBoundingClientRect();
		const bg = backgroundEl.getBoundingClientRect();

		visible = fg.top < wh && fg.bottom > 0;

		const foreground_height = fg.bottom - fg.top;
		const background_height = bg.bottom - bg.top;

		const available_space = bottom_px - top_px;
		progress = (top_px - fg.top) / (foreground_height - available_space);

		if (progress <= 0) {
			offset_top = 0;
			fixed = false;
		} else if (progress >= 1) {
			offset_top = parallax
				? foreground_height - background_height
				: foreground_height - available_space;
			fixed = false;
		} else {
			offset_top = parallax
				? Math.round(top_px - progress * (background_height - available_space))
				: top_px;
			fixed = true;
		}

		for (let i = 0; i < sections.length; i++) {
			const section = sections[i];
			const { top: sectionTop } = section.getBoundingClientRect();

			const next = sections[i + 1];
			const sectionBottom = next ? next.getBoundingClientRect().top : fg.bottom;

			offset = (threshold_px - sectionTop) / (sectionBottom - sectionTop);
			if (sectionBottom >= threshold_px) {
				index = i;
				break;
			}
		}
	}

	$effect(() => {
		top;
		bottom;
		threshold;
		parallax;
		untrack(() => update());
	});

	onMount(() => {
		sections = [...foregroundEl.querySelectorAll(query)];
		count = sections.length;
		update();
	});
</script>

<svelte:window bind:innerHeight={wh} onscroll={update} onresize={update} />

<div class="scroller-outer" bind:this={outer}>
	<div class="background-container" style="{style}{widthStyle}">
		<div class="background" bind:this={backgroundEl}>
			{@render background()}
		</div>
	</div>

	<div class="foreground" bind:this={foregroundEl}>
		{@render foreground()}
	</div>
</div>

{#if showDebugger}
	<div class="debugger" aria-hidden="true">
		<div class="debugger-row">
			<p class="debugger-label">
				current section: <strong>{index + 1}/{count}</strong>
			</p>
			<div class="debugger-bar">
				<div class="debugger-fill" style:width="{sectionProgress}%"></div>
			</div>
		</div>

		<div class="debugger-row">
			<p class="debugger-label">offset in current section</p>
			<div class="debugger-bar">
				<div class="debugger-fill" style:width="{offsetProgress}%"></div>
			</div>
		</div>

		<div class="debugger-row">
			<p class="debugger-label">total progress</p>
			<div class="debugger-bar">
				<div class="debugger-fill" style:width="{totalProgress}%"></div>
			</div>
		</div>
	</div>
{/if}

<style>
	.scroller-outer {
		display: block;
		position: relative;
	}

	.background {
		display: block;
		position: relative;
		width: 100%;
	}

	.foreground {
		display: block;
		position: relative;
		z-index: 2;
	}

	.foreground::after {
		content: ' ';
		display: block;
		clear: both;
	}

	.background-container {
		display: block;
		position: absolute;
		width: 100%;
		max-width: 100%;
		pointer-events: none;
		will-change: transform;
	}

	.debugger {
		position: fixed;
		top: 1rem;
		right: 1rem;
		z-index: 9999;
		width: 14rem;
		padding: 0.75rem;
		border-radius: 0.25rem;
		background: rgb(45 42 40 / 0.92);
		color: white;
		font-family: system-ui, sans-serif;
		font-size: 0.75rem;
		line-height: 1.4;
		pointer-events: none;
	}

	.debugger-row + .debugger-row {
		margin-top: 0.625rem;
	}

	.debugger-label {
		margin: 0 0 0.25rem;
	}

	.debugger-bar {
		height: 0.375rem;
		border-radius: 999px;
		background: rgb(255 255 255 / 0.15);
		overflow: hidden;
	}

	.debugger-fill {
		height: 100%;
		border-radius: 999px;
		background: #6eb5ff;
		transition: width 0.1s linear;
	}
</style>
