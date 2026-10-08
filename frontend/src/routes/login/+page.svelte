<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '#lib/stores/auth.svelte';

	let identifier = $state('');
	let password = $state('');
	let error = $state('');
	let busy = $state(false);

	async function submit(event: Event) {
		event.preventDefault();
		busy = true;
		error = '';
		try {
			await auth.login(identifier, password);
			goto('/');
		} catch (e: any) {
			error = e.message;
		} finally {
			busy = false;
		}
	}
</script>

<div class="mx-auto max-w-md">
	<h1 class="mb-1 text-2xl font-black">Welcome back</h1>
	<p class="mb-5 text-sm text-x-muted">Log in to waste more fake money.</p>

	<form onsubmit={submit} class="flex flex-col gap-3">
		<input
			bind:value={identifier}
			placeholder="Username or email"
			autocomplete="username"
			required
			class="rounded-xl border-x-border bg-black"
		/>
		<input
			bind:value={password}
			type="password"
			placeholder="Password"
			autocomplete="current-password"
			required
			class="rounded-xl border-x-border bg-black"
		/>
		{#if error}<p class="text-sm text-x-red">{error}</p>{/if}
		<button
			type="submit"
			disabled={busy}
			class="rounded-full bg-x-accent py-2 font-bold text-white hover:bg-x-accent-hover disabled:opacity-50"
		>
			{busy ? 'Logging in…' : 'Log in'}
		</button>
	</form>

	<p class="mt-4 text-center text-sm text-x-muted">
		No account? <a href="/register" class="font-semibold text-x-accent hover:underline">Sign up</a>
	</p>
	<p class="mt-2 text-center text-xs text-x-dim">
		Demo admin: <span class="text-x-muted">admin / admin1234</span>
	</p>
</div>
