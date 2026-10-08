<script lang="ts">
	import { mediaUrl } from '#lib/api';

	let {
		user,
		size = 48,
		ring = true
	}: { user: any; size?: number; ring?: boolean } = $props();

	const src = $derived(user?.avatar_url ? mediaUrl(user.avatar_url) : '');
	const initial = $derived(
		(user?.display_name || user?.username || '?').charAt(0).toUpperCase()
	);
	const frameUrl = $derived(ring && user?.frame?.url ? mediaUrl(user.frame.url) : '');
	const inset = $derived(Math.max(1, Math.round(size * 0.08)));
</script>

<span class="relative inline-block shrink-0" style="width:{size}px;height:{size}px">
	<span
		class="absolute grid place-items-center overflow-hidden rounded-full bg-x-elevated font-bold text-white"
		style="inset:{inset}px;font-size:{size * 0.4}px"
	>
		{#if src}
			<img src={src} alt="" class="h-full w-full object-cover" />
		{:else}
			{initial}
		{/if}
	</span>
	{#if frameUrl}
		<img
			src={frameUrl}
			alt=""
			class="pointer-events-none absolute inset-0 h-full w-full object-contain"
		/>
	{/if}
</span>
