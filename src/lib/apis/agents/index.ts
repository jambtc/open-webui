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


export type AgentDetailResponse = AgentItem & {
	identity: Record<string, unknown> | null;
	files: Record<string, unknown>[] | null;
	warnings: string[];
};

export const getAgentById = async (
	token: string = '',
	agentId: string,
	includeFiles: boolean = false
): Promise<AgentDetailResponse> => {
	let error = null;

	const searchParams = new URLSearchParams();
	if (includeFiles) searchParams.append('include_files', 'true');

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/agents/${agentId}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		}
	)
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


export type CreateAgentPayload = {
	name: string;
	workspace: string;
	emoji?: string | null;
	avatar?: string | null;
};

export type AgentCreateResponse = {
	created: boolean;
	agent_id: string | null;
	name: string | null;
	workspace: string | null;
	openclaw_result?: Record<string, unknown> | null;
};

export const createAgent = async (
	token: string = '',
	body: CreateAgentPayload
): Promise<AgentCreateResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(body)
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


export type UpdateAgentPayload = {
	name?: string;
	workspace?: string;
	model?: string;
	avatar?: string;
};

export type AgentUpdateResponse = {
	updated: boolean;
	agent_id: string;
	openclaw_result?: Record<string, unknown> | null;
};

export const updateAgent = async (
	token: string = '',
	agentId: string,
	body: UpdateAgentPayload
): Promise<AgentUpdateResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/agents/${agentId}`, {
		method: 'PATCH',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(body)
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
