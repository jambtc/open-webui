export type ChatErrorKind = 'network' | 'timeout' | 'auth' | 'server' | 'generic';

export interface MappedChatError {
	kind: ChatErrorKind;
	titleKey: string;
	bodyKey: string;
}

const toText = (raw: unknown): string => {
	if (!raw) return '';
	if (typeof raw === 'string') return raw;
	if (typeof raw === 'object') {
		const r = raw as Record<string, any>;
		if (r?.error?.message) return String(r.error.message);
		if (r?.detail) return String(r.detail);
		if (r?.message) return String(r.message);
		try {
			return JSON.stringify(raw);
		} catch {
			return '';
		}
	}
	return String(raw);
};

const statusOf = (raw: unknown): number | null => {
	if (raw && typeof raw === 'object') {
		const r = raw as Record<string, any>;
		const s = r?.status ?? r?.statusCode ?? r?.error?.status ?? r?.response?.status;
		if (typeof s === 'number') return s;
	}
	return null;
};

const has = (haystack: string, needle: string) => haystack.indexOf(needle) !== -1;

export const mapChatError = (raw: unknown): MappedChatError => {
	const text = toText(raw).toLowerCase();
	const status = statusOf(raw);

	if (
		status === 408 ||
		status === 504 ||
		has(text, 'timeout') ||
		has(text, 'timed out') ||
		has(text, 'etimedout')
	) {
		return {
			kind: 'timeout',
			titleKey: 'Request took too long',
			bodyKey:
				"The agent didn't respond in time. This is usually temporary — please try again in a few moments."
		};
	}

	if (
		has(text, 'failed to fetch') ||
		has(text, 'networkerror') ||
		has(text, 'network request failed') ||
		has(text, 'econnrefused') ||
		has(text, 'econnreset') ||
		has(text, 'enotfound') ||
		has(text, 'network')
	) {
		return {
			kind: 'network',
			titleKey: 'Connection issue',
			bodyKey:
				"I wasn't able to reach the network to complete your request. This is likely a temporary hiccup — please try again in a few moments."
		};
	}

	if (status === 401 || status === 403) {
		return {
			kind: 'auth',
			titleKey: 'Authorization issue',
			bodyKey:
				"It looks like you're not authorized to perform this action. Try refreshing the page or signing in again."
		};
	}

	if ((status !== null && status >= 500) || has(text, 'internal server error')) {
		return {
			kind: 'server',
			titleKey: 'Service temporarily unavailable',
			bodyKey: 'The service is having trouble right now. Please try again in a few moments.'
		};
	}

	return {
		kind: 'generic',
		titleKey: "Something didn't work",
		bodyKey: "I couldn't complete your request. Please try again in a few moments."
	};
};
