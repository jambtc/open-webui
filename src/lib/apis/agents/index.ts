import { WEBUI_API_BASE_URL } from '$lib/constants';

export type AgentItem = {
	agent_id: string;
	name: string | null;
	workspace: string | null;
	model: string | null;
	model_fallbacks: string[] | null;
	is_default: boolean;
};

export type AgentsListResponse = {
	default_agent_id: string | null;
	main_key: string | null;
	scope: string | null;
	items: AgentItem[];
};

export const getAgents = async (token: string = ''): Promise<AgentsListResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err?.detail ?? err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
