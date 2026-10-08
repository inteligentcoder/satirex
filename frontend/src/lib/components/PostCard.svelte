<script lang="ts">
	import { api, mediaUrl } from '#lib/api';
	import { auth } from '#lib/stores/auth.svelte';
	import { money, timeAgo, fontStyle } from '#lib/cosmetics';
	import Avatar from './Avatar.svelte';
	import UserBadges from './UserBadges.svelte';

	let { post, onchange }: { post: any; onchange?: (id?: number) => void } = $props();

	let override = $state<any>(null);
	const local = $derived(override ?? post);
	let showTip = $state(false);
	let tipAmount = $state(50);
	let tipMessage = $state('');
	let error = $state('');
	let busy = $state(false);

	const canModerate = $derived(auth.isAdmin || auth.user?.id === local.author?.id);

	async function vote(value: number) {
		if (!auth.isLoggedIn) return;
		try {
			busy = true;
			const next = local.viewer_vote === value ? 0 : value;
			override = await api(`/api/posts/${local.id}/vote`, { body: { value: next } });
		} catch (e: any) {
			error = e.message;
		} finally {
			busy = false;
		}
	}

	async function tip() {
		error = '';
		try {
			busy = true;
			const res = await api(`/api/posts/${local.id}/money`, {
				body: { receiver_username: local.author.username, amount: Number(tipAmount), message: tipMessage }
			});
			override = res.post;
			await auth.refresh();
			showTip = false;
			tipMessage = '';
		} catch (e: any) {
			error = e.message;
		} finally {
			busy = false;
		}
	}

	async function remove() {
		if (!confirm('Delete this post?')) return;
		await api(`/api/posts/${local.id}`, { method: 'DELETE' });
		onchange?.(local.id);
	}
</script>

<article class="border-b border-x-border px-4 py-3 transition hover:bg-[#080808]">
	<header class="flex items-start gap-3">
		<a href={`/u/${local.author.username}`}>
			<Avatar user={local.author} size={46} />
		</a>
		<div class="min-w-0 flex-1">
			<div class="flex flex-wrap items-center gap-1 text-sm">
				<a href={`/u/${local.author.username}`} class="font-bold hover:underline">
					{local.author.display_name}
				</a>
				<UserBadges user={local.author} />
				<span class="text-x-muted">@{local.author.username}</span>
				<span class="text-x-dim">·</span>
				<span class="text-x-muted">{timeAgo(local.created_at)}</span>
			</div>

			{#if local.content}
				<p class="mt-1 whitespace-pre-wrap break-words text-[15px]" style={fontStyle(local.author)}>
					{local.content}
				</p>
			{/if}

			{#if local.media_url && local.media_type === 'image'}
				<img
					src={mediaUrl(local.media_url)}
					alt=""
					class="mt-2 max-h-[520px] w-full rounded-xl border border-x-border object-cover"
					loading="lazy"
				/>
			{:else if local.media_url && local.media_type === 'video'}
				<video
					src={mediaUrl(local.media_url)}
					poster={mediaUrl(local.poster_url)}
					controls
					playsinline
					class="mt-2 max-h-[520px] w-full rounded-xl border border-x-border bg-black"
				>
					<track kind="captions" />
				</video>
			{/if}

			<div class="mt-3 flex items-center gap-4 text-sm text-x-muted">
				<button
					onclick={() => vote(1)}
					disabled={busy || !auth.isLoggedIn}
					class="flex items-center gap-1 transition hover:text-x-accent disabled:opacity-50"
					class:text-x-accent={local.viewer_vote === 1}
				>
					♥ {local.like_count}
				</button>
				<button
					onclick={() => vote(-1)}
					disabled={busy || !auth.isLoggedIn}
					class="flex items-center gap-1 transition hover:text-x-accent disabled:opacity-50"
					class:text-x-accent={local.viewer_vote === -1}
				>
					✖ {local.dislike_count}
				</button>
				<a href={`/post/${local.id}`} class="transition hover:text-white">💬 {local.comment_count}</a>
				{#if auth.isLoggedIn}
					<button
						onclick={() => (showTip = !showTip)}
						class="flex items-center gap-1 transition hover:text-x-green"
					>
						💸 Tip
					</button>
				{/if}
				{#if local.money_received > 0}
					<span class="ml-auto rounded-full bg-x-green/10 px-2 py-0.5 text-xs font-semibold text-x-green">
						{money(local.money_received)}
					</span>
				{/if}
				{#if canModerate}
					<button
						onclick={remove}
						class="ml-auto text-xs text-x-muted transition hover:text-x-red"
					>
						Delete
					</button>
				{/if}
			</div>

			{#if showTip}
				<div class="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-x-border bg-black p-2">
					<input
						type="number"
						min="1"
						bind:value={tipAmount}
						class="w-24 rounded-lg border-x-border bg-black text-sm"
					/>
					<input
						placeholder="Message (optional)"
						bind:value={tipMessage}
						maxlength="255"
						class="min-w-0 flex-1 rounded-lg border-x-border bg-black text-sm"
					/>
					<button
						onclick={tip}
						disabled={busy}
						class="rounded-lg bg-x-green px-3 py-1.5 text-sm font-semibold text-white hover:bg-[#00a86f] disabled:opacity-50"
					>
						Send
					</button>
				</div>
			{/if}

			{#if error}
				<p class="mt-2 text-xs text-x-red">{error}</p>
			{/if}
		</div>
	</header>
</article>
