declare global {
	interface Window {
		__SATIREX_API_BASE__?: string;
	}
}

function resolveApiBase(): string {
	if (typeof window !== 'undefined' && window.__SATIREX_API_BASE__) {
		return window.__SATIREX_API_BASE__;
	}
	const viteEnv = (import.meta as any).env;
	if (viteEnv?.VITE_API_BASE) {
		return viteEnv.VITE_API_BASE;
	}
	return 'http://localhost:8000';
}

/** Base URL of the FastAPI backend. Configure with VITE_API_BASE or window.__SATIREX_API_BASE__. */
export const API_BASE = resolveApiBase().replace(/\/+$/, '');

const TOKEN_KEY = 'satirex_token';
let token: string | null = null;

export function setToken(value: string | null) {
	token = value;
	if (typeof localStorage !== 'undefined') {
		if (value) localStorage.setItem(TOKEN_KEY, value);
		else localStorage.removeItem(TOKEN_KEY);
	}
}

export function loadToken(): string | null {
	if (typeof localStorage !== 'undefined') token = localStorage.getItem(TOKEN_KEY);
	return token;
}

export function getToken() {
	return token;
}

export function mediaUrl(path?: string | null): string {
	if (!path) return '';
	if (/^https?:\/\//.test(path)) return path;
	return API_BASE + path;
}

type ApiOptions = {
	method?: string;
	body?: unknown;
	form?: FormData;
	auth?: boolean;
};

export async function api<T = any>(path: string, opts: ApiOptions = {}): Promise<T> {
	const headers: Record<string, string> = {};
	let body: BodyInit | undefined;

	if (opts.form) {
		body = opts.form;
	} else if (opts.body !== undefined) {
		headers['Content-Type'] = 'application/json';
		body = JSON.stringify(opts.body);
	}

	if ((opts.auth ?? true) && token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	const method = opts.method || (body !== undefined ? 'POST' : 'GET');
	const res = await fetch(API_BASE + path, { method, headers, body });
	const text = await res.text();
	let data: any = null;
	if (text) {
		try {
			data = JSON.parse(text);
		} catch {
			data = text;
		}
	}

	if (!res.ok) {
		const detail = data?.detail;
		const message =
			typeof detail === 'string'
				? detail
				: Array.isArray(detail)
					? detail.map((d: any) => d.msg).join(', ')
					: `Request failed (${res.status})`;
		throw new Error(message);
	}
	return data as T;
}
