<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { api } from '#lib/api';
	import { auth } from '#lib/stores/auth.svelte';
	import { timeAgo, fontStyle } from '#lib/cosmetics';
	import PostCard from '#lib/components/PostCard.svelte';
	import Avatar from '#lib/components/Avatar.svelte';
	import UserBadges from '#lib/components/UserBadges.svelte';

	let post = $state<any>(null);
	let comments = $state<any[]>([]);
	let content = $state('');
	let error = $state('');
	let busy = $state(false);

	async function load() {
		const id = page.params.id;
		error = '';
		try {
			post = await api(`/api/posts/${id}`);
			comments = await api(`/api/posts/${id}/comments`);
		} catch (e: any) {
			error = e.message;
			post = null;
		}
	}

	$effect(() => {
		page.params.id;
		load();
	});

	async function addComment(event: Event) {
		event.preventDefault();
		if (!content.trim()) return;
		busy = true;
		try {
			const c = await api(`/api/posts/${post.id}/comments`, { body: { content } });
			comments = [...comments, c];
			content = '';
			post = { ...post, comment_count: (post.comment_count ?? 0) + 1 };
		} catch (e: any) {
			error = e.message;
		} finally {
			busy = false;
		}
	}

	async function deleteComment(id: number) {
		if (!confirm('Delete comment?')) return;
		await api(`/api/comments/${id}`, { method: 'DELETE' });
		comments = comments.filter((c) => c.id !== id);
		post = { ...post, comment_count: Math.max(0, (post.comment_count ?? 1) - 1) };
	}
</script>

<div class="flex flex-col pb-10">
	<a href="/" class="flex items-center gap-2 px-4 py-3 text-sm font-semibold text-x-text hover:bg-x-elevated">
		<span class="text-lg">←</span> Post
	</a>

	{#if post}
		<PostCard {post} onchange={(id) => id && goto('/')} />

		<div class="border-t border-x-border px-4 py-3">
			<h2 class="mb-3 text-sm font-bold text-x-text">
				Comments ({post.comment_count ?? comments.length})
			</h2>

			{#if auth.isLoggedIn}
				<form onsubmit={addComment} class="mb-4 flex gap-2">
					<input
						bind:value={content}
						placeholder="Add a needlessly aggressive reply…"
						maxlength="1000"
						class="min-w-0 flex-1 rounded-xl border-x-border bg-black"
					/>
					<button
						type="submit"
						disabled={busy}
						class="rounded-full bg-x-accent px-4 text-sm font-bold text-white hover:bg-x-accent-hover disabled:opacity-50"
					>
						Reply
					</button>
				</form>
			{:else}
				<p class="mb-4 text-sm text-x-muted">
					<a href="/login" class="text-x-accent hover:underline">Log in</a> to comment.
				</p>
			{/if}

			<div class="flex flex-col gap-4">
				{#each comments as comment (comment.id)}
					<div class="flex gap-3">
						<a href={`/u/${comment.author.username}`}><Avatar user={comment.author} size={36} /></a>
						<div class="min-w-0 flex-1">
							<div class="flex flex-wrap items-center gap-1 text-xs">
								<span class="font-semibold">{comment.author.display_name}</span>
								<UserBadges user={comment.author} size={13} />
								<span class="text-x-muted">@{comment.author.username}</span>
								<span class="text-x-dim">· {timeAgo(comment.created_at)}</span>
								{#if auth.isAdmin || auth.user?.id === comment.author.id}
									<button
										onclick={() => deleteComment(comment.id)}
										class="ml-auto text-x-dim hover:text-x-red"
									>
										Delete
									</button>
								{/if}
							</div>
							<p class="whitespace-pre-wrap break-words text-sm" style={fontStyle(comment.author)}>
								{comment.content}
							</p>
						</div>
					</div>
				{/each}
				{#if comments.length === 0}
					<p class="py-4 text-center text-sm text-x-muted">No comments. Cowards.</p>
				{/if}
			</div>
		</div>
	{:else if error}
		<p class="py-10 text-center text-x-red">{error}</p>
	{:else}
		<p class="py-10 text-center text-x-muted">Loading post…</p>
	{/if}
</div>
