<script lang="ts">
	import './layout.css';
	import favicon from '#lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import Nav from '#lib/components/Nav.svelte';
	import { auth } from '#lib/stores/auth.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	onMount(() => {
		auth.init();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>SatireX — post to get rich (fake)</title>
</svelte:head>

<Nav />

<main class="mx-auto w-full max-w-[600px] pb-24 pt-0">
	{@render children()}
</main>
