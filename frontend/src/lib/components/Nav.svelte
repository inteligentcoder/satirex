<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '#lib/stores/auth.svelte';
	import { money } from '#lib/cosmetics';
	import Avatar from '#lib/components/Avatar.svelte';

	const links = [
		{ href: '/', label: 'Home' },
		{ href: '/shop', label: 'Shop' },
		{ href: '/fame', label: 'Hall of Fame' }
	];

	function logout() {
		auth.logout();
		goto('/');
	}
</script>

<header class="sticky top-0 z-30 border-b border-x-border bg-black/90 backdrop-blur">
	<div class="mx-auto flex w-full max-w-[600px] items-center gap-3 px-4 py-2.5">
		<a href="/" class="text-xl font-black tracking-tight">
			<span class="text-x-accent">Satire</span><span class="text-x-text">X</span>
		</a>

		<nav class="ml-2 flex items-center gap-1 text-sm">
			{#each links as link (link.href)}
				<a
					href={link.href}
					class="rounded-full px-3 py-1.5 text-x-text transition hover:bg-x-elevated hover:text-white"
				>
					{link.label}
				</a>
			{/each}
			{#if auth.isAdmin}
				<a
					href="/admin"
					class="rounded-full bg-purple-500/15 px-3 py-1.5 font-semibold text-purple-300 transition hover:bg-purple-500/25"
				>
					Admin
				</a>
			{/if}
		</nav>

		<div class="ml-auto flex items-center gap-2">
			{#if auth.isLoggedIn}
				<span
					class="hidden rounded-full bg-x-green/10 px-3 py-1 text-sm font-semibold text-x-green sm:inline"
					title="Fake money balance"
				>
					{money(auth.user?.balance)}
				</span>
				<a href={`/u/${auth.user.username}`} class="flex items-center gap-2">
					<Avatar user={auth.user} size={34} />
					<span class="hidden text-sm font-semibold sm:inline">{auth.user.display_name}</span>
				</a>
				<button
					onclick={logout}
					class="rounded-full border border-x-border px-3 py-1 text-xs text-x-text hover:bg-x-elevated"
				>
					Log out
				</button>
			{:else}
				<a href="/login" class="rounded-full px-3 py-1.5 text-sm text-x-text hover:bg-x-elevated">
					Log in
				</a>
				<a
					href="/register"
					class="rounded-full bg-x-accent px-3 py-1.5 text-sm font-semibold text-white hover:bg-x-accent-hover"
				>
					Sign up
				</a>
			{/if}
		</div>
	</div>
</header>
