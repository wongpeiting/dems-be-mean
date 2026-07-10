<script>
	import Card from '$lib/components/demo/Card.svelte';
	import Panel from '$lib/components/demo/Panel.svelte';
	import Scroller from '$lib/components/Scroller.svelte';
	import Background from '$lib/components/demo/SimpleBackground.svelte';

	let index = $state(0);
	let offset = $state(0);
	let progress = $state(0);
	let count = $state(0);
</script>

<main class="page">
	<section class="demo">
		<h1>Components demo</h1>
		<p class="intro">
			Start with simple props, then pass markup into a component with snippets, then combine both
			in a more advanced component.
		</p>
	</section>

	<section class="demo">
		<h2>1. Props</h2>
		<p class="intro">
			<code>Card</code> receives strings as props. Change the props, change the output.
		</p>

		<div class="cards">
			<Card title="First card" description="This card uses the default props." />

			<Card
				title="Second card"
				description="Props let a parent customize a child component."
				accent="#2a9d8f"
			/>

			<Card title="Third card" description="Same component, different data." accent="#e76f51" />
		</div>
	</section>

	<section class="demo">
		<h2>2. Snippets</h2>
		<p class="intro">
			<code>Panel</code> receives a <code>content</code> snippet — a chunk of markup defined by the
			parent and rendered inside the child with <code>{'@render content()'}</code>.
		</p>

		<div class="panels">
			<Panel title="Text panel">
				{#snippet content()}
					<p>Any HTML can go here. The parent decides what appears inside the panel.</p>
				{/snippet}
			</Panel>

			<Panel title="List panel">
				{#snippet content()}
					<ul>
						<li>Snippets can include multiple elements</li>
						<li>They are not limited to a single string prop</li>
						<li>Scroller uses this idea for <code>background</code> and <code>foreground</code></li>
					</ul>
				{/snippet}
			</Panel>

			<Panel title="Styled panel">
				{#snippet content()}
					<p class="callout">Custom content can include its own classes and structure.</p>
				{/snippet}
			</Panel>
		</div>
	</section>

	<section class="demo scroller-demo">
		<h2>3. Scroller</h2>
		<p class="intro">
			<code>Scroller</code> uses two named snippets — <code>background</code> and
			<code>foreground</code> — plus bindable props like <code>index</code> and
			<code>count</code>.
		</p>

		<Scroller top={0} bottom={1} debugger={true} bind:index bind:offset bind:progress bind:count>
			{#snippet background()}
				<Background {index} {count} />
			{/snippet}

			{#snippet foreground()}
				<div class="step">This is the first step.</div>
				<div class="step">This is the second step.</div>
				<div class="step">This is the third step.</div>
				<div class="step">This is the fourth step.</div>
				<div class="step">This is the fifth step.</div>
			{/snippet}
		</Scroller>
	</section>
</main>

<style>
	.page {
		max-width: 40rem;
		margin: 0 auto;
		padding: 2rem 1.5rem 3rem;
		font-family: system-ui, sans-serif;
		color: #111;
	}

	.demo + .demo {
		margin-top: 2.5rem;
	}

	h1 {
		margin: 0 0 0.5rem;
		font-size: 1.75rem;
	}

	h2 {
		margin: 0 0 0.5rem;
		font-size: 1.25rem;
	}

	.intro {
		margin: 0 0 1.5rem;
		color: #555;
		line-height: 1.5;
	}

	.cards,
	.panels {
		display: grid;
		gap: 1rem;
	}

	.callout {
		margin: 0;
		padding: 0.75rem 1rem;
		border-radius: 0.375rem;
		background: #eef6fb;
		color: #1d3557;
	}

	.scroller-demo {
		max-width: none;
	}

	.step {
		height: 100vh;
	}
</style>
