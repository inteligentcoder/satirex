<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '#lib/stores/auth.svelte';

	let username = $state('');
	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let error = $state('');
	let busy = $state(false);

	async function submit(event: Event) {
		event.preventDefault();
		busy = true;
		error = '';
		try {
			await auth.register(username, email, password, displayName);
			goto('/');
		} catch (e: any) {
			error = e.message;
		} finally {
			busy = false;
		}
	}
</script>

<div class="mx-auto max-w-md">
	<h1 class="mb-1 text-2xl font-black">Join SatireX</h1>
	<p class="mb-5 text-sm text-x-muted">
		Get $1,000 fake dollars and a free profile frame. Invest wisely (you cannot).
	</p>

	<form onsubmit={submit} class="flex flex-col gap-3">
		<input
			bind:value={username}
			placeholder="Username (letters, numbers, _)"
			pattern={'[A-Za-z0-9_]{3,32}'}
			required
			class="rounded-xl border-x-border bg-black"
		/>
		<input
			bind:value={displayName}
			placeholder="Display name (optional)"
			maxlength="64"
			class="rounded-xl border-x-border bg-black"
		/>
		<input
			bind:value={email}
			type="email"
			placeholder="Email"
			required
			class="rounded-xl border-x-border bg-black"
		/>
		<input
			bind:value={password}
			type="password"
			placeholder="Password (min 6 chars)"
			minlength="6"
			autocomplete="new-password"
			required
			class="rounded-xl border-x-border bg-black"
		/>
		{#if error}<p class="text-sm text-x-red">{error}</p>{/if}
		<button
			type="submit"
			disabled={busy}
			class="rounded-full bg-x-accent py-2 font-bold text-white hover:bg-x-accent-hover disabled:opacity-50"
		>
			{busy ? 'Creating…' : 'Create account'}
		</button>
	</form>

	<p class="mt-4 text-center text-sm text-x-muted">
		Already have one? <a href="/login" class="font-semibold text-x-accent hover:underline">Log in</a>
	</p>
</div>
