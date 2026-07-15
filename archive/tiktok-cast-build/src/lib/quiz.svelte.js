export function scoreSentence(n, correct) {
	if (n === 0) return 'Tap a side to start guessing.';
	if (n === 1) return `You’ve guessed once and got it ${correct ? 'right' : 'wrong'}.`;
	const base = `You’ve guessed ${n} times and got ${correct} right`;
	const rate = correct / n;
	if (rate >= 0.75) return `${base} — better than most.`;
	if (rate >= 0.6) return `${base} — above a coin flip.`;
	if (rate >= 0.4) return `${base} — a coin flip.`;
	if (rate < 0.4) return `${base} — worse than a coin flip.`;
	return `${base}.`;
}

const KEY = 'tiktok-cast-quiz-v1';

export class QuizState {
	i = $state(0);
	guesses = $state([]);
	tellPending = $state(false);
	buttonOrder = $state(null);
	#pendingChoice = null;

	constructor(rounds, storage = globalThis.localStorage) {
		this.rounds = rounds;
		this.storage = storage;
		const saved = storage?.getItem(KEY);
		if (saved) {
			try {
				const s = JSON.parse(saved);
				if (s && typeof s === 'object' && Array.isArray(s.guesses)) {
					this.i = s.i;
					this.guesses = s.guesses;
					this.buttonOrder = s.buttonOrder;
				}
			} catch {
				// Corrupted storage — leave $state fields at their initial values (i=0, guesses=[])
			}
		}
		if (!this.buttonOrder) {
			this.buttonOrder = Math.random() < 0.5 ? ['dem', 'rep'] : ['rep', 'dem'];
		}
		this.#save();
	}

	get current() { return this.rounds[this.i] ?? null; }
	get n() { return this.guesses.length; }
	get correct() { return this.guesses.filter((g) => g.correct).length; }

	pick(choice) {
		if (!this.current) return null;
		if (this.current.tell) {
			// A second pick on the same tell round intentionally overwrites the pending choice (last tap wins).
			this.#pendingChoice = choice;
			this.tellPending = true;
			return null;
		}
		return this.#commit(choice);
	}

	guess(choice) {
		// Tell rounds must go through pick() → logTell(); bypass to avoid corrupted state.
		if (this.current?.tell) return null;
		return this.pick(choice) ?? (this.#pendingChoice != null ? this.#commit(this.#drain()) : null);
	}

	logTell(zone) {
		if (!this.tellPending) return null;
		this.tellPending = false;
		const r = this.#commit(this.#drain());
		return { ...r, tellZone: zone };
	}

	#drain() {
		const c = this.#pendingChoice;
		this.#pendingChoice = null;
		return c;
	}

	#commit(choice) {
		const round = this.current;
		const correct = choice === round.answer;
		this.guesses = [...this.guesses, { id: round.id, choice, correct }];
		this.i += 1;
		this.#save();
		return { correct, answer: round.answer };
	}

	#save() {
		try {
			this.storage?.setItem(
				KEY,
				JSON.stringify({ i: this.i, guesses: this.guesses, buttonOrder: this.buttonOrder })
			);
		} catch {
			// Private-mode Safari and storage-full environments throw on setItem — ignore silently.
		}
	}
}
