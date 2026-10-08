<script lang="ts">
	import { api, mediaUrl } from '#lib/api';
	import { auth } from '#lib/stores/auth.svelte';
	import { money } from '#lib/cosmetics';
	import Avatar from '#lib/components/Avatar.svelte';

	let stats = $state<any>(null);
	let users = $state<any[]>([]);
	let promos = $state<any[]>([]);
	let items = $state<any[]>([]);
	let search = $state('');
	let error = $state('');
	let notice = $state('');

	// new promo
	let pCode = $state('');
	let pAmount = $state(500);
	let pMaxUses = $state(0);

	// new item
	let iKey = $state('');
	let iName = $state('');
	let iType = $state('frame');
	let iPrice = $state(100);
	let iAsset = $state('');
	let iFont = $state('');
	let iAdminOnly = $state(false);
	let iDefault = $state(false);

	async function loadAll() {
		if (!auth.isAdmin) return;
		error = '';
		try {
			[stats, users, promos, items] = await Promise.all([
				api('/api/admin/stats'),
				api(`/api/admin/users?q=${encodeURIComponent(search)}`),
				api('/api/admin/promo'),
				api('/api/admin/items')
			]);
		} catch (e: any) {
			error = e.message;
		}
	}

	$effect(() => {
		auth.ready;
		auth.user?.is_admin;
		loadAll();
	});

	async function updateUser(user: any, body: any) {
		error = '';
		try {
			const updated = await api(`/api/admin/users/${user.id}`, { method: 'PATCH', body });
			users = users.map((u) => (u.id === updated.id ? updated : u));
		} catch (e: any) {
			error = e.message;
		}
	}

	async function deleteUser(user: any) {
		if (!confirm(`Delete @${user.username}? This nukes their posts.`)) return;
		await api(`/api/admin/users/${user.id}`, { method: 'DELETE' });
		users = users.filter((u) => u.id !== user.id);
	}

	async function createPromo() {
		error = '';
		notice = '';
		try {
			await api('/api/admin/promo', {
				body: { code: pCode, amount: Number(pAmount), max_uses: Number(pMaxUses), is_active: true }
			});
			notice = `Promo ${pCode.toUpperCase()} created.`;
			pCode = '';
			promos = await api('/api/admin/promo');
		} catch (e: any) {
			error = e.message;
		}
	}

	async function deletePromo(id: number) {
		await api(`/api/admin/promo/${id}`, { method: 'DELETE' });
		promos = promos.filter((p) => p.id !== id);
	}

	async function createItem() {
		error = '';
		notice = '';
		try {
			await api('/api/admin/items', {
				body: {
					key: iKey,
					name: iName,
					type: iType,
					price: Number(iPrice),
					asset_url: iAsset || null,
					font_family: iFont || null,
					is_admin_only: iAdminOnly,
					is_default: iDefault
				}
			});
			notice = `Item ${iKey} created.`;
			iKey = iName = iAsset = iFont = '';
			items = await api('/api/admin/items');
		} catch (e: any) {
			error = e.message;
		}
	}

	async function deleteItem(item: any) {
		if (!confirm(`Delete item ${item.key}?`)) return;
		await api(`/api/admin/items/${item.id}`, { method: 'DELETE' });
		items = items.filter((i) => i.id !== item.id);
	}

	async function toggleActive(item: any) {
		const updated = await api(`/api/admin/items/${item.id}`, {
			method: 'PATCH',
			body: { is_active: !item.is_active }
		});
		items = items.map((i) => (i.id === updated.id ? updated : i));
	}
</script>

{#if !auth.isAdmin}
	<div class="py-16 text-center">
		<h1 class="text-xl font-bold text-x-red">Admins only</h1>
		<p class="mt-2 text-sm text-x-muted">This area is reserved for staff accounts.</p>
	</div>
{:else}
	<div class="flex flex-col gap-4">
		<h1 class="text-2xl font-black">Admin Tools</h1>

		{#if notice}<p class="rounded-xl bg-x-green/10 px-3 py-2 text-sm text-x-green">{notice}</p>{/if}
		{#if error}<p class="rounded-xl bg-x-red/10 px-3 py-2 text-sm text-x-red">{error}</p>{/if}

		{#if stats}
			<div class="grid grid-cols-2 gap-3 sm:grid-cols-5">
				{#each Object.entries(stats) as [k, v] (k)}
					<div class="rounded-2xl border border-x-border bg-x-surface p-3 text-center">
						<div class="text-lg font-bold">{k === 'money_circulating' ? money(v as number) : v}</div>
						<div class="text-xs capitalize text-x-muted">{k.replaceAll('_', ' ')}</div>
					</div>
				{/each}
			</div>
		{/if}

		<!-- USERS -->
		<section class="rounded-2xl border border-x-border bg-x-surface p-4">
			<div class="mb-3 flex items-center gap-2">
				<h2 class="text-lg font-bold">Users</h2>
				<input bind:value={search} placeholder="Search…" class="ml-auto w-40 rounded-lg border-x-border bg-black text-sm" />
				<button onclick={loadAll} class="rounded-lg bg-x-elevated px-3 py-1 text-sm hover:bg-x-border">Search</button>
			</div>
			<div class="flex flex-col gap-2">
				{#each users as user (user.id)}
					<div class="flex flex-wrap items-center gap-2 rounded-xl border border-x-border bg-black p-2">
						<Avatar user={user} size={34} />
						<div class="min-w-0">
							<div class="truncate text-sm font-semibold">{user.display_name}</div>
							<div class="truncate text-xs text-x-muted">@{user.username} · {user.email}</div>
						</div>
						<div class="ml-auto flex flex-wrap items-center gap-2 text-xs">
							<button
								onclick={() => updateUser(user, { is_verified: !user.is_verified })}
								class="rounded-full px-2 py-1"
								class:bg-x-accent={user.is_verified}
								class:bg-x-elevated={!user.is_verified}
							>✔ Verified</button>
							<button
								onclick={() => updateUser(user, { is_admin: !user.is_admin })}
								class="rounded-full px-2 py-1"
								class:bg-purple-600={user.is_admin}
								class:bg-x-elevated={!user.is_admin}
							>★ Admin</button>
							<button
								onclick={() => updateUser(user, { is_banned: !user.is_banned })}
								class="rounded-full px-2 py-1"
								class:bg-x-red={user.is_banned}
								class:bg-x-elevated={!user.is_banned}
							>⛔ Ban</button>
							<input
								type="number"
								value={user.balance}
								onchange={(e) => updateUser(user, { balance: Number(e.currentTarget.value) })}
								class="w-24 rounded-lg border-x-border bg-black text-xs"
								title="Balance"
							/>
							<input
								type="number"
								value={user.xp}
								onchange={(e) => updateUser(user, { xp: Number(e.currentTarget.value) })}
								class="w-20 rounded-lg border-x-border bg-black text-xs"
								title="XP"
							/>
							<button onclick={() => deleteUser(user)} class="rounded-full bg-x-surface px-2 py-1 hover:bg-[#d31b26]">🗑</button>
						</div>
					</div>
				{/each}
			</div>
		</section>

		<!-- PROMOS -->
		<section class="rounded-2xl border border-x-border bg-x-surface p-4">
			<h2 class="mb-3 text-lg font-bold">Promo codes</h2>
			<div class="mb-3 flex flex-wrap gap-2">
				<input bind:value={pCode} placeholder="CODE" class="w-32 rounded-lg border-x-border bg-black text-sm uppercase" />
				<input type="number" bind:value={pAmount} placeholder="Amount" class="w-28 rounded-lg border-x-border bg-black text-sm" />
				<input type="number" bind:value={pMaxUses} placeholder="Max uses (0=∞)" class="w-36 rounded-lg border-x-border bg-black text-sm" />
				<button onclick={createPromo} class="rounded-full bg-x-accent px-4 text-sm font-bold hover:bg-x-accent-hover">Create</button>
			</div>
			<div class="flex flex-col gap-1">
				{#each promos as promo (promo.id)}
					<div class="flex items-center gap-3 rounded-lg bg-black px-3 py-1.5 text-sm">
						<span class="font-mono font-bold">{promo.code}</span>
						<span class="text-x-green">{money(promo.amount)}</span>
						<span class="text-xs text-x-muted">{promo.uses}/{promo.max_uses || '∞'} uses</span>
						<span class="text-xs" class:text-x-green={promo.is_active} class:text-x-dim={!promo.is_active}>
							{promo.is_active ? 'active' : 'off'}
						</span>
						<button onclick={() => deletePromo(promo.id)} class="ml-auto text-x-muted hover:text-x-red">Delete</button>
					</div>
				{/each}
			</div>
		</section>

		<!-- ITEMS -->
		<section class="rounded-2xl border border-x-border bg-x-surface p-4">
			<h2 class="mb-1 text-lg font-bold">Shop items</h2>
			<p class="mb-3 text-xs text-x-muted">
				Paste an uploaded asset URL (from <code>/api/upload</code>) or an external GIF/AVIF URL.
			</p>
			<div class="mb-3 grid gap-2 sm:grid-cols-2">
				<input bind:value={iKey} placeholder="key (e.g. frame_diamond)" class="rounded-lg border-x-border bg-black text-sm" />
				<input bind:value={iName} placeholder="Name" class="rounded-lg border-x-border bg-black text-sm" />
				<select bind:value={iType} class="rounded-lg border-x-border bg-black text-sm">
					<option value="frame">frame</option>
					<option value="font">font</option>
					<option value="avatar">avatar</option>
					<option value="banner">banner</option>
				</select>
				<input type="number" bind:value={iPrice} placeholder="Price" class="rounded-lg border-x-border bg-black text-sm" />
				{#if iType === 'font'}
					<input bind:value={iFont} placeholder="font-family: 'Impact', sans-serif" class="rounded-lg border-x-border bg-black text-sm sm:col-span-2" />
				{:else}
					<input bind:value={iAsset} placeholder="asset URL" class="rounded-lg border-x-border bg-black text-sm sm:col-span-2" />
				{/if}
			</div>
			<div class="mb-3 flex items-center gap-4 text-sm">
				<label class="flex items-center gap-2">
					<input type="checkbox" bind:checked={iAdminOnly} class="rounded border-x-border bg-black" /> Admin only
				</label>
				<label class="flex items-center gap-2">
					<input type="checkbox" bind:checked={iDefault} class="rounded border-x-border bg-black" /> Default (free for everyone)
				</label>
				<button onclick={createItem} class="ml-auto rounded-full bg-x-accent px-4 py-1 text-sm font-bold hover:bg-x-accent-hover">Create item</button>
			</div>
			<div class="flex flex-col gap-1">
				{#each items as item (item.id)}
					<div class="flex items-center gap-3 rounded-lg bg-black px-3 py-1.5 text-sm">
						{#if item.asset_url && item.type !== 'font'}
							<img src={mediaUrl(item.asset_url)} alt="" class="h-8 w-8 rounded object-cover" />
						{:else}
							<span class="grid h-8 w-8 place-items-center rounded bg-x-surface text-xs">Aa</span>
						{/if}
						<span class="font-semibold">{item.name}</span>
						<span class="rounded bg-x-surface px-1.5 text-xs">{item.type}</span>
						<span class="text-xs text-x-muted">{item.key}</span>
						<span class="text-x-green">{item.price === 0 ? 'Free' : money(item.price)}</span>
						{#if item.is_admin_only}<span class="text-xs text-purple-400">admin</span>{/if}
						{#if item.is_default}<span class="text-xs text-x-accent">default</span>{/if}
						<button onclick={() => toggleActive(item)} class="ml-auto text-xs text-x-muted hover:text-white">
							{item.is_active ? 'Disable' : 'Enable'}
						</button>
						<button onclick={() => deleteItem(item)} class="text-x-muted hover:text-x-red">Delete</button>
					</div>
				{/each}
			</div>
		</section>
	</div>
{/if}
