<script lang="ts">
	import { api } from '#lib/api';
	import { money } from '#lib/cosmetics';
	import Avatar from '#lib/components/Avatar.svelte';
	import UserBadges from '#lib/components/UserBadges.svelte';

	let data = $state<any>(null);
	let error = $state('');
	let loading = $state(true);

	async function load() {
		loading = true;
		try {
			data = await api('/api/fame');
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		load();
	});

	const sections = [
		{ key: 'most_funded', title: '🤑 Most Funded', hint: 'Received the most fake money.', tone: 'text-x-green' },
		{ key: 'biggest_spenders', title: '💸 Biggest Spenders', hint: 'Gave away the most fake money.', tone: 'text-x-accent' },
		{ key: 'most_hated', title: '💀 Most Hated', hint: 'Collected the most dislikes.', tone: 'text-x-red' },
		{ key: 'richest', title: '👑 Richest', hint: 'Currently sitting on the biggest balance.', tone: 'text-yellow-400' }
	];
</script>

<div class="flex flex-col gap-4">
	<h1 class="text-2xl font-black">Hall of Fame &amp; Wall of Shame</h1>

	{#if loading}
		<p class="py-8 text-center text-x-muted">Counting the money…</p>
	{:else if error}
		<p class="py-8 text-center text-x-red">{error}</p>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2">
			{#each sections as section (section.key)}
				<section class="rounded-2xl border border-x-border bg-x-surface p-4">
					<h2 class="text-lg font-bold">{section.title}</h2>
					<p class="mb-3 text-xs text-x-muted">{section.hint}</p>
					<ol class="flex flex-col gap-2">
						{#each data[section.key] as entry, i (entry.user.id)}
							<li class="flex items-center gap-3">
								<span class="w-5 text-center text-sm font-bold text-x-muted">{i + 1}</span>
								<a href={`/u/${entry.user.username}`}><Avatar user={entry.user} size={36} /></a>
								<a href={`/u/${entry.user.username}`} class="min-w-0 flex-1 truncate text-sm font-semibold hover:underline">
									{entry.user.display_name}
								</a>
								<UserBadges user={entry.user} size={14} />
								<span class={`text-sm font-bold ${section.tone}`}>
									{section.key === 'most_hated' ? `${entry.total} ✖` : money(entry.total)}
								</span>
							</li>
						{/each}
						{#if data[section.key].length === 0}
							<li class="text-sm text-x-muted">No data yet.</li>
						{/if}
					</ol>
				</section>
			{/each}
		</div>
	{/if}
</div>
