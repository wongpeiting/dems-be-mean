<script>
	import Scroller from '$lib/components/Scroller.svelte';
	import { base } from '$app/paths';
	import HeatField from './HeatField.svelte';
	import Montage from './Montage.svelte';
	import CastPack from './CastPack.svelte';
	import MeanSpark from './MeanSpark.svelte';
	import PayoffSwarm from './PayoffSwarm.svelte';
	// import Flow from './Flow.svelte'; // flow/Sankey section removed for now
	import data from '$lib/data/dunk_hero.json';
	import trollImgs from '$lib/data/troll.json';
	import worduse from '$lib/data/worduse.json';
	import postmeta from '$lib/data/postmeta.json';
	import payoff from '$lib/data/payoff.json';

	let index = $state(0);
	let progress = $state(0);
	let count = $state(0);
	let vw = $state(1200); // viewport width → drives mobile chart sizing
	const isMobile = $derived(vw <= 640);

	// opening: scrolly cards over the tiled video wall
	let openIndex = $state(0);
	let openProgress = $state(0);
	const openCards = [
		'You’re doomscrolling TikTok.',
		'A screaming heavy-metal edit floods your screen — a bald eagle, fireworks, a man with glowing laser eyes, a voice booming <em>God bless America.</em>',
		'It’s aggressively patriotic and completely unhinged. You can’t tell if it’s sincere, a joke, or both.',
		'You tap the profile, expecting a teenager, a troll or a shitposter.',
		'Instead, you find @democrats, the official TikTok account of the Democratic National Committee.',
		'You scroll. It’s the same energy, post after post.'
	];

	// headline glitch (muffinman-style): the word is sliced into horizontal strips that each
	// displace + get a chromatic drop-shadow on their own slow, off-phase cycle → a quiet,
	// occasional "something's wrong" glitch rather than a constant jitter.
	const glitchStrips = [
		{ clip: 'inset(0 0 84% 0)', v: 'a', dur: '7s', delay: '0s' },
		{ clip: 'inset(22% 0 60% 0)', v: 'b', dur: '8.5s', delay: '-1.4s' },
		{ clip: 'inset(44% 0 40% 0)', v: 'a', dur: '6.4s', delay: '-3.1s' },
		{ clip: 'inset(62% 0 22% 0)', v: 'b', dur: '9s', delay: '-0.7s' },
		{ clip: 'inset(80% 0 2% 0)', v: 'a', dur: '7.7s', delay: '-4.2s' }
	];

	// archived opening montage act (its own scroller)
	let introIndex = $state(0);
	let introProgress = $state(0);
	let introCount = $state(0);
	const introSteps = [
		'You’re doomscrolling TikTok.',
		'Another hyperactive, irony-soaked Gen Z montage fills your screen.',
		'You notice the highly recognizable figure of President Donald Trump composited with rainbows, sparkling stars, floating hearts and glitter explosions.',
		'Everything is aggressively cheerful, but the effect is unmistakably sarcastic.',
		'You tap the profile.',
		'@democrats. The official TikTok account of the Democratic National Committee.',
		'<span class="fg-wrap">You scroll on to find another post that presents him like an entry in a field guide:<span class="fieldguide"><b>WHAT IS THAT CREATURE?</b>SCIENTIFIC NAME: DONALD JOHN TRUMP<br>COMMONLY REFERRED TO AS: UGLY :(</span></span>',
		'The posts are definitely entertaining. But you also wonder what official political accounts have become in the race for attention, and whether there are any limits left 👀'
	];

	// --- "type an insult" interaction, with typo tolerance ----------------------
	const lexMeta = worduse.__meta ?? { dLines: 1, rLines: 1 };
	const lexKeys = Object.keys(worduse).filter((k) => k !== '__meta');
	let typed = $state('');
	let answered = $state(false);
	let skipped = $state(false);
	// the story stays gated until the reader answers the prompt or explicitly skips
	const gateOpen = $derived(answered || skipped);
	const norm = (s) => s.toLowerCase().replace(/[^a-z']/g, '');
	// lemma-ish variants so plurals/tenses match (idiots→idiot, called→call…)
	function variants(w) {
		const v = new Set([w]);
		if (w.endsWith('s')) v.add(w.slice(0, -1));
		else v.add(w + 's');
		if (w.endsWith('es')) v.add(w.slice(0, -2));
		if (w.endsWith('ies')) v.add(w.slice(0, -3) + 'y');
		if (w.endsWith('ed')) {
			v.add(w.slice(0, -2));
			v.add(w.slice(0, -1));
		}
		if (w.endsWith('ing')) {
			v.add(w.slice(0, -3));
			v.add(w.slice(0, -3) + 'e');
		}
		return [...v];
	}
	// bounded Damerau–Levenshtein (OSA): like edit distance, but an ADJACENT swap counts as
	// one edit, so transposition typos match (idoit→idiot, d=1). 99 if it exceeds the cap.
	function dist(a, b, cap) {
		const m = a.length,
			n = b.length;
		if (Math.abs(m - n) > cap) return 99;
		const d = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
		for (let i = 0; i <= m; i++) d[i][0] = i;
		for (let j = 0; j <= n; j++) d[0][j] = j;
		for (let i = 1; i <= m; i++) {
			let row = 99;
			for (let j = 1; j <= n; j++) {
				const cost = a[i - 1] === b[j - 1] ? 0 : 1;
				d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
				if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
					d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1); // adjacent transposition
				}
				row = Math.min(row, d[i][j]);
			}
			if (row > cap) return 99; // early out
		}
		return d[m][n];
	}
	// exact → variant → fuzzy(typo). Returns {word, t, l, corrected} or null.
	function lookup(raw) {
		const w = norm(raw);
		if (w.length < 2) return null;
		for (const v of variants(w)) if (worduse[v]) return { word: v, ...worduse[v] };
		// No fuzzy match for short words: a single edit on a ≤4-letter word usually lands on
		// an unrelated real word (cat→cut, bat→ban). Only a single typo for medium words,
		// two for genuinely long ones (where "faggot"→"forgot" style collisions can't happen).
		const cap = w.length <= 4 ? 0 : w.length >= 8 ? 2 : 1;
		if (cap === 0) return null;
		let bestK = null,
			bestD = 99;
		for (const k of lexKeys) {
			const d = dist(w, k, cap);
			if (d < bestD || (d === bestD && bestK && worduse[k].t && !worduse[bestK].t)) {
				bestD = d;
				bestK = k;
			}
		}
		if (bestK && bestD <= cap) return { word: bestK, ...worduse[bestK], corrected: bestK !== w };
		return null;
	}
	let result = $derived(answered ? lookup(typed) : null);
	// collapse repeated targets: group the example lines by who they were aimed at
	const exGroups = $derived.by(() => {
		if (!result?.ex) return [];
		const m = new Map();
		for (const e of result.ex) {
			const k = e.t || '';
			if (!m.has(k)) m.set(k, []);
			m.get(k).push(e);
		}
		return [...m.entries()].map(([t, items]) => ({ t, items }));
	});
	const vidOf = (u) => (u || '').match(/video\/(\d+)/)?.[1];
	const fmtViews = (n) =>
		n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? Math.round(n / 1e3) + 'K' : '' + n;
	const fmtDate = (d) =>
		d && d.length === 8
			? new Date(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8)).toLocaleDateString('en-US', {
					month: 'short',
					day: 'numeric',
					year: 'numeric'
				})
			: '';
	// nice words that show up in dunk lines (often sarcastically) but plainly aren't insults —
	// call it out instead of pretending "beautiful" is a put-down
	const NICE = new Set(
		'beautiful beauty great greatness wonderful lovely love nice kind good goodness amazing awesome sweet cute happy joy gorgeous perfect brilliant fantastic excellent smart strong brave hero honest gentle friend friendly pretty fun cool wise talented generous thoughtful adorable charming graceful wholesome angel sunshine darling precious grateful hope kindness caring warm delightful'.split(
			' '
		)
	);
	const niceWord = $derived(answered && variants(norm(typed)).some((v) => NICE.has(v)));
	function askSubmit(e) {
		e.preventDefault();
		generated = false;
		if (norm(typed).length >= 2) answered = true;
	}
	// "generate one for me": pull a real @democrats insult (a dunk word aimed at someone)
	let generated = $state(false);
	const INSULT_POOL = 'fascist clown loser weird creep coward liar fraud racist criminal crook conman bully extremist hypocrite grifter sellout traitor puppet snowflake wimp pathetic desperate unhinged deranged felon idiot moron buffoon dictator wannabe stooge chicken cruel corrupt spineless clueless stupid fat ugly dumb dumbass gross nasty weirdo greedy fake sad mad pig scared weak mean'.split(' ');
	function generateInsult() {
		const pool = INSULT_POOL.filter((w) => worduse[w] && worduse[w].t);
		const src = pool.length ? pool : lexKeys.filter((k) => worduse[k].t);
		let pick = src[Math.floor(Math.random() * src.length)];
		if (pick === typed && src.length > 1)
			pick = src[(src.indexOf(pick) + 1) % src.length]; // avoid repeating the same one
		typed = pick;
		generated = true;
		answered = true;
	}
	// how much more (or less) often the Democrats reach for this word than the GOP side,
	// compared dunk-for-dunk (rate per dunk line, not raw counts, since the corpora differ)
	const compare = $derived.by(() => {
		if (!result) return null;
		const d = result.d ?? 0,
			r = result.r ?? 0;
		// bars are proportional to the raw counts shown beside them, so the lengths match the
		// numbers. (Rate-per-post would be a fairer cross-account comparison, but the corpora
		// differ ~3× in size, which made a "2" bar nearly as long as a "7" — bar vs number lied.)
		const maxC = Math.max(d, r) || 1;
		let note;
		if (r === 0) note = 'The Republican side hasn’t reached for it.';
		else if (d / r >= 1.25) note = `The Democrats reach for it about ${(d / r).toFixed(1)}× as often.`;
		else if (r / d >= 1.25)
			note = `The Republican side reaches for it ${(r / d).toFixed(1)}× as often.`;
		else note = 'Both sides reach for it about equally often.';
		return {
			d,
			r,
			demPct: (d / maxC) * 100,
			repPct: (r / maxC) * 100,
			note
		};
	});

	// Two phases. REVEAL: the field builds over time as you scroll (with a teaching
	// pause partway through). ANNOTATE: the field is fully revealed and each card
	// spotlights a group of words to talk about.
	const cards = [
		{
			tone: 'post',
			vh: 200,
			h: '@democrats’ attacks went personal',
			p: 'The findings show that as the account adopted the language of the reply guy – such as “btw,” “wtf,” and other casual profanities – it also became more likely to attack appearance and the body instead of policy or conduct.',
			group: ['fuck', 'shit', 'wtf', 'chud', 'fat', 'ugly', 'bro', 'lol', 'btw'],
			videos: [
				{ id: '7621282572986813709', cap: 'you’ll always find your way back home ✨', views: 558400, date: '20260325' },
				{ id: '7644980788047383821', cap: 'ugly inside and out', views: 299300, date: '20260528' },
				{ id: '7651243755499965710', cap: 'the retirement home is calling', views: 21500000, date: '20260614' },
				{ id: '7652457956365176078', cap: 'rarest species of chud', views: 3600000, date: '20260617' }
			]
		},
		{
			tone: 'pre',
			vh: 190,
			h: 'It did not start here',
			p: 'Earlier posts attacked politicians for what they did, not what they looked like. They centered on things like <em>Kevin</em> <em>McCarthy</em>’s <em>speakership</em>, <em>extremist</em> Republicans, and voting records, in a tone that was procedural and on message.',
			group: ['mccarthy', 'speakership', 'speaker', 'voted', 'against', 'extremist', 'maga', 'republicans', 'republican', 'abortion', 'desantis', 'kevin', 'ron', 'brandon', 'lost', 'weird', 'power', 'never'],
			videos: [
				{ id: '7296354324144475438', cap: 'GOP Speaker Mike Johnson, everybody…', views: 46900, date: '20231101' },
				{ id: '7299317698079542570', cap: 'Red flags.', views: 40200, date: '20231109' },
				{ id: '7310701306128354606', cap: 'the “new generation” of conservative leaders', views: 50700, date: '20231209' },
				{ id: '7426829046127938862', cap: 'voted against protecting IVF 🤔', views: 22300, date: '20241017' }
			]
		},
		{
			tone: 'post',
			vh: 190,
			h: 'Then, one subject takes over',
			p: 'In the ramp up to the more profane and personal approach, the Democrats targeted Trump’s links to <em>Jeffrey</em> <em>Epstein</em>. The Epstein <em>files</em> and calls to <em>release</em> them took center stage.',
			group: ['epstein', 'files', 'jeffrey', 'release'],
			videos: [
				{ id: '7603134429913009422', cap: 'hmmmm', views: 2700000, date: '20260204' },
				{ id: '7608603519829970189', cap: 'think he got the message?', views: 986000, date: '20260219' },
				{ id: '7639028702294150413', cap: 'lmao', views: 269700, date: '20260512' },
				{ id: '7648015319260269837', cap: '😩💔', views: 1000000, date: '20260605' }
			]
		},
		{
			tone: 'post',
			vh: 190,
			h: 'Oligarchy also in the spotlight',
			p: 'Before the pivot, another strain of attacks centered on Trump’s protection of <em>billionaires</em>, his ties to <em>Elon</em> <em>Musk</em>, and his proposed $300 million <em>ballroom</em>. Slowly the institutional voice started making way for uncensored profanity, including phrases like “f--ka-- ballroom”.',
			group: ['elon', 'musk', 'billionaires', 'ballroom', 'money', 'vacation'],
			videos: [
				{ id: '7462073823316217134', cap: '“an oligarchy is taking shape”', views: 4700000, date: '20250120' },
				{ id: '7462488811189112107', cap: 'oligarchy, defined', views: 2100000, date: '20250121' },
				{ id: '7563419444672859447', cap: 'the golden ballroom', views: 4300000, date: '20251020' },
				{ id: '7641259921287286029', cap: 'can’t afford gas 😬', views: 10000000, date: '20260518' }
			]
		}
	];
	// The reveal has two scripted PAUSES: a teaching pause early on, and a pause exactly
	// at the election line where the account's tone escalates. The clock holds at each.
	const REVEAL1_VH = 170; // playhead 0 → P1 (first few words appear)
	const TEACH_VH = 150; // clock holds at P1 while the how-to-read card is up
	const REVEAL2A_VH = 210; // playhead P1 → P2 (up to the election)
	const LOSSPAUSE_VH = 140; // clock holds at the election line
	const REVEAL2B_VH = 260; // playhead P2 → 1 (post-loss escalation)
	const SETTLE_VH = 120; // hold the finished wall before annotating
	const P1 = 0.15; // clock position held during the teaching pause
	const P2 = data.span?.lossXr ?? 0.34; // clock position of the "Trump wins election" line
	const REVEAL_TOTAL = REVEAL1_VH + TEACH_VH + REVEAL2A_VH + LOSSPAUSE_VH + REVEAL2B_VH;

	const totalVh = REVEAL_TOTAL + SETTLE_VH + cards.reduce((s, c) => s + c.vh, 0);
	const fA = REVEAL1_VH / totalVh;
	const fB = (REVEAL1_VH + TEACH_VH) / totalVh;
	const fC = (REVEAL1_VH + TEACH_VH + REVEAL2A_VH) / totalVh;
	const fD = (REVEAL1_VH + TEACH_VH + REVEAL2A_VH + LOSSPAUSE_VH) / totalVh;
	const fE = REVEAL_TOTAL / totalVh;
	// piecewise clock: ramp → teach hold → ramp → LOSS hold → ramp → settle
	function playheadOf(p) {
		if (p <= fA) return (p / fA) * P1;
		if (p <= fB) return P1; // teaching pause
		// reach the election point at ~75% of 2a so the now-line sits on the marker by the pause
		if (p <= fC) return Math.min(P2, P1 + ((p - fB) / ((fC - fB) * 0.75)) * (P2 - P1));
		if (p <= fD) return P2; // loss pause (held at the election line)
		if (p <= fE) return Math.min(1, P2 + ((p - fD) / ((fE - fD) * 0.72)) * (1 - P2));
		return 1;
	}
	const playhead = $derived(playheadOf(progress));

	// sections: 0 reveal1, 1 teach, 2 reveal2a, 3 losspause, 4 reveal2b, 5 settle,
	//           6..10 cards, 11 explore intro, 12 explore space
	const teaching = $derived(index === 1);
	const lossPausing = $derived(index === 3);
	const activeCard = $derived(index >= 6 && index < 6 + cards.length ? cards[index - 6] : null);
	const highlight = $derived(activeCard ? activeCard.group : null);
	const annotating = $derived(!!activeCard);
	// after the annotation cards, a final no-card beat lights the whole field and turns on
	// hover: mouse over any word to see its harshest line and clip
	const exploring = $derived(index >= 6 + cards.length);

	// the payoff: the meanness line + what it's made of
	// payoff: two inline Mean-o-meter charts that play their reveal once, on entering view
	let meanProg = $state(0);
	let cmpProg = $state(0);
	let payoffShown = $state(false);
	// median views per @democrats post since the loss, by crudeness level (0..3).
	// Pooled through the July 9 scrape; a clean monotonic staircase.
	const crudeTiers = [
		{ k: 0, label: 'Institutional', desc: 'on-message, no edge', views: 370100, color: '#565b63' },
		{ k: 1, label: 'Edgy', desc: 'informal, a little sharp', views: 558400, color: '#9c6790' },
		{ k: 2, label: 'Crude', desc: 'insults, appearance jabs', views: 816250, color: '#a8478c' },
		{ k: 3, label: 'Crass', desc: 'vulgarity, body-shaming', views: 1000000, color: '#7d2d60' }
	];
	const crudeMax = 1000000;
	const fmtV = (n) => (n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : Math.round(n / 1e3) + 'K');
	// facet each account down to its OWN active lifetime (its non-null run of months)
	const MON3 = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
	const fmtRange = (ms) =>
		`${MON3[+ms[0].slice(5, 7) - 1]} ${ms[0].slice(0, 4)} – ${MON3[+ms[ms.length - 1].slice(5, 7) - 1]} ${ms[ms.length - 1].slice(0, 4)}`;
	function facetData(key, postLoss) {
		const arr = payoff.series[key].vals;
		let lo = 0;
		while (lo < arr.length && arr[lo] == null) lo++;
		// DESKTOP keeps each account's full lifetime (unchanged); only MOBILE narrows to
		// post-loss so all three small-multiples fit in one screen.
		if (postLoss) lo = Math.max(lo, payoff.electionIdx);
		let hi = arr.length - 1;
		while (hi >= 0 && arr[hi] == null) hi--;
		const vals = arr.slice(lo, hi + 1);
		const monthsList = payoff.months.slice(lo, hi + 1);
		const eli = payoff.electionIdx - lo;
		return { vals, monthsList, electionIdx: eli >= 0 && eli < vals.length ? eli : null };
	}
	const facets = $derived([
		{ key: 'democrats', label: '@democrats', color: '#a8478c', ...facetData('democrats', isMobile) },
		{ key: 'whitehouse', label: '@whitehouse', color: '#e8863a', ...facetData('whitehouse', isMobile) },
		{ key: 'republicans', label: '@republicans', color: '#ee6677', ...facetData('republicans', isMobile) }
	]);
	// account comparison, narrowed to POST-LOSS so all three share one axis and can be overlaid
	const cmpLo = payoff.electionIdx;
	const cmpMonths = payoff.months.slice(cmpLo);
	const cmpSeries = [
		{ key: 'democrats', label: '@democrats', color: '#a8478c', vals: payoff.series.democrats.vals.slice(cmpLo) },
		{ key: 'whitehouse', label: '@whitehouse', color: '#e8863a', vals: payoff.series.whitehouse.vals.slice(cmpLo) },
		{ key: 'republicans', label: '@republicans', color: '#ee6677', vals: payoff.series.republicans.vals.slice(cmpLo) }
	];
	// tween progress 0→1 over `dur`, after `delay`, easing out; skips animation for reduced motion
	function playReveal(setter, { delay = 700, dur = 4800 } = {}) {
		if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
			setter(1);
			return;
		}
		let t0 = null;
		function frame(t) {
			if (t0 == null) t0 = t;
			const el = t - t0;
			if (el < delay) return requestAnimationFrame(frame);
			const p = Math.min(1, (el - delay) / dur);
			setter(1 - Math.pow(1 - p, 3)); // ease-out cubic
			if (p < 1) requestAnimationFrame(frame);
		}
		requestAnimationFrame(frame);
	}
	// action: play the reveal once when the node scrolls into view (works even for
	// nodes that mount later, e.g. after the reader opens the gate)
	function revealOnView(node, cb) {
		const obs = new IntersectionObserver(
			(entries) => {
				for (const e of entries) {
					if (e.isIntersecting) {
						cb();
						obs.disconnect();
						return;
					}
				}
			},
			{ threshold: 0.35 }
		);
		obs.observe(node);
		return { destroy: () => obs.disconnect() };
	}

	// video wall: offset each tile's start by its index so the loop rolls across the wall
	// like a strip of film frames. Phase offsets persist because every tile shares one loop.
	const WALL_N = 48;
	function reel(node, i) {
		const apply = () => {
			const d = node.duration || 11.7;
			if (d) node.currentTime = ((i * d) / WALL_N) % d;
		};
		if (node.readyState >= 1) apply();
		else node.addEventListener('loadedmetadata', apply, { once: true });
		node.play?.().catch(() => {});
		return { destroy: () => node.removeEventListener('loadedmetadata', apply) };
	}

	// Act 6.5 — the cast pack (who the @democrats put on camera)
	let castIndex = $state(0);
	const castSteps = [
		{
			side: 'all',
			colorBy: 'party',
			h: 'Meet the ensemble',
			p: 'Every political figure the <b>@democrats</b> put on screen, sized by how many videos they lead. Their own side in <b style="color:#5b8dd6">blue</b>, the opposition in <b style="color:#ee6677">red</b>.'
		},
		{
			side: 'all',
			colorBy: 'party',
			h: '',
			p: 'For all its new venom, the <b>@democrats</b> account has built a feed with no protagonist of its own. The meaner it got, the more that enemy became the main character of its own show.'
		},
		{
			side: 'all',
			colorBy: 'party',
			spotlight: 'donald-trump',
			h: '',
			p: '<b>Donald Trump</b> leads <b>1,192</b> of the account’s videos, accounting for more than a third of all starring roles.'
		},
		{
			side: 'all',
			colorBy: 'party',
			litParty: 'opp',
			h: '',
			p: 'Overall, <b>57%</b> of lead roles go to <b style="color:#ee6677">political opponents</b>.'
		},
		{
			side: 'own',
			colorBy: 'party',
			emphasis: ['kamala-harris', 'joe-biden', 'barack-obama'],
			h: '',
			p: 'Strip the opposition away and the Democrats’ own cast is harder to read. Its biggest faces are <b>Kamala Harris</b>, <b>Joe Biden</b> and <b>Barack Obama</b>: a defeated nominee and two former presidents.'
		},
		{
			side: 'own',
			colorBy: 'party',
			h: '',
			p: 'No active Democrat commands a share of appearances close to Trump’s. Beyond the legacy names, attention scatters across a rotating ensemble — <b>Zohran Mamdani</b>, <b>Gavin Newsom</b>, <b>Alexandria Ocasio-Cortez</b> — with no successor at the centre.'
		},
		{
			side: 'own',
			colorBy: 'party',
			win: 'recent3',
			h: '',
			p: 'Narrow the window to the most recent three months, as of July 9, 2026, and the Democrats’ own bench barely registers. Its most-posted figure is former president <b>Barack Obama</b>, at <b>14</b>, with New York City mayor <b>Zohran Mamdani</b> trailing close behind at <b>13</b>.'
		},
		{
			side: 'all',
			colorBy: 'party',
			win: 'recent3',
			h: '',
			p: 'Put GOP figures back on the board for the same three months, and one face swallows it whole again: <b>Donald Trump</b>, with <b>160</b> appearances, more than ten times any Democrat’s.'
		},
		{
			account: 'Republican',
			side: 'all',
			colorBy: 'party',
			win: 'recent3',
			h: '',
			p: 'The Republicans’ side tell a much simpler story. Their universe revolves around a tightly defined cast.'
		},
		{
			account: 'Republican',
			side: 'all',
			colorBy: 'party',
			h: '',
			p: 'Across the Republicans’ official TikTok universe, the cast changes remarkably little. Trump remains the central protagonist, with the same small circle of allies and opponents returning again and again.'
		}
	];
	const castStep = $derived(castSteps[Math.min(castIndex, castSteps.length - 1)]);
</script>

<svelte:window bind:innerWidth={vw} />
<div class="dbm">
	<!-- ARCHIVED front sequence (opening doomscrolling montage) — set to `true` to restore -->
	{#if false}
		<section class="intro-story">
			<Scroller top={0} bottom={1} bind:index={introIndex} bind:progress={introProgress} bind:count={introCount}>
				{#snippet background()}
					<Montage imgs={trollImgs} progress={introProgress} lines={introSteps} />
				{/snippet}
				{#snippet foreground()}
					<!-- pure scroll spacers; the narration itself is pinned centre inside <Montage> -->
					{#each introSteps as _, i (i)}
						<div class="narr-step"></div>
					{/each}
				{/snippet}
			</Scroller>
		</section>
	{/if}

	<!-- opening: scrolly cards over a full-screen wall of the same @democrats video, tiled + looping -->
	<section class="opening">
		<Scroller top={0} bottom={1} bind:index={openIndex} bind:progress={openProgress}>
			{#snippet background()}
				<div class="video-wall" aria-hidden="true">
					{#each Array(WALL_N) as _, i (i)}
						<video src="{base}/wall_web.mp4" autoplay loop muted playsinline preload="auto" use:reel={i}
						></video>
					{/each}
				</div>
			{/snippet}
			{#snippet foreground()}
				{#each openCards as card, i (i)}
					<div class="open-step">
						<!-- eslint-disable-next-line svelte/no-at-html-tags -->
						<p class="open-card" class:active={openIndex === i}>{@html card}</p>
					</div>
				{/each}
			{/snippet}
		</Scroller>
	</section>

	<!-- Act 3 — the turn: how "go high" became "dark woke" (reporting bridge into the data) -->
	<section class="turn">
		<div class="turn-inner">
			{#snippet glitchWord(word)}
				<span class="glitch"
					>{word}{#each glitchStrips as s (s.clip)}<span
							class="glitch__l"
							aria-hidden="true"
							style="clip-path:{s.clip};animation-name:glitch-{s.v};animation-duration:{s.dur};animation-delay:{s.delay};"
							>{word}</span
						>{/each}</span
					>
			{/snippet}
			<h1 class="lede-h1">
				Brat Summer,<br />
				{@render glitchWord('Mean')} {@render glitchWord('Winter')}
			</h1>
			<p class="lede-sub">
				Democrats broke out of their respectability prison in embrace of ‘dark woke’. Things escalated quickly.
			</p>
			<p class="lede-byline">A TikTok deep-dive by <span>Wong Pei Ting</span></p>
			<p class="turn-line">
				For years, Democrats lived by Michelle Obama’s refrain: “When they go low, we go high.”
			</p>
			<p class="turn-line">
				Then they lost the 2024 election, and the party changed its mind. The Democratic National
				Committee set up a rapid-response “war room,” and the man who runs it, Tim Hogan, said the goal
				was to put in charge people who “know how to dunk without reading a 40-page deck.”
				Staff were encouraged to stop overthinking and treat the Trump administration as “objects of
				ridicule.” Congressman Robert Garcia put it even more bluntly: “We deserve to be mean to them.”
			</p>
			<p class="turn-line">But what does being mean actually look like?</p>
			<p class="turn-line">
				To find out, I analyzed nearly 2,800 TikTok posts published by the official @democrats account
				since its inception in 2022.
			</p>
		</div>
	</section>

	<!-- gut-check, right before the wall: type an insult; did the @democrats already use it? -->
	<section class="ask">
		<div class="ask-inner">
			<img class="laser-eyes" src="{base}/laser-eyes.png" alt="" aria-hidden="true" />
			<p class="ask-q">Before we begin,<br />let’s channel our<br />inner middle-schooler.</p>
			<form class="ask-form" onsubmit={askSubmit}>
				<input
					bind:value={typed}
					placeholder="type an insult, then hit enter"
					autocomplete="off"
					autocapitalize="off"
					spellcheck="false"
				/>
			</form>
			{#if answered}
				<button class="ask-skip" onclick={generateInsult}>↻ Pick another</button>
			{:else}
				<button class="ask-skip" onclick={generateInsult}>Or try the insult randomizer.</button>
			{/if}
			{#if answered}
				<div class="ask-a">
					{#if niceWord}
						<p>Ha — right, <em>“{typed.trim()}”</em> isn’t an insult.</p>
					{:else if result}
						{#if generated}
							<p>Here’s one straight from their playbook: <em>“{result.word}”</em>.</p>
						{:else}
							{#if result.corrected}<p class="mut">(reading that as <em>“{result.word}”</em>)</p>{/if}
							<p>
								Yes. The <b>@democrats</b> have used <em>“{result.word}”</em> in <b>{result.n}</b>
								{result.n === 1 ? 'dunk' : 'dunks'}{#if result.t}, on people like <b>{result.t}</b>{/if}.
							</p>
						{/if}
						{#each exGroups as g}
							{#if g.t}<div class="ex-t">Used on {g.t}</div>{/if}
							<ul class="ex-list">
								{#each g.items as e (e.l)}
									{@const vid = vidOf(e.u)}
									{@const pm = vid ? postmeta[vid] : null}
									<li>
										<a class="ex-post" href={e.u} target="_blank" rel="noopener noreferrer">
											<span class="ex-line">“{e.l}”</span>
											<span class="ex-tip">
												{#if vid}<img
														src="{base}/kf/{vid}.jpg"
														alt=""
														loading="lazy"
														onerror={(e) => (e.currentTarget.style.display = 'none')}
													/>{/if}
												<span class="ex-tip-meta">
													{#if pm?.v}<span class="tip-views">{fmtViews(pm.v)} views</span>{/if}
													{#if pm?.emo?.length}<span class="tip-emo">{pm.emo.join(' · ')}</span>{/if}
													{#if pm?.intent}<span class="tip-intent">{pm.intent}</span>{/if}
													<span class="watch">▶&nbsp;watch the post&nbsp;↗</span>
												</span>
											</span>
										</a>
									</li>
								{/each}
							</ul>
						{/each}
						{#if result.n > result.ex.length}
							<p class="mut">…and {result.n - result.ex.length} more.</p>
						{/if}
						{#if compare}
							<div class="cmp">
								<div class="cmp-cap">How often each side reaches for it</div>
								<div class="cmp-row">
									<span class="cmp-lab">@democrats</span>
									<div class="cmp-track"><div class="cmp-fill dem" style:width="{compare.demPct}%"></div><span class="cmp-num">{compare.d}</span></div>
								</div>
								<div class="cmp-row">
									<span class="cmp-lab">@whitehouse @republicans</span>
									<div class="cmp-track"><div class="cmp-fill rep" style:width="{compare.repPct}%"></div><span class="cmp-num">{compare.r}</span></div>
								</div>
							</div>
						{/if}
					{:else}
						<p>
							<em>“{typed.trim()}”</em>? The <b>@democrats</b> haven’t gone there — not yet. But the
							words they <em>did</em> reach for are meaner than you’d guess.
						</p>
					{/if}
					<p class="ask-cont">
						{#if result && !niceWord}
							This insult wasn’t an isolated dunk. Zoom out, and you can see when this brand
							of personal attacks began to take shape.
						{:else}
							Your word wasn’t one of theirs. But zoom out, and you can see when this brand
							of personal attacks began to take shape.
						{/if}
					</p>
					<p class="ask-cont">
						To trace that shift, I compared the language the party used before and after the 2024
						election, focusing on posts that attacked an opponent. I looked for the insults, labels and
						rhetorical habits that became markedly more common after Democrats embraced a more
						combative online strategy.
					</p>
					<p class="ask-cont">The results reveal the shift.</p>
				</div>
			{/if}
		</div>
	</section>

	{#if gateOpen}
	<section class="story">
		<Scroller top={0} bottom={1} bind:index bind:progress bind:count>
			{#snippet background()}
				<HeatField {data} progress={playhead} {highlight} {annotating} {exploring} />
			{/snippet}

			{#snippet foreground()}
				<!-- reveal, part 1: a few early words appear -->
				<div class="reveal-space" style:height="{REVEAL1_VH}vh"></div>
				<!-- teaching pause: the clock holds while this explains how to read height -->
				<div class="step teach" class:on={teaching} style:height="{TEACH_VH}vh">
					<div class="card">
						<h3>What am I looking at?</h3>
						<p>
							Every word is a dunk word most distinct of the point in the timeline where it stands.
							The <b>bigger</b> they are, the more <u>frequently</u> they were used. The
							<span class="hl-red">redder</span> a word is, the more
							<span class="red-word">inflammatory</span> the context in which it was used.
						</p>
					</div>
				</div>
				<!-- reveal 2a: fill in up to the election -->
				<div class="reveal-space" style:height="{REVEAL2A_VH}vh"></div>
				<!-- loss pause: clock holds at the "Trump wins election" line -->
				<div class="step loss" class:on={lossPausing} style:height="{LOSSPAUSE_VH}vh">
					<div class="card">
						<p>
							{isMobile
								? "Notice how things escalate from Nov 2024 with Trump's electoral win."
								: 'Notice how things escalate from here.'}
						</p>
					</div>
				</div>
				<!-- reveal 2b: the post-loss escalation fills in -->
				<div class="reveal-space" style:height="{REVEAL2B_VH}vh"></div>
				<!-- settle: hold the finished, full-brightness wall before any spotlight -->
				<div class="reveal-space" style:height="{SETTLE_VH}vh"></div>
				<!-- annotate: one card per group of words to spotlight -->
				{#each cards as card, i (i)}
					<div class="step {card.tone}" class:on={index === i + 6} style:height="{card.vh}vh">
						<div class="card" class:has-videos={card.videos} class:has-chart={card.chart}>
							{#if card.h}<h3>{card.h}</h3>{/if}
							{#if card.chart}
							<div class="card-chart"><MeanSpark w={500} h={188} light /></div>
							<p class="chart-note">
								<b>How we measured meanness:</b> an LLM scored every @democrats post from −3
								(friendly) to +3 (hostile); the line is that score averaged by month, smoothed over
								three months.
							</p>
						{/if}
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							<p>{@html card.p}</p>
							{#if card.videos}
								<div class="tk-grid">
									{#each card.videos as v (v.id)}
										<div class="tk">
											<div class="tk-vid">
												<video src="{base}/rg/{v.id}.mp4" muted loop playsinline autoplay preload="metadata"
												></video>
												<span class="tk-views">▶ {fmtViews(v.views)}</span>
											</div>
											<div class="tk-meta">
												<span class="tk-handle">@democrats</span>
												<span class="tk-cap">{v.cap}</span>
												<span class="tk-date">{fmtDate(v.date)}</span>
											</div>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					</div>
				{/each}
				<!-- final beat: no card, full field lit, every word hoverable (see HeatField
					     `exploring`); the hint box lives in HeatField -->
					<div class="step" style:height="230vh"></div>
			{/snippet}
		</Scroller>
	</section>

	<!-- the payoff: prose with the Mean-o-meter embedded inline, revealing as it scrolls in -->
	<section class="mean-reveal">
		<div class="mr-text">
			<p>
				I also looked beyond the changing vocabulary in dunk lines and measured the emotional register
				of every @democrats post, on a 7-point scale from hero-worship (−3) to hostile/taunting (+3).
				For nearly three years, the account hovered close to neutral. After the 2024 election, it shifted sharply toward hostility and stayed there.
			</p>
		</div>
		<div class="mr-block">
			<h3 class="mr-h">The Mean-o-meter</h3>
			<p class="mr-dek">
				Every @democrats post scored from hero-worship to hostile, averaged by month on a
				three-month trailing basis.
			</p>
			<div class="mr-chart" use:revealOnView={() => playReveal((v) => (meanProg = v))}>
				<MeanSpark
					w={isMobile ? 360 : 620}
					h={isMobile ? 430 : 344}
					progress={meanProg}
					title=""
					endAvatar="{base}/avatars/democrats.jpg"
					labelPx={isMobile ? 11 : 12}
				/>
			</div>
		</div>

		<div class="mr-text">
			<p>
				As of July 9, the number of posts at the top of the scale (+3, or hostile/taunting) went from
				168 before the loss to 549 after.
			</p>
		</div>

		<div class="mr-text">
			<p>
				Is this simply how political TikTok sounds now? To check, I ran the same measure on the other
				side’s official accounts, and they don’t look the same.
			</p>
		</div>
		<div class="mr-block">
			<h3 class="mr-h">It’s uniquely @democrats</h3>
			<p class="mr-dek">
				{isMobile
					? 'Each account since the 2024 loss, on the same hero-worship to hostile scale.'
					: 'Each account’s register over its own lifetime, on the same hero-worship to hostile scale.'}
			</p>
			<div class="facets" use:revealOnView={() => playReveal((v) => (cmpProg = v), { delay: 700, dur: 5000 })}>
				{#each facets as f, i (f.key)}
					<div class="facet">
						<div class="facet-head">
							<span class="facet-dot" style:background={f.color}></span>
							<span class="facet-name">{f.label}</span>
						</div>
						<div class="mr-chart">
							<MeanSpark
								w={isMobile ? 360 : i === 0 ? 232 : 178}
								h={isMobile ? 150 : 250}
								progress={cmpProg}
								vals={f.vals}
								monthsList={f.monthsList}
								electionIdx={null}
								lineColor={f.color}
								showY={isMobile || i === 0}
								xEndpoints={true}
								allGrid={true}
								endAvatar="{base}/avatars/{f.key}.jpg"
								title=""
							/>
						</div>
					</div>
				{/each}
			</div>
		</div>
		<div class="mr-text">
			<p>
				The @whitehouse posts more to glorify its own side than to attack anyone, and @republicans,
				posting only since early 2026, sit close to neutral. Only @democrats climbed into hostile
				territory.
			</p>
		</div>
		<div class="mr-text">
			<p>
				If the @democrats account turned this mean, the question
				that follows is who it turned mean toward, whose face keeps filling these videos. So I
				counted every political figure the account built a post around.
			</p>
		</div>
	</section>

	<!-- Act 6.5 — who they aim at: the cast pack -->
	<section class="cast-story">
		<Scroller top={0} bottom={1} bind:index={castIndex}>
			{#snippet background()}
				<CastPack
					account={castStep.account ?? 'Democrat'}
					side={castStep.side}
					colorBy={castStep.colorBy}
					spotlight={castStep.spotlight ?? null}
					emphasis={castStep.emphasis ?? null}
					litParty={castStep.litParty ?? null}
					win={castStep.win ?? null}
				/>
			{/snippet}
			{#snippet foreground()}
				{#each castSteps as step, i (i)}
					<div class="cast-step" class:on={castIndex === i}>
						<div class="card">
							{#if step.h}<h3>{step.h}</h3>{/if}
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							<p>{@html step.p}</p>
						</div>
					</div>
				{/each}
				<!-- trailing hold: the last card scrolls off and the full circle pack is revealed
				     (pack still pinned) before the whole section scrolls away -->
				<div class="cast-step cast-tail" aria-hidden="true"></div>
			{/snippet}
		</Scroller>
	</section>

	<!-- the payoff: cruelty tracks reach almost perfectly; then, at what cost -->
	<section class="payoff wrap">
		<p class="payoff-lede">
			So did the “dark woke” turn pay off? By one measure, yes. The account’s median post drew
			55,000 views before the Democrats’ 2024 loss. Afterwards, that figure rose to more than
			530,000, a tenfold increase.
		</p>
		<p class="payoff-lede">
			Within the post-election feed, the cruder the post, the larger
			its audience. Rank posts from institutional to crass, and the median number of views climbs at
			every rung.
		</p>

		<h3 class="cs-h">Meanness, rewarded</h3>
		<div class="cs-dek-wrap">
			<p class="cs-dek">
				Each dot is a @democrats post since the 2024 loss, by view count and crudeness
			</p>
			{#if isMobile}
				<p class="cs-legend"><span class="cs-legend-line"></span>median</p>
			{/if}
		</div>
		<div class="cs-swarm" use:revealOnView={() => (payoffShown = true)}>
			<PayoffSwarm shown={payoffShown} portrait={isMobile} />
		</div>

		<p class="payoff-kicker">
			The more abrasive the post, the larger the audience. Perhaps we’re only witnessing the
			beginning of a feedback loop that rewards escalation, where each successful provocation
			strengthens the case for the next.
		</p>
		<p class="payoff-kicker">
			That leaves a harder question, not just for Democrats but for politics in the attention
			economy: can a politics optimized for attention still persuade?
		</p>
	</section>

	<!-- REMOVED for now (recoverable from git): the flow/Sankey ("Where every post ends
	     up"), Act 7 reckoning, and Act 8 close. Methodology kept below. -->

	<section class="after wrap">
		<div class="method-wrap">
			<hr class="method-rule" />
			<h3 class="method-h">Data and Methods</h3>
			<p class="method">
				The analysis covers every TikTok post by @democrats through July 9, 2026 (2,786 posts),
				with @whitehouse (856) and @republicans (189) as comparisons; audio was transcribed with
				Whisper and on-screen text extracted using OCR. Cast portraits from YouGov Ratings.
			</p>
			<p class="method">
				Gemini 2.5 Pro labelled every video for its function, featured political figures, register
				(−3 to +3, with +2 or above classified as an attack), crudeness (0–3), and whether it
				delivered a “dunk.” Ambiguous posts were not coded as attacks.
			</p>
			<p class="method">
				To plot the @democrats’ most distinctive attack words, I pulled 2,613 “dunk” lines across
				916 attacking videos and split them on Nov. 5, 2024, the day their presidential candidate,
				Kamala Harris, lost the race. The post-loss vocabulary was then ranked against the pre-loss
				lexicon with weighted log-odds (Monroe, Colaresi &amp; Quinn, 2008, “Fightin’ Words”).
			</p>
		</div>
	</section>

	<!-- laser eyes one last time, all the way at the bottom (cropped to end just past the streak) -->
	<div class="endflare" aria-hidden="true">
		<img src="{base}/laser-eyes-end.png" alt="" />
	</div>
	{/if}
</div>

<style>
	@font-face {
		font-family: 'Atlas Grotesk';
		src: url('https://pudding.cool/assets/fonts/atlas/AtlasGrotesk-Regular-Web.woff2') format('woff2');
		font-weight: 400;
		font-display: swap;
	}
	@font-face {
		font-family: 'Atlas Grotesk';
		src: url('https://pudding.cool/assets/fonts/atlas/AtlasGrotesk-Bold-Web.woff2') format('woff2');
		font-weight: 700;
		font-display: swap;
	}
	@font-face {
		font-family: 'Tiempos Text';
		src: url('https://pudding.cool/assets/fonts/tiempos/TiemposTextWeb-Regular.woff2') format('woff2');
		font-weight: 400;
		font-display: swap;
	}
	@font-face {
		font-family: 'Tiempos Text';
		src: url('https://pudding.cool/assets/fonts/tiempos/TiemposTextWeb-Bold.woff2') format('woff2');
		font-weight: 700;
		font-display: swap;
	}

	:global(body) {
		background: #1a1d21;
	}

	.dbm {
		--bg: #1a1d21;
		--ink: #e6e6e7;
		--muted: #8a8f96;
		--pre: #66ccee;
		--post: #ee6677;
		--gold: #ccbb44;
		--line: #33383f;
		--sans: 'Atlas Grotesk', -apple-system, Helvetica, Arial, sans-serif;
		--serif: 'Tiempos Text', Georgia, 'Times New Roman', serif;
		background: var(--bg);
		color: var(--ink);
		font-family: var(--sans);
		line-height: 1.5;
		-webkit-font-smoothing: antialiased;
	}

	.wrap {
		max-width: 820px;
		margin: 0 auto;
		padding: 0 24px;
	}
	header {
		padding: 16vh 0 8vh;
	}
	.eyebrow {
		font-size: 0.75rem;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: var(--muted);
		margin: 0 0 1.6em;
	}
	h1 {
		font-family: var(--serif);
		font-weight: 700;
		font-size: clamp(2.6rem, 7.5vw, 5rem);
		line-height: 1;
		letter-spacing: -0.02em;
		margin: 0 0 0.5em;
	}
	.dek {
		font-family: var(--serif);
		font-size: 1.35rem;
		color: #cfd2d6;
		max-width: 37em;
		line-height: 1.5;
	}
	.dek b {
		color: var(--post);
		font-weight: 400;
	}
	.dek b.b {
		color: var(--pre);
		font-weight: 400;
	}
	.scroll-hint {
		margin-top: 3.4em;
		font-size: 0.75rem;
		letter-spacing: 0.2em;
		text-transform: uppercase;
		color: var(--muted);
	}

	/* standalone mirrored laser-eyes flare filling a gap between sections */
	.laser-band {
		position: relative;
		height: 34vh;
		pointer-events: none;
		z-index: 50; /* laser eyes always paint on top — no hard section seams */
	}
	/* page-ending flare: a PRE-CROPPED image (top glow → just past the streak). The top fades in
	   naturally, the page ends right at the streak, and it's un-flipped like the insult-frame flare. */
	.endflare {
		position: relative;
		z-index: 50;
		line-height: 0;
		margin-top: -20vw; /* the transparent top glow overlaps the text above (screen-blend, no box) */
	}
	.endflare img {
		display: block;
		width: 100vw;
		margin-left: 50%;
		transform: translateX(-50%); /* full-bleed, un-flipped */
		mix-blend-mode: screen;
		-webkit-mask-image: linear-gradient(to right, transparent, #000 18%, #000 82%, transparent);
		mask-image: linear-gradient(to right, transparent, #000 18%, #000 82%, transparent);
	}
	.laser-band img {
		position: absolute;
		top: 50%;
		left: 50%;
		width: 100vw;
		transform: translate(-50%, -50%) scaleX(-1); /* mirrored */
		mix-blend-mode: screen;
		-webkit-mask-image: radial-gradient(ellipse 60% 52% at 50% 50%, #000 38%, transparent 100%);
		mask-image: radial-gradient(ellipse 60% 52% at 50% 50%, #000 38%, transparent 100%);
	}
	.video-wall {
		position: relative;
		height: 100vh;
		overflow: hidden;
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
		grid-auto-rows: 33.34vh;
		background: #000;
	}
	.video-wall video {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}
	.open-step {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 24px;
		pointer-events: none;
	}
	.open-card {
		max-width: 23em;
		margin: 0;
		text-align: center;
		font-family: var(--serif);
		font-weight: 500;
		font-size: clamp(0.95rem, 1.7vw, 1.25rem); /* small + quiet against the chaotic wall */
		line-height: 1.5;
		color: #16181c; /* dark ink on the white card */
		background: #ffffff;
		padding: 0.9rem 1.7rem;
		box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45);
		opacity: 0.22;
		transition: opacity 0.4s ease;
	}
	.open-card.active {
		opacity: 1;
	}
	.open-card :global(em) {
		font-style: italic;
		color: inherit;
	}
	.intro-story {
		max-width: none;
	}
	.narr-step {
		height: 118vh;
		pointer-events: none;
	}

	.ask {
		min-height: 86vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 30vh 24px 4vh; /* room above for the laser-eyes flare; content sits lower */
	}
	.ask-inner {
		max-width: 40rem;
		width: 100%;
		text-align: center;
		position: relative;
		padding-top: 7vh; /* space below the flare; shifts the words down */
	}
	.ask-q {
		font-family: var(--serif);
		font-weight: 700;
		font-size: clamp(1.75rem, 3.8vw, 2.5rem);
		line-height: 1.3;
		color: #a8478c; /* deeper gauge magenta */
		margin: 0 0 1.4em;
	}
	.ask-form {
		margin: 0 auto;
		max-width: 26rem;
	}
	.ask-form input {
		width: 100%;
		background: transparent;
		border: none;
		border-bottom: 2px solid var(--line);
		color: var(--ink);
		font-family: var(--serif);
		font-size: clamp(1.6rem, 4vw, 2.2rem);
		text-align: center;
		padding: 0.3em 0.2em;
		outline: none;
	}
	.ask-form input::placeholder {
		color: var(--muted);
		font-size: 0.7em;
	}
	.ask-form input:focus {
		border-bottom-color: var(--post);
	}
	.ask-a {
		margin-top: 2.6em;
		animation: askfade 0.5s ease;
	}
	@keyframes askfade {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
	}
	.ask-a p {
		font-family: var(--serif);
		font-size: clamp(1.2rem, 3vw, 1.7rem);
		line-height: 1.4;
		color: #cfd2d6;
		margin: 0 0 0.5em;
	}
	.ask-a b {
		color: var(--ink);
		font-weight: 700;
	}
	.ask-a em {
		font-style: normal;
		color: var(--post);
	}
	.ask-a .mut {
		font-size: 0.9rem;
		color: var(--muted);
	}
	.ask-a .ex {
		font-size: 1rem;
		font-style: italic;
		color: var(--muted);
		max-width: 32em;
		margin: 0.8em auto 0;
	}
	/* list of every dunk line that uses the typed word */
	.ex-list {
		list-style: none;
		max-width: 34rem;
		margin: 0 auto;
		padding: 0;
		text-align: left;
	}
	.ex-list li {
		position: relative;
		padding: 0.4em 0;
		border-top: 1px solid var(--line);
	}
	.ex-post {
		display: block;
		position: relative;
		font-family: var(--serif);
		font-size: 1rem;
		font-style: italic;
		line-height: 1.45;
		color: #cfd2d6;
		text-decoration: none;
		cursor: pointer;
	}
	.ex-post:hover .ex-line {
		color: #fff;
	}
	.ex-t {
		display: block;
		max-width: 34rem;
		margin: 1.2em auto 0.3em;
		text-align: left;
		font-family: var(--sans);
		font-style: normal;
		font-size: 0.68rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--post);
	}
	/* hover tooltip: key frame + watch-the-post link */
	.ex-tip {
		position: absolute;
		left: 0;
		bottom: calc(100% + 8px);
		display: flex;
		gap: 10px;
		align-items: center;
		width: max-content;
		max-width: 380px;
		background: #0f1114;
		border: 1px solid #2a2f36;
		border-radius: 8px;
		padding: 8px;
		box-shadow: 0 12px 34px rgba(0, 0, 0, 0.6);
		opacity: 0;
		transform: translateY(6px);
		pointer-events: none;
		transition:
			opacity 150ms ease,
			transform 150ms ease;
		z-index: 20;
	}
	/* invisible bridge across the gap so the pointer can travel up into the tooltip
	   without dropping the hover (otherwise the watch link is unreachable) */
	.ex-tip::after {
		content: '';
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		height: 12px;
	}
	.ex-post:hover .ex-tip,
	.ex-tip:hover {
		opacity: 1;
		transform: translateY(0);
		pointer-events: auto;
	}
	.ex-tip img {
		width: 66px;
		aspect-ratio: 9 / 16;
		object-fit: cover;
		border-radius: 5px;
		display: block;
		flex: 0 0 auto;
	}
	.ex-tip-meta {
		display: flex;
		flex-direction: column;
		gap: 3px;
		font-family: var(--sans);
		font-style: normal;
		font-size: 0.8rem;
		line-height: 1.4;
		color: #cfd2d6;
		max-width: 19em;
	}
	.ex-tip-meta b {
		color: #fff;
	}
	.tip-views {
		font-weight: 700;
		color: #fff;
	}
	.tip-emo {
		font-size: 0.72rem;
		text-transform: capitalize;
		color: var(--post);
	}
	.tip-intent {
		font-size: 0.72rem;
		color: var(--muted);
		font-style: italic;
	}
	.ex-tip-meta .watch {
		margin-top: 2px;
		color: #d4a3c6;
		font-weight: 700;
		white-space: nowrap;
	}
	/* dem-vs-rep frequency comparison */
	.cmp {
		max-width: 34em;
		margin: 1.8em auto 0;
		text-align: left;
	}
	.cmp-cap {
		font-family: var(--sans);
		font-size: 0.72rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--muted);
		margin-bottom: 0.7em;
	}
	.cmp-row {
		display: grid;
		grid-template-columns: 8.5em 1fr;
		align-items: center;
		gap: 0.6em;
		margin-bottom: 0.5em;
	}
	.cmp-lab {
		font-family: var(--sans);
		font-size: 0.78rem;
		line-height: 1.25;
		color: #cfd2d6;
		text-align: right;
	}
	.cmp-track {
		display: flex;
		align-items: center;
	}
	.cmp-fill {
		height: 12px;
		max-width: calc(100% - 2.6em); /* leave room for the count at the bar's end */
		flex-shrink: 0;
		background: #a8478c;
		transition: width 0.4s ease;
	}
	.cmp-num {
		margin-left: 0.5em;
		font-family: var(--sans);
		font-size: 0.82rem;
		font-weight: 700;
		color: var(--ink);
		white-space: nowrap;
	}
	.cmp-note {
		font-family: var(--sans);
		font-size: 0.8rem;
		color: var(--muted);
		margin: 0.9em 0 0;
	}
	.ask-regen {
		display: inline-block;
		margin-top: 1.6em;
		font-family: var(--sans);
		font-size: 0.82rem;
		color: #d4a3c6;
		background: none;
		border: 1px solid #3a3f47;
		border-radius: 999px;
		padding: 0.35em 0.9em;
		cursor: pointer;
		transition:
			border-color 160ms ease,
			color 160ms ease;
	}
	.ask-regen:hover {
		border-color: #d4a3c6;
	}
	.ask-cont {
		margin-top: 2.8em !important;
		font-family: var(--serif) !important;
		font-size: 1.32rem !important;
		font-weight: 400;
		font-style: normal;
		line-height: 1.62;
		letter-spacing: 0;
		text-transform: none;
		text-align: left;
		color: #d7dade !important;
	}
	.ask-cont + .ask-cont {
		margin-top: 0.9em !important;
	}
	/* the story is only mounted once the reader answers or skips (see {#if gateOpen}),
	   so its scroll-driven graphics measure their size while visible, not while hidden */
	.ask-skip {
		display: inline-block;
		margin-top: 1.1em;
		background: none;
		border: 0;
		padding: 0;
		font-family: var(--sans);
		font-size: 0.92rem;
		color: #d4a3c6; /* lighter magenta */
		text-decoration: underline;
		cursor: pointer;
		transition: opacity 160ms ease;
	}
	.ask-skip:hover {
		opacity: 0.7;
	}

	/* article headline above the opening bridge */
	.lede-kicker {
		font-family: var(--sans);
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: var(--muted);
		margin: 0 0 1.3em;
	}
	.lede-h1 {
		font-family: var(--sans);
		font-weight: 700;
		font-size: clamp(3rem, 8.5vw, 5.2rem);
		line-height: 0.97;
		letter-spacing: -0.025em;
		color: #a8478c; /* the gauge magenta */
		-webkit-text-stroke: 3.5px #ffffff; /* white outline around the magenta */
		paint-order: stroke fill;
		margin: 0 0 0.4em;
		position: relative;
	}
	.glitch {
		position: relative;
		display: inline-block;
	}
	.glitch__l {
		position: absolute;
		top: 0;
		left: 0;
		color: #a8478c;
		-webkit-text-stroke: 3.5px #ffffff;
		paint-order: stroke fill;
		pointer-events: none;
		animation-timing-function: steps(1, end);
		animation-iteration-count: infinite;
		will-change: transform, filter;
	}
	/* muffinman-style strip glitch: each band displaces + gets a chromatic drop-shadow on its
	   own slow, off-phase cycle — quiet and occasional, not a constant jitter */
	@keyframes -global-glitch-a {
		0%, 14%, 17%, 48%, 51%, 79%, 82%, 100% { transform: none; filter: none; }
		15% { transform: translateX(-8px); filter: drop-shadow(3px 0 0 rgba(0,225,255,0.85)) drop-shadow(-3px 0 0 rgba(255,45,75,0.85)); }
		16% { transform: translateX(5px); filter: drop-shadow(-2px 0 0 rgba(0,225,255,0.7)); }
		49% { transform: translateX(7px); filter: hue-rotate(40deg) drop-shadow(-3px 0 0 rgba(255,45,75,0.8)); }
		50% { transform: translateX(-4px); filter: drop-shadow(2px 0 0 rgba(0,225,255,0.7)); }
		80% { transform: translateX(-9px); filter: drop-shadow(3px 0 0 rgba(0,225,255,0.85)) drop-shadow(-3px 0 0 rgba(255,45,75,0.85)); }
		81% { transform: translateX(4px); filter: none; }
	}
	@keyframes -global-glitch-b {
		0%, 29%, 33%, 63%, 67%, 100% { transform: none; filter: none; }
		30% { transform: translateX(9px); filter: hue-rotate(-30deg) drop-shadow(-3px 0 0 rgba(0,225,255,0.75)); }
		32% { transform: translateX(-5px); filter: drop-shadow(3px 0 0 rgba(255,45,75,0.8)); }
		64% { transform: translateX(-7px); filter: drop-shadow(3px 0 0 rgba(0,225,255,0.75)) drop-shadow(-3px 0 0 rgba(255,45,75,0.75)); }
		66% { transform: translateX(6px); filter: none; }
	}
	/* laser-eyes PNG flare (in the "Before we begin" frame), sides feathered to no hard edges */
	.laser-eyes {
		position: absolute;
		bottom: 100%; /* sits above "Before we begin" in the insult frame */
		left: 50%;
		width: 100vw; /* mega, full-screen width, centred on the viewport */
		transform: translate(-50%, 40%);
		pointer-events: none;
		mix-blend-mode: screen;
		z-index: 50;
		-webkit-mask-image: radial-gradient(ellipse 60% 52% at 50% 50%, #000 38%, transparent 100%);
		mask-image: radial-gradient(ellipse 60% 52% at 50% 50%, #000 38%, transparent 100%);
	}
	@keyframes laser-flicker {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.86;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.laser-eyes {
			animation: none;
		}
	}
	@keyframes jitter {
		0% {
			transform: translate(0, 0) rotate(0deg);
		}
		25% {
			transform: translate(-0.02em, 0.03em) rotate(-3.5deg);
		}
		50% {
			transform: translate(0.03em, -0.02em) rotate(2.5deg);
		}
		75% {
			transform: translate(-0.015em, -0.03em) rotate(-1.5deg);
		}
		100% {
			transform: translate(0.025em, 0.02em) rotate(3deg);
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.jit-l {
			animation: none;
		}
	}
	.lede-sub {
		font-family: var(--sans);
		font-size: 1.4rem;
		font-weight: 400;
		line-height: 1.5;
		color: var(--post); /* red */
		margin: 0 0 0.9em;
	}
	.lede-byline {
		font-family: var(--sans);
		font-size: 1rem;
		text-align: right;
		color: #ffffff;
		margin: 3em 0 2.8em;
		padding-bottom: 0.9em;
		border-bottom: 1px solid var(--line);
	}
	.lede-byline span {
		color: #ffffff;
		font-weight: 600;
	}
	.lede-sub strong {
		color: #d4a3c6; /* 50% between the gauge magenta (#a8478c) and white */
		font-weight: 700;
	}

	/* narrative bridges — read as an article column (prose + pull-quotes) */
	.turn {
		padding: 14vh 24px 4vh;
	}
	.turn-inner {
		max-width: 40rem;
		margin: 0 auto;
	}
	.turn-line {
		margin: 0 0 1.4em;
		font-family: var(--serif);
		font-weight: 400;
		font-size: 1.32rem;
		line-height: 1.62;
		color: #d7dade;
	}
	.turn-line.small {
		font-size: 1.2rem;
		color: #aeb2b8;
	}
	.turn-line em,
	.turn-quote em {
		font-style: italic;
		color: inherit;
	}
	.turn-quote {
		margin: 1.8em 0;
		padding: 0.1em 0 0.1em 1.1em;
		border-left: 3px solid var(--post);
		font-family: var(--serif);
		font-style: italic;
		font-size: 1.55rem;
		line-height: 1.34;
		color: #fff;
	}
	.turn-quote cite {
		display: block;
		margin-top: 0.9em;
		font-style: normal;
		font-size: 0.74rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--muted);
	}
	.turn-line.big {
		font-weight: 700;
		font-size: clamp(1.9rem, 4.6vw, 2.8rem);
		line-height: 1.16;
		letter-spacing: -0.01em;
		color: var(--ink);
		text-align: center;
		margin: 1.4em 0 0.4em;
	}
	.turn .hot {
		color: var(--post);
		font-style: normal;
		font-weight: 700;
	}

	.story {
		max-width: none;
	}
	/* the account-to-emotion flow */
	.flow-story {
		max-width: none;
		padding: 8vh 4vw 10vh;
	}
	.flow-inner {
		max-width: 1080px;
		margin: 0 auto;
	}
	.flow-h {
		font-family: var(--serif);
		font-weight: 700;
		font-size: clamp(1.9rem, 4vw, 2.8rem);
		line-height: 1.05;
		color: var(--ink);
		margin: 0 0 0.5em;
	}
	.flow-lede,
	.flow-note {
		font-family: var(--serif);
		font-size: 1.18rem;
		line-height: 1.55;
		color: #cfd2d6;
		max-width: 40em;
	}
	.flow-lede {
		margin: 0 0 2em;
	}
	.flow-note {
		margin: 1.6em 0 0;
	}
	/* Act 6.5 — cast pack: circles parked on the right, cards ride up the left */
	/* payoff: prose with the Mean-o-meter embedded inline (same dark bg as the wall) */
	.mean-reveal {
		max-width: none;
		background: var(--bg);
		padding: 1vh 0 10vh;
	}
	.mr-text {
		max-width: 620px;
		margin: 0 auto;
		padding: 6vh 24px 0;
	}
	.mr-text:first-child {
		padding-top: 8vh;
	}
	/* two prose paragraphs in a row read as one block, not two sections apart */
	.mr-text + .mr-text {
		padding-top: 1.1em;
	}
	.mr-text p {
		font-family: var(--serif);
		font-size: 1.32rem;
		line-height: 1.62;
		color: #e6e6e7;
		margin: 0;
	}
	.mr-block {
		max-width: 620px;
		margin: 4vh auto 0;
		padding: 0 24px;
	}
	.mr-h {
		font-family: var(--serif);
		font-weight: 700;
		font-size: 1.5rem;
		color: #fff;
		margin: 0 0 0.2em;
	}
	.mr-dek {
		font-family: var(--sans);
		font-size: 1.05rem;
		line-height: 1.45;
		color: var(--muted);
		margin: 0 0 1.4em;
	}
	.mr-chart {
		width: 100%;
	}
	.mr-chart :global(svg) {
		width: 100%;
		height: auto;
	}
	.facets {
		display: grid;
		grid-template-columns: 1.3fr 1fr 1fr;
		gap: 2.4em 14px;
		align-items: end;
	}
	@media (max-width: 820px) {
		.facets {
			grid-template-columns: 1fr;
			gap: 1.4em;
		}
	}
	.facet-head {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 4px;
		font-family: var(--sans);
	}
	.facet-dot {
		width: 20px;
		height: 3px;
		border-radius: 2px;
	}
	.facet-name {
		font-weight: 700;
		font-size: 0.95rem;
		color: #e6e6e7;
	}
	.facet-range {
		font-size: 0.75rem;
		color: var(--muted);
	}
	.cast-story {
		max-width: none;
		/* desktop: circle pack on the LEFT, scroll cards ride up the RIGHT lane.
		   both nudged right (bigger left inset, smaller right inset) so the whole thing sits
		   more centred rather than hugging the left edge */
		--chart-left: 6vw;
		--chart-right: 40%;
	}
	.cast-story :global(.foreground) {
		pointer-events: none;
	}
	/* the Scroller pins the cast pack as a pointer-events:none background; re-enable it so
	   the reader can hover a face to see how the account portrayed them */
	.cast-story :global(.background-container) {
		pointer-events: auto;
	}
	.cast-step.cast-tail {
		height: 100vh; /* pack-only beat before the section scrolls away (beats base + mobile height) */
	}
	.cast-step {
		height: 110vh;
		display: flex;
		align-items: center;
		/* park the card at the left end of the RIGHT lane so it hugs the circles (pack on the left) */
		justify-content: flex-start;
		padding-left: calc(100% - var(--chart-right) + 1.5vw);
		padding-right: 3vw;
		pointer-events: none;
	}
	.cast-step .card {
		margin: 0;
		max-width: 380px;
		pointer-events: auto; /* let the reader select/copy the card text */
	}
	/* narrow screens: stack — circles centred, card sits low and gets extra scroll room so it
	   clears the top of the screen (revealing the pack) before the next step arrives */
	@media (max-width: 820px) {
		.cast-story {
			/* mobile: pack fills the width again (card centres over it) */
			--chart-left: 4vw;
			--chart-right: 2vw;
		}
		.cast-step {
			height: 175vh;
			justify-content: center;
			align-items: flex-end;
			padding: 0 4vw 8vh;
		}
		.cast-step .card {
			margin: 0 auto;
		}
	}
	.card :global(.hyp) {
		color: #e8863a;
		font-weight: 700;
	}
	.card :global(.att) {
		color: #a8478c;
		font-weight: 700;
	}
	/* let hovers/clicks reach the interactive words in the (background) field during
	   the explore act; foreground cards are text-only and need no pointer events */
	.story :global(.foreground) {
		pointer-events: none;
	}
	/* Scroller renders sections as direct children; each is one screen of scroll */
	.reveal-space {
		pointer-events: none;
	}
	.step {
		height: 118vh;
		display: flex;
		align-items: center;
		justify-content: center;
		pointer-events: none;
	}
	.card {
		max-width: 460px;
		margin: 0 auto;
		background: #ffffff;
		padding: 22px 26px;
		pointer-events: auto; /* selectable/copyable even inside a pointer-events:none foreground */
		opacity: 0;
		transform: translateY(14px);
		transition:
			opacity 0.4s ease,
			transform 0.4s ease;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
	}
	.step.on .card,
	.cast-step.on .card {
		opacity: 1;
		transform: none;
	}
	.card h3 {
		font-family: var(--serif);
		font-weight: 700;
		font-size: 1.5rem;
		line-height: 1.12;
		margin: 0 0 0.4em;
		color: #16181c;
	}
	.card p {
		margin: 0;
		font-size: 1.02rem;
		color: #33373d;
	}
	.card :global(em) {
		font-style: normal;
		color: #16181c;
		font-weight: 700;
	}
	/* reply-guy card: four native clips shown like TikTok posts */
	.card.has-videos {
		max-width: 640px;
	}
	.card.has-chart {
		max-width: 640px;
	}
	.card-chart {
		margin: 1.1em 0 0.6em;
	}
	.chart-note {
		margin: 0 0 0.2em;
		font-family: var(--sans);
		font-size: 0.74rem;
		line-height: 1.4;
		color: #8a8f96;
	}
	.chart-note b {
		color: #5a5f66;
		font-weight: 700;
	}
	.tk-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 8px;
		margin-top: 1.1em;
	}
	.tk {
		background: #000;
		border-radius: 7px;
		overflow: hidden;
	}
	.tk-vid {
		position: relative;
		/* the source clips are 9:16 with black letterbox baked in; a shorter tile + object-fit:cover
		   crops the top/bottom black away so the receipts aren't extra-long */
		aspect-ratio: 3 / 4;
	}
	.tk-vid video {
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: top; /* keep the top of the clip; crop the black space off the BOTTOM */
		display: block;
	}
	.tk-views {
		position: absolute;
		left: 5px;
		bottom: 5px;
		font-family: var(--sans);
		font-size: 0.62rem;
		font-weight: 700;
		color: #fff;
		text-shadow: 0 1px 3px rgba(0, 0, 0, 0.85);
	}
	.tk-meta {
		padding: 5px 7px 7px;
		text-align: left;
	}
	.tk-handle {
		display: block;
		font-family: var(--sans);
		font-size: 0.64rem;
		font-weight: 700;
		color: #fff;
	}
	.tk-cap {
		display: block;
		font-family: var(--sans);
		font-size: 0.62rem;
		line-height: 1.25;
		color: #cfd2d6;
		margin: 1px 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.tk-date {
		display: block;
		font-family: var(--sans);
		font-size: 0.56rem;
		color: #8a8f96;
	}
	@media (max-width: 620px) {
		.card.has-videos {
			max-width: 340px;
		}
		.tk-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		/* keep enough headroom for the laser-eyes flare to show above "Before we begin"
		   (it extends well above the text); 13vh clipped it off the top */
		.ask {
			padding-top: 25vh;
		}
		/* mobile: header hugs the left, the randomizer link hugs the right */
		.ask-q {
			text-align: left;
		}
		.ask-skip {
			display: block;
			width: fit-content;
			margin-left: auto;
		}
		/* the opening white cards shouldn't sprawl */
		.open-card {
			max-width: 17em;
		}
		/* mobile type: dial down the dek, byline and body prose so they don't feel oversized */
		.dek {
			font-size: 0.85rem;
		}
		.lede-byline {
			font-size: 0.82rem;
		}
		.turn-line {
			font-size: 1.1rem;
		}
		.turn-line.small {
			font-size: 1.02rem;
		}
		.turn-quote {
			font-size: 1.25rem;
		}
		/* scale the scroll boxes (annotate + cast cards) down on mobile */
		.card {
			padding: 13px 15px;
		}
		.card h3 {
			font-size: 1.15rem;
		}
		.card p {
			font-size: 0.88rem;
		}
		.tk-meta {
			padding: 4px 5px 5px;
		}
		/* keep ALL body prose at the same small size on mobile. NOTE: several of these base rules
		   sit AFTER this media query in the file, so a plain selector loses on source order —
		   the .dbm prefix raises specificity so the mobile size reliably wins. */
		.dbm .mr-text p,
		.dbm .payoff-lede,
		.dbm .payoff-kicker,
		.dbm .after p,
		.dbm .ask-cont {
			font-size: 1.1rem !important;
		}
	}
	/* demonstrates the colour rule: "redder" as a red highlight chip with white text */
	.hl-red {
		background: rgb(238, 92, 108);
		color: #fff;
		font-weight: 700;
		padding: 0.04em 0.32em;
		border-radius: 3px;
	}
	.red-word {
		color: rgb(238, 92, 108);
		font-weight: 700;
	}

	.payoff {
		padding: 14vh 24px 4vh;
	}
	.payoff-kick-q {
		font-family: var(--sans);
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: #a8478c;
		margin: 0 0 0.7em;
	}
	.payoff-h {
		font-family: var(--serif);
		font-weight: 700;
		font-size: clamp(2rem, 5vw, 3rem);
		line-height: 1.05;
		color: #ffffff;
		margin: 0 0 0.5em;
	}
	.payoff-lede {
		font-family: var(--serif);
		font-size: 1.32rem;
		line-height: 1.6;
		color: #e6e6e7;
		margin: 0 0 1.3em;
	}
	.payoff-lede:last-of-type {
		margin-bottom: 2.6em;
	}
	.cs-swarm {
		margin: 0 0 1em;
	}
	.cstair {
		display: flex;
		flex-direction: column;
		gap: 1.05em;
		margin: 0 0 1em;
	}
	.cs-row {
		display: grid;
		grid-template-columns: 150px 1fr;
		align-items: center;
		gap: 16px;
	}
	.cs-cat {
		text-align: right;
		display: flex;
		flex-direction: column;
		line-height: 1.15;
	}
	.cs-label {
		font-family: var(--sans);
		font-weight: 700;
		font-size: 0.98rem;
		color: #f2f2f3;
	}
	.cs-desc {
		font-family: var(--sans);
		font-size: 0.7rem;
		color: var(--muted);
		margin-top: 2px;
	}
	.cs-track {
		height: 34px;
	}
	.cs-fill {
		height: 100%;
		min-width: 3.2em;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 10px;
		transition: width 1.15s cubic-bezier(0.22, 1, 0.36, 1);
	}
	.cs-val {
		font-family: var(--sans);
		font-weight: 700;
		font-size: 0.92rem;
		color: #fff;
		white-space: nowrap;
	}
	.cs-h {
		font-family: var(--serif);
		font-weight: 700;
		font-size: 1.5rem;
		color: #ffffff;
		margin: 0 0 0.15em;
	}
	.cs-dek {
		font-family: var(--sans);
		font-size: 0.92rem;
		color: #ffffff;
		margin: 0 0 0.5em;
	}
	.cs-dek-wrap {
		position: relative;
		margin: 0 0 1.4em;
	}
	.cs-dek-wrap .cs-dek {
		margin: 0;
	}
	.cs-legend {
		position: absolute;
		right: 0;
		bottom: 0; /* tuck into the empty space at the end of the dek's last line */
		display: flex;
		align-items: center;
		gap: 5px;
		margin: 0;
		font-family: var(--sans);
		font-size: 0.58rem;
		color: #ffffff;
	}
	.cs-legend-line {
		display: inline-block;
		width: 14px;
		height: 1.5px;
		background: #ffffff;
	}
	.payoff-body {
		font-family: var(--serif);
		font-size: 1.2rem;
		line-height: 1.6;
		color: #cfd2d6;
		margin: 2.4em 0 0;
	}
	.payoff-kicker {
		font-family: var(--serif);
		font-size: 1.32rem;
		line-height: 1.62;
		color: #e6e6e7;
		margin: 1.4em 0 0;
	}
	@media (max-width: 620px) {
		.cs-row {
			grid-template-columns: 110px 1fr;
			gap: 10px;
		}
		.cs-axis {
			margin-left: 120px;
		}
	}
	.after {
		padding: 7vh 24px 6vh;
		text-align: center;
	}
	.after p {
		font-family: var(--serif);
		font-size: 1.3rem;
		color: #cfd2d6;
		line-height: 1.5;
	}
	.after .b {
		color: var(--pre);
	}
	.after .post {
		color: var(--post);
	}
	.after .method-wrap {
		max-width: none;
		text-align: left;
	}
	.after .method-rule {
		margin: 0;
		border: 0;
		border-top: 1px solid rgba(255, 255, 255, 0.18);
	}
	.after .method-h {
		font-family: var(--sans);
		font-size: 0.8rem;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: #ffffff;
		margin: 2.2em 0 1.3em;
	}
	.after .method {
		font-size: 0.9rem;
		color: #ffffff;
		margin: 0 0 1.1em;
		line-height: 1.65;
	}
	.after .method b {
		color: #cfd2d6;
		font-weight: 600;
	}

	@media (max-width: 620px) {
		.card {
			max-width: none;
			margin: 0 4vw;
		}
	}
</style>
