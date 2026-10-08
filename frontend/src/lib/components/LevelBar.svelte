<script lang="ts">
	import { levelColor } from '#lib/cosmetics';

	let { level }: { level: any } = $props();
	const color = $derived(levelColor(level?.level ?? 1));
</script>

<div class="w-full">
	<div class="flex items-center justify-between text-xs text-x-muted">
		<span class="font-semibold" style="color:{color}">
			Lv {level?.level ?? 1} · {level?.title ?? ''}
		</span>
		<span>{level?.xp ?? 0} XP</span>
	</div>
	<div class="mt-1 h-2 w-full overflow-hidden rounded-full bg-x-surface">
		<div
			class="h-full rounded-full transition-all"
			style="width:{Math.round((level?.progress ?? 0) * 100)}%;background:{color}"
		></div>
	</div>
	<div class="mt-1 text-right text-[11px] text-x-muted">
		{level?.xp_needed ?? 0} XP to next level
	</div>
</div>
