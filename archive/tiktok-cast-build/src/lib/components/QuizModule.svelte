<script>
	import ClipCard from './ClipCard.svelte';
	import ScoreSentence from './ScoreSentence.svelte';
	import { QuizState, scoreSentence } from '$lib/quiz.svelte.js';
	import { postGuess, fetchStats } from '$lib/crowd.js';

	let { rounds, seeded = {}, quiz = $bindable() } = $props();

	quiz = new QuizState(rounds);

	let phase = $state('guess'); // 'guess' | 'tell' | 'revealed'
	let lastResult = $state(null);
	let stats = $state(seeded);
	let revealTimer;

	$effect(() => {
		fetchStats(
			rounds.map((r) => r.id),
			seeded
		).then((s) => (stats = s));
	});

	$effect(() => {
		return () => clearTimeout(revealTimer);
	});

	const LABELS = { dem: '🔵 Democrats', rep: '🔴 White House / GOP' };
	const VERDICTS_Y = ['Correct.', 'You got this one.', 'Right — this time.'];
	const VERDICTS_N = ['Nope.', 'Wrong side.', 'Gotcha.'];

	function crowdWrong(id, answer) {
		const s = stats[id];
		if (!s) return null;
		const total = s.dem + s.rep;
		if (total < 20) return null;
		return Math.round((100 * s[answer === 'dem' ? 'rep' : 'dem']) / total);
	}

	function reveal(roundId, res, choice, tellZone) {
		lastResult = {
			...res,
			roundId,
			verdict: (res.correct ? VERDICTS_Y : VERDICTS_N)[quiz.n % 3],
			wrongPct: crowdWrong(roundId, res.answer)
		};
		postGuess({ roundId, choice, ...(tellZone ? { tellZone } : {}) });
		phase = 'revealed';
		revealTimer = setTimeout(() => {
			lastResult = null;
			phase = 'guess';
		}, 1500);
	}

	function tap(choice) {
		if (phase !== 'guess' || !quiz.current) return;
		// Capture roundId BEFORE any commit (quiz.i advances on commit)
		const roundId = quiz.current.id;
		const isTell = !!quiz.current.tell;
		const res = quiz.pick(choice);
		if (isTell) {
			// pick() returned null and set tellPending; wait for zone tap
			phase = 'tell';
			return;
		}
		// Non-tell: pick() called #commit and returned { correct, answer }
		reveal(roundId, res, choice);
	}

	function zone(z) {
		if (phase !== 'tell') return;
		// Capture roundId: quiz.i has already advanced if pick committed, but for tell rounds
		// pick() sets tellPending and doesn't commit, so quiz.i still points to the same round
		// quiz.current is still the tell round at this point
		const roundId = quiz.current.id;
		const res = quiz.logTell(z);
		if (!res) return;
		const choice = quiz.guesses.at(-1)?.choice;
		reveal(roundId, res, choice, z);
	}

	const shownRound = $derived(
		phase === 'revealed' ? rounds.find((r) => r.id === lastResult?.roundId) : quiz.current
	);
</script>

{#if shownRound}
	<div
		class="quiz"
		style:--reveal={lastResult
			? lastResult.answer === 'dem'
				? '#5588d5'
				: '#d5564c'
			: null}
	>
		{#if phase === 'tell'}
			<p class="prompt">Before we tell you — tap the thing that gave it away.</p>
		{/if}
		<ClipCard round={shownRound} revealed={phase === 'revealed'} onzone={phase === 'tell' ? zone : null} />
		{#if phase === 'revealed'}
			<p class="verdict" aria-live="polite">
				{lastResult.verdict} It's from <b>@{shownRound.account}</b>.
				{#if lastResult.wrongPct !== null && lastResult.wrongPct !== undefined}{lastResult.wrongPct}% of readers got this wrong.{/if}
			</p>
		{:else if phase === 'guess'}
			<div class="buttons">
				{#each quiz.buttonOrder as side}
					<button class={side} onclick={() => tap(side)}>{LABELS[side]}</button>
				{/each}
			</div>
		{/if}
	</div>
{:else}
	<p class="done">That's every clip we prepared. {scoreSentence(quiz.n, quiz.correct)}</p>
{/if}
<ScoreSentence n={quiz.n} correct={quiz.correct} />

<style>
	.quiz {
		max-width: 390px;
		margin: 0 auto;
		padding: 0 12px;
	}
	.buttons {
		display: flex;
		gap: 10px;
		justify-content: center;
		margin-top: 12px;
	}
	button {
		flex: 1;
		max-width: 190px;
		min-height: 44px;
		padding: 14px 8px;
		border: none;
		border-radius: 22px;
		color: #fff;
		font-weight: 700;
		font-size: 15px;
		cursor: pointer;
	}
	button.dem {
		background: #5588d5;
	}
	button.rep {
		background: #d5564c;
	}
	.verdict,
	.prompt {
		text-align: center;
		min-height: 44px;
		margin-top: 12px;
		font-size: 15px;
	}
	.done {
		text-align: center;
		padding: 24px 12px;
		font-size: 16px;
		max-width: 390px;
		margin: 0 auto;
	}
</style>
