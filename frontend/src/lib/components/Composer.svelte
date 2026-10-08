<script lang="ts">
	import { api, mediaUrl } from '#lib/api';
	import { auth } from '#lib/stores/auth.svelte';
	import Avatar from './Avatar.svelte';

	let { onposted }: { onposted?: (post: any) => void } = $props();

	let content = $state('');
	let file = $state<File | null>(null);
	let previewUrl = $state('');
	let previewType = $state('');
	let busy = $state(false);
	let error = $state('');
	let fileInput: HTMLInputElement | undefined = $state();

	function pickFile(event: Event) {
		const input = event.target as HTMLInputElement;
		file = input.files?.[0] ?? null;
		if (previewUrl) URL.revokeObjectURL(previewUrl);
		if (file) {
			previewUrl = URL.createObjectURL(file);
			previewType = file.type.startsWith('video/') ? 'video' : 'image';
		} else {
			previewUrl = '';
		}
	}

	function clearFile() {
		file = null;
		if (previewUrl) URL.revokeObjectURL(previewUrl);
		previewUrl = '';
		if (fileInput) fileInput.value = '';
	}

	async function submit() {
		if (!content.trim() && !file) return;
		busy = true;
		error = '';
		try {
			let media_url: string | null = null;
			let media_type: string | null = null;
			let poster_url: string | null = null;
			if (file) {
				const form = new FormData();
				form.append('file', file);
				form.append('kind', 'post');
				const up = await api('/api/upload', { form });
				media_url = up.url;
				media_type = up.media_type;
				poster_url = up.poster_url ?? null;
			}
			const post = await api('/api/posts', { body: { content, media_url, media_type, poster_url } });
			content = '';
			clearFile();
			await auth.refresh();
			onposted?.(post);
		} catch (e: any) {
			error = e.message;
		} finally {
			busy = false;
		}
	}
</script>

<div class="border-b border-x-border px-4 py-3">
	<div class="flex gap-3">
		<Avatar user={auth.user} size={46} />
		<div class="min-w-0 flex-1">
			<textarea
				bind:value={content}
				rows="3"
				maxlength="2000"
				placeholder="What controversial nonsense are we posting today?"
				class="w-full resize-none border-0 bg-transparent p-0 text-[15px] placeholder-x-dim focus:ring-0"
			></textarea>

			{#if previewUrl}
				<div class="relative mt-2">
					{#if previewType === 'video'}
						<video src={previewUrl} controls class="max-h-80 w-full rounded-xl bg-black">
							<track kind="captions" />
						</video>
					{:else}
						<img src={previewUrl} alt="" class="max-h-80 w-full rounded-xl object-cover" />
					{/if}
					<button
						onclick={clearFile}
						class="absolute right-2 top-2 rounded-full bg-black/70 px-2 py-1 text-xs text-white"
					>
						Remove
					</button>
				</div>
			{/if}

			{#if error}
				<p class="mt-2 text-xs text-x-red">{error}</p>
			{/if}

			<div class="mt-2 flex items-center justify-between">
				<label class="cursor-pointer rounded-full px-2 py-1 text-sm text-x-muted hover:text-x-accent">
					<input
						bind:this={fileInput}
						type="file"
						accept="image/*,video/*"
						class="hidden"
						onchange={pickFile}
					/>
					📎 Media
				</label>
				<button
					onclick={submit}
					disabled={busy || (!content.trim() && !file)}
					class="rounded-full bg-x-accent px-5 py-1.5 text-sm font-bold text-white transition hover:bg-x-accent-hover disabled:opacity-40"
				>
					{busy ? 'Posting…' : 'Post'}
				</button>
			</div>
		</div>
	</div>
</div>
