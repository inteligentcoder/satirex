<script lang="ts">
	import { api } from '#lib/api';
	import { auth } from '#lib/stores/auth.svelte';
	import Composer from '#lib/components/Composer.svelte';
	import PostCard from '#lib/components/PostCard.svelte';

	let posts = $state<any[]>([]);
	let loading = $state(true);
	let error = $state('');
	let sort = $state<'recent' | 'top' | 'rich'>('recent');

	async function load(s: string) {
		loading = true;
		error = '';
		try {
			posts = await api(`/api/posts?sort=${s}`);
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		const current = sort;
		load(current);
	});

	const sorts = [
		{ key: 'recent', label: 'Latest' },
		{ key: 'top', label: 'Top' },
		{ key: 'rich', label: 'Richest' }
	] as const;
</script>

<div class="flex flex-col pb-10">
	{#if auth.isLoggedIn}
		<Composer onposted={(post) => (posts = [post, ...posts])} />
	{:else}
		<div class="border-b border-x-border px-4 py-6 text-center text-sm text-x-muted">
			<a href="/login" class="font-semibold text-x-accent hover:underline">Log in</a>
			or
			<a href="/register" class="font-semibold text-x-accent hover:underline">sign up</a>
			to post, tip and flex.
		</div>
	{/if}

	<div class="flex gap-1 border-b border-x-border px-2 py-1">
		{#each sorts as s (s.key)}
			<button
				onclick={() => (sort = s.key)}
				class="relative rounded-full px-3 py-2 text-sm font-medium transition hover:bg-x-elevated"
				class:text-x-text={sort === s.key}
				class:font-bold={sort === s.key}
				class:text-x-muted={sort !== s.key}
			>
				{s.label}
				{#if sort === s.key}
					<span class="absolute inset-x-3 -bottom-[5px] h-1 rounded-full bg-x-accent"></span>
				{/if}
			</button>
		{/each}
	</div>

	{#if loading}
		<p class="py-8 text-center text-x-muted">Loading feed…</p>
	{:else if error}
		<p class="py-8 text-center text-x-red">{error}</p>
	{:else if posts.length === 0}
		<p class="py-8 text-center text-x-muted">No posts yet. Be the first to post nonsense.</p>
	{:else}
		{#each posts as post (post.id)}
			<PostCard {post} onchange={(id) => id && (posts = posts.filter((p) => p.id !== id))} />
		{/each}
	{/if}
</div>
