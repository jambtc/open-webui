<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import {
		getAgentById,
		updateAgent,
		deleteAgent,
		getAgentKnowledgeTree,
		createAgentKnowledgeFolder,
		deleteAgentKnowledgeFolder,
		uploadAgentKnowledgeFile,
		deleteAgentKnowledgeFile,
		getAgentKnowledgeFileContent,
		getAgentKnowledgeFileDownloadUrl,
		type AgentDetailResponse,
		type AgentKnowledgeFileContentResponse,
		type AgentKnowledgeTreeResponse,
		type UpdateAgentPayload
	} from '$lib/apis/agents';
	import { mobile, showArchivedChats, showSidebar, user } from '$lib/stores';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import EditAgentModal from '$lib/components/agents/EditAgentModal.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Eye from '$lib/components/icons/Eye.svelte';
	import Download from '$lib/components/icons/Download.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');

	let loaded = false;
	let errorMessage = '';
	let agent: AgentDetailResponse | null = null;
	let knowledgeTree: AgentKnowledgeTreeResponse | null = null;
	let knowledgeLoading = false;
	let knowledgeError = '';
	let currentKnowledgePath = '';
	let knowledgeFileInput: HTMLInputElement | null = null;
	let showKnowledgePreviewModal = false;
	let knowledgePreviewLoading = false;
	let knowledgePreview: AgentKnowledgeFileContentResponse | null = null;
	let showEditAgentModal = false;
	let editLoading = false;
	let deleteLoading = false;

	const getAgentWorkspace = (currentAgent: AgentDetailResponse | null) => {
		if (!currentAgent) return '';

		if (typeof currentAgent.workspace === 'string' && currentAgent.workspace.trim()) {
			return currentAgent.workspace.trim();
		}

		const identity = currentAgent.identity ?? {};
		const candidates = [
			identity?.workspace,
			identity?.cwd,
			identity?.root,
			identity?.path,
			identity?.workspace_path
		];

		for (const value of candidates) {
			if (typeof value === 'string' && value.trim()) {
				return value.trim();
			}
		}

		return '';
	};

	const loadAgent = async () => {
		errorMessage = '';
		agent = await getAgentById(localStorage.token, $page.params.agent_id);
		return agent;
	};

	const loadKnowledgeTree = async (path = currentKnowledgePath) => {
		knowledgeLoading = true;
		knowledgeError = '';
		try {
			knowledgeTree = await getAgentKnowledgeTree(localStorage.token, $page.params.agent_id, path);
			currentKnowledgePath = knowledgeTree?.path ?? path;
		} catch (error) {
			knowledgeError = `${error}`;
		} finally {
			knowledgeLoading = false;
		}
	};

	const openKnowledgeFolder = async (path: string) => {
		await loadKnowledgeTree(path);
	};

	const createKnowledgeFolderHandler = async () => {
		const base = currentKnowledgePath ? `${currentKnowledgePath}/` : '';
		const value = window.prompt('New folder path', base);
		if (value === null) return;

		const nextPath = value.trim().replace(/^\/+|\/+$/g, '');
		if (!nextPath) {
			toast.error('Folder path is required');
			return;
		}

		try {
			await createAgentKnowledgeFolder(localStorage.token, $page.params.agent_id, nextPath);
			toast.success('Folder created successfully');
			await loadKnowledgeTree(currentKnowledgePath);
		} catch (error) {
			toast.error(`${error}`);
		}
	};

	const deleteKnowledgeFolderHandler = async (itemPath: string, itemName: string) => {
		const confirmed = window.confirm(
			`Delete folder "${itemName}" and all its contents? This action cannot be undone.`
		);
		if (!confirmed) return;

		try {
			await deleteAgentKnowledgeFolder(localStorage.token, $page.params.agent_id, itemPath, true);
			toast.success('Folder deleted successfully');
			await loadKnowledgeTree(currentKnowledgePath);
		} catch (error) {
			toast.error(`${error}`);
		}
	};


	const triggerKnowledgeUpload = () => {
		knowledgeFileInput?.click();
	};

	const uploadKnowledgeFileHandler = async (event: Event) => {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		try {
			await uploadAgentKnowledgeFile(localStorage.token, $page.params.agent_id, file, currentKnowledgePath);
			toast.success('File uploaded successfully');
			await loadKnowledgeTree(currentKnowledgePath);
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			input.value = '';
		}
	};

	const deleteKnowledgeFileHandler = async (itemPath: string, itemName: string) => {
		const confirmed = window.confirm(`Delete file "${itemName}" from knowledge?`);
		if (!confirmed) return;

		try {
			await deleteAgentKnowledgeFile(localStorage.token, $page.params.agent_id, itemPath);
			toast.success('File deleted successfully');
			await loadKnowledgeTree(currentKnowledgePath);
		} catch (error) {
			toast.error(`${error}`);
		}
	};

	const viewKnowledgeFileHandler = async (itemPath: string) => {
		knowledgePreviewLoading = true;
		knowledgePreview = null;
		try {
			knowledgePreview = await getAgentKnowledgeFileContent(
				localStorage.token,
				$page.params.agent_id,
				itemPath
			);
			showKnowledgePreviewModal = true;
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			knowledgePreviewLoading = false;
		}
	};

	const downloadKnowledgeFileHandler = (itemPath: string) => {
		window.open(getAgentKnowledgeFileDownloadUrl($page.params.agent_id, itemPath), '_blank');
	};

	const knowledgeBreadcrumbs = (path: string) => {
		if (!path) return [];
		const parts = path.split('/').filter(Boolean);
		return parts.map((part, idx) => ({
			label: part,
			path: parts.slice(0, idx + 1).join('/')
		}));
	};

	const formatKnowledgeDate = (value: string | null) => {
		if (!value) return 'n/a';
		const date = new Date(value);
		if (Number.isNaN(date.getTime())) return value;
		return date.toLocaleString();
	};

	const formatBytes = (value: number | null) => {
		if (value === null || value === undefined) return 'n/a';
		if (value < 1024) return `${value} B`;
		const units = ['KB', 'MB', 'GB', 'TB'];
		let size = value / 1024;
		let idx = 0;
		while (size >= 1024 && idx < units.length - 1) {
			size /= 1024;
			idx += 1;
		}
		return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[idx]}`;
	};

	const waitForUpdatedAgent = async (payload: UpdateAgentPayload, maxAttempts = 8, delayMs = 250) => {
		for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
			const currentAgent = await getAgentById(localStorage.token, $page.params.agent_id);
			const currentWorkspace = getAgentWorkspace(currentAgent);
			const currentAvatar =
				typeof currentAgent?.identity?.avatar_url === 'string' ? currentAgent.identity.avatar_url.trim() : '';

			const matches =
				(payload.name === undefined || (currentAgent.name ?? '') === payload.name) &&
				(payload.workspace === undefined || currentWorkspace === payload.workspace) &&
				(payload.model === undefined || (currentAgent.model ?? '') === payload.model) &&
				(payload.avatar === undefined || currentAvatar === payload.avatar);

			if (matches) {
				agent = currentAgent;
				return currentAgent;
			}

			await new Promise((resolve) => setTimeout(resolve, delayMs));
		}

		return loadAgent();
	};

	const waitForDeletedAgent = async (agentId: string, attempts = 10, delayMs = 250) => {
		for (let attempt = 0; attempt < attempts; attempt += 1) {
			try {
				await getAgentById(localStorage.token, agentId);
				await new Promise((resolve) => setTimeout(resolve, delayMs));
			} catch (error) {
				if (`${error}`.toLowerCase().includes('not found')) {
					return true;
				}
				throw error;
			}
		}

		return false;
	};

	const updateAgentHandler = async (payload: UpdateAgentPayload) => {
		editLoading = true;
		try {
			await updateAgent(localStorage.token, $page.params.agent_id, payload);
			await waitForUpdatedAgent(payload);
			showEditAgentModal = false;
			toast.success('Agent updated successfully');
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			editLoading = false;
		}
	};

	const deleteAgentHandler = async () => {
		if (!agent || deleteLoading) return;

		const confirmed = window.confirm(
			`Delete agent "${agent.name ?? agent.agent_id}" and its files? This action cannot be undone.`
		);
		if (!confirmed) return;

		deleteLoading = true;
		try {
			await deleteAgent(localStorage.token, agent.agent_id, true);
			await waitForDeletedAgent(agent.agent_id);
			toast.success('Agent deleted successfully');
			await goto('/agents');
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			deleteLoading = false;
		}
	};

	onMount(async () => {
		try {
			await loadAgent();
			await loadKnowledgeTree('');
		} catch (error) {
			errorMessage = `${error}`;
		} finally {
			loaded = true;
		}
	});
</script>

<div
	class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''} max-w-full"
>
	<nav class="px-2 pt-1.5 backdrop-blur-xl w-full drag-region">
		<div class="flex items-center">
			{#if $mobile}
				<div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center">
					<Tooltip
						content={$showSidebar ? $i18n.t('Close Sidebar') : $i18n.t('Open Sidebar')}
						interactive={true}
					>
						<button
							id="sidebar-toggle-button"
							class="cursor-pointer flex rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
							on:click={() => {
								showSidebar.set(!$showSidebar);
							}}
						>
							<div class="self-center p-1.5">
								<Sidebar />
							</div>
						</button>
					</Tooltip>
				</div>
			{/if}

			<div class="ml-2 py-0.5 self-center flex items-center justify-between w-full">
				<div class="flex items-center gap-2 text-sm font-medium">
					<button
						type="button"
						class="rounded-lg px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
						on:click={() => goto('/agents')}
					>
						{$i18n.t('Agents')}
					</button>
					<span class="text-gray-400">/</span>
					<span class="text-gray-700 dark:text-gray-300">{$page.params.agent_id}</span>
				</div>

				<div class="self-center flex items-center gap-1">
					{#if $user !== undefined && $user !== null}
						<UserMenu
							className="w-[240px]"
							role={$user?.role}
							help={true}
							on:show={(e) => {
								if (e.detail === 'archived-chat') {
									showArchivedChats.set(true);
								}
							}}
						>
							<button
								class="select-none flex rounded-xl p-1.5 w-full hover:bg-gray-50 dark:hover:bg-gray-850 transition"
								aria-label="User Menu"
							>
								<div class="self-center">
									<img
										src={`${WEBUI_API_BASE_URL}/users/${$user?.id}/profile/image`}
										class="size-6 object-cover rounded-full"
										alt="User profile"
										draggable="false"
									/>
								</div>
							</button>
						</UserMenu>
					{/if}
				</div>
			</div>
		</div>
	</nav>

	<div class="flex-1 max-h-full overflow-y-auto px-5 py-4 @container">
		{#if !loaded}
			<div class="flex h-full items-center justify-center">
				<Spinner className="size-8" />
			</div>
		{:else if errorMessage}
			<div class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
				{errorMessage}
			</div>
		{:else if agent}
			<div class="mx-auto w-full max-w-4xl space-y-4">
				<div class="rounded-2xl border border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-900">
					<div class="flex items-start justify-between gap-4">
						<div>
							<h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
								{agent.name ?? agent.agent_id}
							</h1>
							<div class="mt-1 font-mono text-xs text-gray-500 dark:text-gray-400">
								{agent.agent_id}
							</div>
						</div>
						<div class="flex items-center gap-2">
							{#if agent.is_default}
								<span class="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-200">
									Default
								</span>
							{/if}
							<button
								type="button"
								class="rounded-xl border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
								on:click={() => {
									showEditAgentModal = true;
								}}
								disabled={deleteLoading}
							>
								{$i18n.t('Edit Agent')}
							</button>
							<button
								type="button"
								class="rounded-xl border border-red-200 px-3 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950/40"
								on:click={deleteAgentHandler}
								disabled={deleteLoading || editLoading}
							>
								{#if deleteLoading}
									<Spinner className="size-4" />
								{:else}
									Delete Agent
								{/if}
							</button>
						</div>
					</div>
				</div>

				<div class="grid gap-4 md:grid-cols-2">
					<div class="rounded-2xl border border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-900">
						<div class="text-sm font-medium text-gray-900 dark:text-gray-100">Summary</div>
						<dl class="mt-3 space-y-2 text-sm">
							<div>
								<dt class="text-gray-500 dark:text-gray-400">Workspace</dt>
								<dd class="text-gray-900 dark:text-gray-100">{getAgentWorkspace(agent) || 'n/a'}</dd>
							</div>
							<div>
								<dt class="text-gray-500 dark:text-gray-400">Model</dt>
								<dd class="text-gray-900 dark:text-gray-100">{agent.model ?? 'n/a'}</dd>
							</div>
							<div>
								<dt class="text-gray-500 dark:text-gray-400">Fallbacks</dt>
								<dd class="text-gray-900 dark:text-gray-100">{agent.model_fallbacks?.join(', ') ?? 'n/a'}</dd>
							</div>
						</dl>
					</div>

					<div class="rounded-2xl border border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-900">
						<div class="text-sm font-medium text-gray-900 dark:text-gray-100">Identity</div>
						{#if agent.identity}
							<pre class="mt-3 overflow-x-auto rounded-xl bg-gray-50 p-3 text-xs text-gray-700 dark:bg-gray-950 dark:text-gray-300">{JSON.stringify(agent.identity, null, 2)}</pre>
						{:else}
							<div class="mt-3 text-sm text-gray-500 dark:text-gray-400">No identity payload available.</div>
						{/if}
					</div>
				</div>

				<div class="rounded-2xl border border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-900">
					<div class="flex items-center justify-between gap-3">
						<div>
							<div class="text-sm font-medium text-gray-900 dark:text-gray-100">Knowledge</div>
							<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">Tree for /memory/knowledge. Upload uses the current folder shown below.</div>
						</div>
						<div class="flex items-center gap-2">
							<input bind:this={knowledgeFileInput} type="file" class="hidden" on:change={uploadKnowledgeFileHandler} />
							<button
								type="button"
								class="rounded-xl border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
								on:click={triggerKnowledgeUpload}
								disabled={knowledgeLoading}
							>
								Upload Here
							</button>
							<button
								type="button"
								class="rounded-xl border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
								on:click={createKnowledgeFolderHandler}
								disabled={knowledgeLoading}
							>
								New Folder
							</button>
							<button
								type="button"
								class="rounded-xl border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
								on:click={() => loadKnowledgeTree(currentKnowledgePath)}
								disabled={knowledgeLoading}
							>
								Refresh
							</button>
						</div>
					</div>

					<div class="mt-3 space-y-2 text-sm">
						<div>
							<span class="text-gray-500 dark:text-gray-400">Workspace:</span>
							<span class="ml-2 text-gray-900 dark:text-gray-100">{(knowledgeTree?.workspace ?? getAgentWorkspace(agent)) || 'n/a'}</span>
						</div>
						<div>
							<span class="text-gray-500 dark:text-gray-400">Root:</span>
							<span class="ml-2 font-mono text-xs text-gray-900 dark:text-gray-100">{knowledgeTree?.root ?? 'n/a'}</span>
						</div>
						<div>
							<span class="text-gray-500 dark:text-gray-400">Current upload target:</span>
							<span class="ml-2 font-mono text-xs text-gray-900 dark:text-gray-100">{currentKnowledgePath || 'root'}</span>
						</div>
					</div>

					<div class="mt-4 flex flex-wrap items-center gap-2 text-sm">
						<button
							type="button"
							class="rounded-lg border border-gray-200 px-2 py-1 text-gray-700 transition hover:bg-gray-50 disabled:cursor-default disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
							on:click={() => openKnowledgeFolder('')}
							disabled={!currentKnowledgePath || knowledgeLoading}
						>
							root
						</button>
						{#each knowledgeBreadcrumbs(currentKnowledgePath) as crumb}
							<span class="text-gray-400">/</span>
							<button
								type="button"
								class="rounded-lg border border-gray-200 px-2 py-1 text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
								on:click={() => openKnowledgeFolder(crumb.path)}
								disabled={knowledgeLoading}
							>
								{crumb.label}
							</button>
						{/each}
					</div>

					{#if knowledgeLoading}
						<div class="mt-4 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
							<Spinner className="size-4" /> Loading knowledge tree...
						</div>
					{:else if knowledgeError}
						<div class="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
							{knowledgeError}
						</div>
					{:else if knowledgeTree}
						<div class="mt-4 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-800">
							<div class="grid grid-cols-[minmax(0,1.6fr)_120px_180px_180px] gap-3 border-b border-gray-200 bg-gray-50 px-4 py-2 text-xs font-medium uppercase tracking-wide text-gray-500 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-400">
								<div>Name</div>
								<div>Size</div>
								<div>Updated</div>
								<div>Actions</div>
							</div>
							{#if knowledgeTree.items.length === 0}
								<div class="px-4 py-6 text-sm text-gray-500 dark:text-gray-400">No knowledge files or folders in this path.</div>
							{:else}
								{#each knowledgeTree.items as item (item.path)}
									<div class="grid grid-cols-[minmax(0,1.6fr)_120px_180px_180px] gap-3 border-t border-gray-100 px-4 py-3 text-sm dark:border-gray-850">
										<div class="min-w-0">
											{#if item.kind === 'folder'}
												<button
													type="button"
													class="font-medium text-blue-700 transition hover:underline dark:text-blue-300"
													on:click={() => openKnowledgeFolder(item.path)}
												>
													📁 {item.name}
												</button>
											{:else}
												<div class="text-gray-900 dark:text-gray-100">📄 {item.name}</div>
											{/if}
											<div class="mt-1 font-mono text-xs text-gray-500 dark:text-gray-400">{item.path}</div>
										</div>
										<div class="text-gray-600 dark:text-gray-300">{item.kind === 'file' ? formatBytes(item.size_bytes) : '—'}</div>
										<div class="text-gray-600 dark:text-gray-300">{formatKnowledgeDate(item.updated_at)}</div>
										<div class="flex items-start justify-start gap-2">
											{#if item.kind === 'file'}
												<Tooltip content="View" interactive={true}>
													<button
														type="button"
														class="rounded-lg border border-gray-200 p-1.5 text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
														on:click={() => viewKnowledgeFileHandler(item.path)}
														disabled={knowledgeLoading || knowledgePreviewLoading}
														aria-label="View file"
													>
														<Eye className="size-4" />
													</button>
												</Tooltip>
												<Tooltip content="Download" interactive={true}>
													<button
														type="button"
														class="rounded-lg border border-gray-200 p-1.5 text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-850"
														on:click={() => downloadKnowledgeFileHandler(item.path)}
														disabled={knowledgeLoading}
														aria-label="Download file"
													>
														<Download className="size-4" />
													</button>
												</Tooltip>
												<Tooltip content="Delete" interactive={true}>
													<button
														type="button"
														class="rounded-lg border border-red-200 p-1.5 text-red-700 transition hover:bg-red-50 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950/40"
														on:click={() => deleteKnowledgeFileHandler(item.path, item.name)}
														aria-label="Delete file"
													>
														<GarbageBin className="size-4" />
													</button>
												</Tooltip>
											{:else if item.kind === 'folder'}
												<Tooltip content="Delete Folder" interactive={true}>
													<button
														type="button"
														class="rounded-lg border border-red-200 p-1.5 text-red-700 transition hover:bg-red-50 dark:border-red-900 dark:text-red-300 dark:hover:bg-red-950/40"
														on:click={() => deleteKnowledgeFolderHandler(item.path, item.name)}
														aria-label="Delete folder"
													>
														<GarbageBin className="size-4" />
													</button>
												</Tooltip>
											{:else}
												<span class="text-gray-400">—</span>
											{/if}
										</div>
									</div>
								{/each}
							{/if}
						</div>
					{/if}
				</div>

				{#if agent.warnings?.length}
					<div class="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 dark:border-amber-900 dark:bg-amber-950/40">
						<div class="text-sm font-medium text-amber-900 dark:text-amber-200">Warnings</div>
						<ul class="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800 dark:text-amber-300">
							{#each agent.warnings as warning}
								<li>{warning}</li>
							{/each}
						</ul>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<EditAgentModal
	bind:show={showEditAgentModal}
	loading={editLoading}
	initialName={agent?.name ?? ''}
	initialWorkspace={getAgentWorkspace(agent)}
	initialModel={agent?.model ?? ''}
	initialAvatar={typeof agent?.identity?.avatar_url === 'string' ? agent.identity.avatar_url : ''}
	onSubmit={updateAgentHandler}
/>

<Modal size="lg" bind:show={showKnowledgePreviewModal}>
	<div class="flex items-center justify-between gap-4">
		<div>
			<div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
				{knowledgePreview?.filename ?? 'Knowledge File'}
			</div>
			{#if knowledgePreview}
				<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					{knowledgePreview.path}
				</div>
			{/if}
		</div>
	</div>

	<div class="mt-4 space-y-2 text-sm">
		{#if knowledgePreview}
			<div>
				<span class="text-gray-500 dark:text-gray-400">Mime:</span>
				<span class="ml-2 text-gray-900 dark:text-gray-100">{knowledgePreview.mime_type}</span>
			</div>
			<div>
				<span class="text-gray-500 dark:text-gray-400">Size:</span>
				<span class="ml-2 text-gray-900 dark:text-gray-100">{formatBytes(knowledgePreview.size_bytes)}</span>
			</div>
		{/if}
	</div>

	<div class="mt-4">
		{#if knowledgePreview && knowledgePreview.content_text !== null}
			<pre class="max-h-[60vh] overflow-auto rounded-xl bg-gray-50 p-4 text-xs text-gray-700 dark:bg-gray-950 dark:text-gray-300">{knowledgePreview.content_text}</pre>
		{:else if knowledgePreview}
			<div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300">
				Binary file preview is not available. Use Download instead.
			</div>
		{/if}
	</div>
</Modal>
