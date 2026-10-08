import { api, loadToken, setToken } from '#lib/api';

class AuthStore {
	user = $state<any>(null);
	ready = $state(false);

	get isLoggedIn() {
		return this.user !== null;
	}
	get isAdmin() {
		return !!this.user?.is_admin;
	}

	async init() {
		const token = loadToken();
		if (!token) {
			this.ready = true;
			return;
		}
		try {
			this.user = await api('/api/auth/me');
		} catch {
			setToken(null);
			this.user = null;
		}
		this.ready = true;
	}

	async login(identifier: string, password: string) {
		const res = await api('/api/auth/login', {
			body: { identifier, password },
			auth: false
		});
		setToken(res.access_token);
		this.user = res.user;
		return res.user;
	}

	async register(username: string, email: string, password: string, display_name: string) {
		const res = await api('/api/auth/register', {
			body: { username, email, password, display_name },
			auth: false
		});
		setToken(res.access_token);
		this.user = res.user;
		return res.user;
	}

	async refresh() {
		if (!this.user) return;
		try {
			this.user = await api('/api/auth/me');
		} catch {
			/* keep existing */
		}
	}

	patch(partial: Record<string, unknown>) {
		this.user = { ...this.user, ...partial };
	}

	logout() {
		setToken(null);
		this.user = null;
	}
}

export const auth = new AuthStore();
