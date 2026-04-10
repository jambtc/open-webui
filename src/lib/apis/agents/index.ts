import { WEBUI_API_BASE_URL } from '$lib/constants';

const jsonHeaders = {
	Accept: 'application/json',
	'Content-Type': 'application/json'
};

const authFetch = (input: RequestInfo | URL, init: RequestInit = {}) => {
	return fetch(input, {
		credentials: 'include',
		...init
	});
};

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

export const getAgents = async (_token: string = ''): Promise<AgentsListResponse> => {
	let error = null;

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents`, {
		method: 'GET',
		headers: jsonHeaders
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
	_token: string = '',
	agentId: string,
	includeFiles: boolean = false
): Promise<AgentDetailResponse> => {
	let error = null;

	const searchParams = new URLSearchParams();
	if (includeFiles) searchParams.append('include_files', 'true');

	const res = await authFetch(
		`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
		{
			method: 'GET',
			headers: jsonHeaders
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
	_token: string = '',
	body: CreateAgentPayload
): Promise<AgentCreateResponse> => {
	let error = null;

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents`, {
		method: 'POST',
		headers: jsonHeaders,
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
	_token: string = '',
	agentId: string,
	body: UpdateAgentPayload
): Promise<AgentUpdateResponse> => {
	let error = null;

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}`, {
		method: 'PATCH',
		headers: jsonHeaders,
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

export type AgentDeleteResponse = {
	deleted: boolean;
	agent_id: string;
	removed_bindings?: number | null;
	openclaw_result?: Record<string, unknown> | null;
};

export const deleteAgent = async (
	_token: string = '',
	agentId: string,
	deleteFiles: boolean = true
): Promise<AgentDeleteResponse> => {
	let error = null;
	const searchParams = new URLSearchParams();
	searchParams.append('delete_files', deleteFiles ? 'true' : 'false');

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}?${searchParams.toString()}`, {
		method: 'DELETE',
		headers: jsonHeaders
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

export type AgentKnowledgeTreeItem = {
	path: string;
	name: string;
	kind: 'file' | 'folder' | string;
	size_bytes: number | null;
	updated_at: string | null;
};

export type AgentKnowledgeTreeResponse = {
	agent_id: string;
	workspace: string;
	root: string;
	path: string;
	items: AgentKnowledgeTreeItem[];
};

export const getAgentKnowledgeTree = async (
	_token: string = '',
	agentId: string,
	path: string = ''
): Promise<AgentKnowledgeTreeResponse> => {
	let error = null;
	const searchParams = new URLSearchParams();
	if (path) searchParams.append('path', path);

	const res = await authFetch(
		`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}/knowledge/tree${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
		{
			method: 'GET',
			headers: jsonHeaders
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

export type AgentKnowledgeFolderMutationResponse = {
	ok: boolean;
	agent_id: string;
	path: string;
};

export const createAgentKnowledgeFolder = async (
	_token: string = '',
	agentId: string,
	path: string
): Promise<AgentKnowledgeFolderMutationResponse> => {
	let error = null;

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}/knowledge/folders`, {
		method: 'POST',
		headers: jsonHeaders,
		body: JSON.stringify({ path })
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

export type AgentKnowledgeFolderDeleteResponse = {
	deleted: boolean;
	agent_id: string;
	path: string;
};

export const deleteAgentKnowledgeFolder = async (
	_token: string = '',
	agentId: string,
	path: string,
	recursive: boolean = true
): Promise<AgentKnowledgeFolderDeleteResponse> => {
	let error = null;
	const searchParams = new URLSearchParams();
	searchParams.append('path', path);
	searchParams.append('recursive', recursive ? 'true' : 'false');

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}/knowledge/folders?${searchParams.toString()}`, {
		method: 'DELETE',
		headers: jsonHeaders
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

export type AgentKnowledgeFileMutationResponse = {
	ok: boolean;
	agent_id: string;
	path: string;
	filename: string;
	size_bytes: number;
	sha256: string;
	mime_type: string;
	updated_at: string;
};

export const uploadAgentKnowledgeFile = async (
	_token: string = '',
	agentId: string,
	file: File,
	path: string = '',
	overwrite: boolean = false
): Promise<AgentKnowledgeFileMutationResponse> => {
	let error = null;
	const formData = new FormData();
	formData.append('file', file);
	formData.append('path', path);
	formData.append('overwrite', overwrite ? 'true' : 'false');

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}/knowledge/files/upload`, {
		method: 'POST',
		headers: {
			Accept: 'application/json'
		},
		body: formData
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

export type AgentKnowledgeFileDeleteResponse = {
	deleted: boolean;
	agent_id: string;
	path: string;
};

export const deleteAgentKnowledgeFile = async (
	_token: string = '',
	agentId: string,
	path: string
): Promise<AgentKnowledgeFileDeleteResponse> => {
	let error = null;
	const searchParams = new URLSearchParams();
	searchParams.append('path', path);

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}/knowledge/files?${searchParams.toString()}`, {
		method: 'DELETE',
		headers: jsonHeaders
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

export type AgentKnowledgeFileContentResponse = {
	agent_id: string;
	path: string;
	filename: string;
	size_bytes: number;
	mime_type: string;
	updated_at: string;
	content_text: string | null;
	content_base64: string | null;
};

export const getAgentKnowledgeFileContent = async (
	_token: string = '',
	agentId: string,
	path: string
): Promise<AgentKnowledgeFileContentResponse> => {
	let error = null;
	const searchParams = new URLSearchParams();
	searchParams.append('path', path);

	const res = await authFetch(`${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}/knowledge/files/content?${searchParams.toString()}`, {
		method: 'GET',
		headers: jsonHeaders
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

export const getAgentKnowledgeFileDownloadUrl = (agentId: string, path: string) => {
	const searchParams = new URLSearchParams();
	searchParams.append('path', path);
	return `${WEBUI_API_BASE_URL}/boxedai/agents/${agentId}/knowledge/files/download?${searchParams.toString()}`;
};
