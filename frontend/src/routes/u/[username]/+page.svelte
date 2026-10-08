<script lang="ts">
	import { page } from '$app/state';
	import { api, mediaUrl } from '#lib/api';
	import { auth } from '#lib/stores/auth.svelte';
	import { money } from '#lib/cosmetics';
	import Avatar from '#lib/components/Avatar.svelte';
	import UserBadges from '#lib/components/UserBadges.svelte';
	import LevelBar from '#lib/components/LevelBar.svelte';
	import PostCard from '#lib/components/PostCard.svelte';

	let profile = $state<any>(null);
	let posts = $state<any[]>([]);
	let inventory = $state<any[]>([]);
	let error = $state('');
	let notice = $state('');
	let loading = $state(true);

	let showEdit = $state(false);
	let showSend = $state(false);
	let editName = $state('');
	let editBio = $state('');
	let uploadBusy = $state(false);

	let sendAmount = $state(100);
	let sendMessage = $state('');

	let promoCode = $state('');

	const isSelf = $derived(auth.user?.username === page.params.username);

	async function load() {
		const username = page.params.username;
		loading = true;
		error = '';
		try {
			profile = await api(`/api/users/${username}`);
			posts = await api(`/api/users/${username}/posts`);
			editName = profile.display_name;
			editBio = profile.bio;
			if (auth.user?.username === username) {
				inventory = await api('/api/shop/inventory');
			} else {
				inventory = [];
			}
		} catch (e: any) {
			error = e.message;
			profile = null;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		page.params.username;
		auth.user?.username;
		load();
	});

	async function saveProfile() {
		try {
			await api('/api/users/me', { method: 'PATCH', body: { display_name: editName, bio: editBio } });
			showEdit = false;
			await auth.refresh();
			await load();
		} catch (e: any) {
			error = e.message;
		}
	}

	async function uploadCosmetic(kind: 'avatar' | 'banner', event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		uploadBusy = true;
		error = '';
		try {
			const form = new FormData();
			form.append('file', file);
			form.append('kind', kind);
			const up = await api('/api/upload', { form });
			const body = kind === 'avatar' ? { avatar_url: up.url } : { banner_url: up.url };
			await api('/api/users/me', { method: 'PATCH', body });
			await auth.refresh();
			await load();
		} catch (e: any) {
			error = e.message;
		} finally {
			uploadBusy = false;
			input.value = '';
		}
	}

	async function equip(item: any) {
		try {
			await api('/api/shop/equip', { body: { key: item.key } });
			await auth.refresh();
			await load();
		} catch (e: any) {
			error = e.message;
		}
	}

	async function unequip(kind: string) {
		await api('/api/shop/unequip', { body: { key: kind } });
		await auth.refresh();
		await load();
	}

	async function sendMoney() {
		error = '';
		notice = '';
		try {
			const res = await api('/api/money/send', {
				body: { receiver_username: profile.username, amount: Number(sendAmount), message: sendMessage }
			});
			notice = `Sent ${money(res.transaction.amount)} to @${profile.username}!`;
			showSend = false;
			await auth.refresh();
			await load();
		} catch (e: any) {
			error = e.message;
		}
	}

	async function redeemPromo() {
		error = '';
		notice = '';
		try {
			const res = await api('/api/promo/redeem', { body: { code: promoCode } });
			notice = `Redeemed! +${money(res.amount)} (balance ${money(res.balance)})`;
			promoCode = '';
			await auth.refresh();
			await load();
		} catch (e: any) {
			error = e.message;
		}
	}

	const groups = [
		{ type: 'frame', label: 'Frames' },
		{ type: 'font', label: 'Fonts' },
		{ type: 'avatar', label: 'Profile pictures' },
		{ type: 'banner', label: 'Banners' }
	];
</script>

{#if loading}
	<p class="py-10 text-center text-x-muted">Loading profile…</p>
{:else if !profile}
	<p class="py-10 text-center text-x-red">{error || 'User not found'}</p>
{:else}
	<div class="flex flex-col pb-10">
		<div class="border-b border-x-border">
			<div class="h-40 w-full bg-gradient-to-r from-x-accent via-[#5b7cf5] to-x-purple">
				{#if profile.banner_url}
					<img src={mediaUrl(profile.banner_url)} alt="" class="h-40 w-full object-cover" />
				{/if}
			</div>

			<div class="relative px-4 pb-4">
				<div class="-mt-12 flex items-end justify-between">
					<Avatar user={profile} size={96} />
					<div class="flex gap-2">
						{#if isSelf}
							<button
								onclick={() => (showEdit = !showEdit)}
								class="rounded-full border border-x-border px-4 py-1.5 text-sm font-semibold hover:bg-x-elevated"
							>
								Edit profile
							</button>
						{:else if auth.isLoggedIn}
							<button
								onclick={() => (showSend = !showSend)}
								class="rounded-full bg-x-green px-4 py-1.5 text-sm font-bold text-white hover:bg-[#00a86f]"
							>
								💸 Send money
							</button>
						{/if}
					</div>
				</div>

				<div class="mt-3">
					<div class="flex flex-wrap items-center gap-1.5">
						<h1 class="text-xl font-black">{profile.display_name}</h1>
						<UserBadges user={profile} size={20} />
					</div>
					<p class="text-sm text-x-muted">@{profile.username}</p>
					{#if profile.bio}
						<p class="mt-2 text-sm text-x-text">{profile.bio}</p>
					{/if}

					<div class="mt-3 flex flex-wrap gap-4 text-sm">
						<span><b class="text-x-green">{money(profile.balance)}</b> <span class="text-x-muted">balance</span></span>
						<span><b>{profile.level?.xp ?? profile.xp}</b> <span class="text-x-muted">XP</span></span>
						<span class="text-x-muted">
							Joined {new Date(profile.created_at).toLocaleDateString()}
						</span>
					</div>

					<div class="mt-3 max-w-sm">
						<LevelBar level={profile.level} />
					</div>
				</div>
			</div>
		</div>

		{#if notice}
			<p class="rounded-xl bg-x-green/10 px-3 py-2 text-sm text-x-green">{notice}</p>
		{/if}
		{#if error}
			<p class="rounded-xl bg-x-red/10 px-3 py-2 text-sm text-x-red">{error}</p>
		{/if}

		{#if showSend}
			<div class="rounded-2xl border border-x-border bg-x-surface p-3">
				<h2 class="mb-2 text-sm font-bold">Send fake money to @{profile.username}</h2>
				<div class="flex flex-wrap gap-2">
					<input type="number" min="1" bind:value={sendAmount} class="w-28 rounded-xl border-x-border bg-black" />
					<input bind:value={sendMessage} placeholder="Message (optional)" maxlength="255" class="min-w-0 flex-1 rounded-xl border-x-border bg-black" />
					<button onclick={sendMoney} class="rounded-full bg-x-green px-4 py-1.5 text-sm font-bold hover:bg-[#00a86f]">Send</button>
				</div>
			</div>
		{/if}

		{#if isSelf && showEdit}
			<div class="rounded-2xl border border-x-border bg-x-surface p-3">
				<h2 class="mb-3 text-sm font-bold">Edit profile</h2>
				<div class="flex flex-col gap-2">
					<input bind:value={editName} maxlength="64" placeholder="Display name" class="rounded-xl border-x-border bg-black" />
					<textarea bind:value={editBio} maxlength="500" rows="3" placeholder="Bio" class="rounded-xl border-x-border bg-black"></textarea>
					<div class="flex flex-wrap gap-3 text-sm">
						<label class="cursor-pointer rounded-full border border-x-border px-3 py-1.5 hover:bg-x-elevated">
							<input type="file" accept="image/*" class="hidden" onchange={(e) => uploadCosmetic('avatar', e)} />
							Upload avatar
						</label>
						<label class="cursor-pointer rounded-full border border-x-border px-3 py-1.5 hover:bg-x-elevated">
							<input type="file" accept="image/*" class="hidden" onchange={(e) => uploadCosmetic('banner', e)} />
							Upload banner
						</label>
						{#if uploadBusy}<span class="text-x-muted">Compressing…</span>{/if}
					</div>
					<button onclick={saveProfile} class="self-start rounded-full bg-x-accent px-5 py-1.5 text-sm font-bold hover:bg-x-accent-hover">
						Save
					</button>
				</div>
			</div>
		{/if}

		{#if isSelf}
			<div class="rounded-2xl border border-x-border bg-x-surface p-3">
				<h2 class="mb-2 text-sm font-bold">Redeem a promo code</h2>
				<div class="flex gap-2">
					<input bind:value={promoCode} placeholder="e.g. WELCOME" class="min-w-0 flex-1 rounded-xl border-x-border bg-black uppercase" />
					<button onclick={redeemPromo} class="rounded-full bg-purple-600 px-4 text-sm font-bold hover:bg-purple-500">Redeem</button>
				</div>
			</div>

			<div class="rounded-2xl border border-x-border bg-x-surface p-3">
				<h2 class="mb-2 text-sm font-bold">Your cosmetics</h2>
				{#if inventory.length === 0}
					<p class="text-sm text-x-muted">Nothing owned yet. Visit the <a href="/shop" class="text-x-accent hover:underline">shop</a>.</p>
				{:else}
					{#each groups as group (group.type)}
						{#if inventory.some((i) => i.type === group.type)}
							<p class="mt-2 text-xs font-semibold uppercase tracking-wide text-x-muted">{group.label}</p>
							<div class="mt-1 flex flex-wrap gap-2">
								{#each inventory.filter((i) => i.type === group.type) as item (item.id)}
									<button
										onclick={() => equip(item)}
										class="rounded-xl border border-x-border bg-black px-3 py-2 text-left text-xs hover:border-x-accent"
									>
										<div class="font-semibold">{item.name}</div>
										<div class="text-x-muted">Equip</div>
									</button>
								{/each}
							</div>
						{/if}
					{/each}
					{#if profile.frame}
						<button onclick={() => unequip('frame')} class="mt-3 text-xs text-x-muted hover:text-x-red">Remove frame</button>
					{/if}
				{/if}
			</div>
		{/if}

		<div class="mt-2 border-t border-x-border">
			<h2 class="px-4 py-3 text-lg font-bold">Posts</h2>
			{#if posts.length === 0}
				<p class="px-4 py-6 text-center text-sm text-x-muted">No posts yet.</p>
			{:else}
				<div class="flex flex-col">
					{#each posts as post (post.id)}
						<PostCard {post} onchange={(id) => id && (posts = posts.filter((p) => p.id !== id))} />
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}
