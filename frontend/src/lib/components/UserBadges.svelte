<script lang="ts">
	let { user, size = 16 }: { user: any; size?: number } = $props();
</script>

{#if user?.is_verified}
	<svg
		viewBox="0 0 24 24"
		width={size}
		height={size}
		fill="#1d9bf0"
		class="inline-block shrink-0"
		aria-label="Verified"
	>
		<title>Verified account</title>
		<path
			d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81C14.67 2.63 13.43 1.75 12 1.75s-2.67.88-3.34 2.19c-1.39-.46-2.9-.2-3.91.81s-1.27 2.52-.81 3.91C2.63 9.33 1.75 10.57 1.75 12s.88 2.67 2.19 3.34c-.46 1.39-.2 2.9.81 3.91s2.52 1.27 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.67-.88 3.34-2.19c1.39.46 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34zm-11.71 4.2L6.8 12.46l1.41-1.42 2.26 2.26 4.8-5.23 1.47 1.36-6.2 6.77z"
		/>
	</svg>
{/if}

{#if user?.is_admin}
	<svg
		viewBox="0 0 24 24"
		width={size}
		height={size}
		fill="#a855f7"
		class="inline-block shrink-0"
		aria-label="Admin"
	>
		<title>Administrator</title>
		<path
			d="M12 1l3.09 6.26L22 8.27l-5 4.87L18.18 20 12 16.77 5.82 20 7 13.14l-5-4.87 6.91-1.01L12 1z"
		/>
	</svg>
{/if}
