export function money(n: number | null | undefined): string {
	const value = n ?? 0;
	return (
		'$' +
		value.toLocaleString(undefined, {
			minimumFractionDigits: 0,
			maximumFractionDigits: 2
		})
	);
}

export function fontStyle(user: any): string {
	const family = user?.font?.family;
	return family ? `font-family:${family};` : '';
}

export function timeAgo(iso: string | null | undefined): string {
	if (!iso) return '';
	const then = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z').getTime();
	const seconds = Math.max(0, Math.floor((Date.now() - then) / 1000));
	const units: [number, string][] = [
		[60, 's'],
		[3600, 'm'],
		[86400, 'h'],
		[604800, 'd'],
		[2592000, 'w']
	];
	if (seconds < 60) return `${seconds}s`;
	if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
	if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
	if (seconds < 604800) return `${Math.floor(seconds / 86400)}d`;
	return new Date(then).toLocaleDateString();
}

export const LEVEL_COLORS = [
	'#94a3b8',
	'#22c55e',
	'#3b82f6',
	'#8b5cf6',
	'#ec4899',
	'#f59e0b',
	'#ef4444',
	'#14b8a6',
	'#eab308',
	'#f97316'
];

export function levelColor(level: number): string {
	return LEVEL_COLORS[(level - 1) % LEVEL_COLORS.length];
}
