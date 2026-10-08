<script lang="ts">
	import { api, mediaUrl } from '#lib/api';
	import { auth } from '#lib/stores/auth.svelte';
	import { money } from '#lib/cosmetics';
	import Avatar from '#lib/components/Avatar.svelte';

	let items = $state<any[]>([]);
	let error = $state('');
	let notice = $state('');
	let busy = $state(false);
	let loading = $state(true);

	const groups = [
		{ type: 'frame', label: 'Profile frames', hint: 'Animated GIF rings around your avatar.' },
		{ type: 'font', label: 'Text fonts', hint: 'Change the font of your posts and comments.' },
		{ type: 'avatar', label: 'Profile pictures', hint: 'Ready-made gradient avatars.' },
		{ type: 'banner', label: 'Profile banners', hint: 'Make your profile header pop.' }
	];

	async function load() {
		loading = true;
		try {
			items = await api('/api/shop/items');
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		auth.user?.id;
		load();
	});

	function isEquipped(item: any): boolean {
		const u = auth.user;
		if (!u) return false;
		if (item.type === 'frame') return u.frame?.key === item.key;
		if (item.type === 'font') return u.font?.key === item.key;
		if (item.type === 'avatar') return u.avatar_url === item.asset_url;
		if (item.type === 'banner') return u.banner_url === item.asset_url;
		return false;
	}

	async function buy(item: any) {
		error = '';
		notice = '';
		busy = true;
		try {
			const res = await api('/api/shop/buy', { body: { key: item.key } });
			notice = `Bought ${item.name}! Balance: ${money(res.balance)}`;
			await auth.refresh();
			await load();
		} catch (e: any) {
			error = e.message;
		} finally {
			busy = false;
		}
	}

	async function equip(item: any) {
		error = '';
		notice = '';
		try {
			await api('/api/shop/equip', { body: { key: item.key } });
			await auth.refresh();
			notice = `Equipped ${item.name}.`;
		} catch (e: any) {
			error = e.message;
		}
	}
</script>

<div class="flex flex-col gap-4">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-black">Cosmetics Shop</h1>
		{#if auth.isLoggedIn}
			<span class="rounded-full bg-x-green/10 px-3 py-1 text-sm font-semibold text-x-green">
				{money(auth.user?.balance)}
			</span>
		{/if}
	</div>

	{#if !auth.isLoggedIn}
		<p class="text-sm text-x-muted">
			<a href="/login" class="text-x-accent hover:underline">Log in</a> to buy and equip cosmetics.
		</p>
	{/if}
	{#if notice}<p class="rounded-xl bg-x-green/10 px-3 py-2 text-sm text-x-green">{notice}</p>{/if}
	{#if error}<p class="rounded-xl bg-x-red/10 px-3 py-2 text-sm text-x-red">{error}</p>{/if}

	{#if loading}
		<p class="py-8 text-center text-x-muted">Loading shop…</p>
	{:else}
		{#each groups as group (group.type)}
			{@const list = items.filter((i) => i.type === group.type)}
			{#if list.length}
				<section>
					<h2 class="text-lg font-bold">{group.label}</h2>
					<p class="mb-2 text-xs text-x-muted">{group.hint}</p>
					<div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
						{#each list as item (item.id)}
							<div class="flex flex-col rounded-2xl border border-x-border bg-x-surface p-3">
								<div class="mb-2 grid h-24 place-items-center overflow-hidden rounded-xl bg-black">
									{#if item.type === 'frame'}
										<div class="relative h-24 w-24">
											<div
												class="absolute inset-[8%] rounded-full bg-gradient-to-br from-x-accent to-x-purple"
											></div>
											<img src={mediaUrl(item.asset_url)} alt="" class="absolute inset-0 h-24 w-24 object-contain" />
										</div>
									{:else if item.type === 'font'}
										<span class="text-xl" style="font-family:{item.font_family}">Aa Bb</span>
									{:else}
										<img
											src={mediaUrl(item.asset_url)}
											alt=""
											class={item.type === 'avatar' ? 'h-24 w-24 rounded-full object-cover' : 'h-24 w-full object-cover'}
										/>
									{/if}
								</div>
								<div class="flex-1">
									<div class="text-sm font-semibold">{item.name}</div>
									<div class="text-xs text-x-muted">{item.description}</div>
								</div>
								<div class="mt-2 flex items-center justify-between">
									<span class="text-sm font-bold text-x-green">
										{item.is_admin_only ? 'Admin' : item.price === 0 ? 'Free' : money(item.price)}
									</span>
									{#if !auth.isLoggedIn}
										<span class="text-xs text-x-dim">Login to buy</span>
									{:else if isEquipped(item)}
										<span class="text-xs font-semibold text-x-accent">Equipped</span>
									{:else if item.owned}
										<button onclick={() => equip(item)} class="rounded-full bg-x-elevated px-3 py-1 text-xs font-semibold hover:bg-x-border">
											Equip
										</button>
									{:else if item.is_admin_only}
										<span class="text-xs text-x-dim">Staff only</span>
									{:else}
										<button
											onclick={() => buy(item)}
											disabled={busy}
											class="rounded-full bg-x-accent px-3 py-1 text-xs font-bold hover:bg-x-accent-hover disabled:opacity-50"
										>
											Buy
										</button>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</section>
			{/if}
		{/each}
	{/if}
</div>
