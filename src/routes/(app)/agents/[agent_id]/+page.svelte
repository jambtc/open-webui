<script lang="ts">
	import { getContext, onDestroy, onMount } from 'svelte';
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
		uploadAgentKnowledgeFileBackground,
		deleteAgentKnowledgeFile,
		getAgentKnowledgeFileContent,
		getAgentKnowledgeFileDownloadUrl,
		getAgentKnowledgePendingTasks,
		getAgentKnowledgeTaskStatus,
		type AgentDetailResponse,
		type AgentKnowledgeFileContentResponse,
		type AgentKnowledgeTreeResponse,
		type AgentKnowledgeUploadTaskStatusResponse,
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
	let knowledgeTasks: AgentKnowledgeUploadTaskStatusResponse[] = [];
	let knowledgeTasksLoading = false;
	let trackedKnowledgeTaskIds: string[] = [];
	let taskTerminalNotified: Record<string, boolean> = {};
	let taskStatusById: Record<string, string> = {};
	let taskPollTimer: ReturnType<typeof setInterval> | null = null;
	let showEditAgentModal = false;
	let editLoading = false;
	let deleteLoading = false;
	let isKnowledgeDropActive = false;

	const humanizeAgentLabel = (value: string | null | undefined) => {
		const raw = (value ?? '').trim();
		if (!raw) return '';
		let out = raw;
		out = out.replace(
			/^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|u-[0-9a-f]{24})-(.+)$/i,
			'$1'
		);
		return out;
	};

	const debugAgent = (event: string, payload: Record<string, unknown> = {}) => {
		console.debug(`[agents.ui] ${event}`, {
			agent_id: $page.params.agent_id,
			currentKnowledgePath,
			...payload
		});
	};

	const loadAgent = async () => {
		errorMessage = '';
		debugAgent('agent.load.start');
		agent = await getAgentById(localStorage.token, $page.params.agent_id);
		debugAgent('agent.load.success', {
			name: agent?.name ?? null,
			is_default: agent?.is_default ?? null
		});
		return agent;
	};

	const loadKnowledgeTree = async (path = currentKnowledgePath) => {
		knowledgeLoading = true;
		knowledgeError = '';
		debugAgent('knowledge.tree.load.start', { requested_path: path });
		try {
			knowledgeTree = await getAgentKnowledgeTree(localStorage.token, $page.params.agent_id, path);
			currentKnowledgePath = knowledgeTree?.path ?? path;
			debugAgent('knowledge.tree.load.success', {
				requested_path: path,
				resolved_path: currentKnowledgePath,
				root: knowledgeTree?.root ?? null,
				items_count: knowledgeTree?.items?.length ?? 0
			});
		} catch (error) {
			knowledgeError = `${error}`;
			debugAgent('knowledge.tree.load.error', { requested_path: path, error: `${error}` });
		} finally {
			knowledgeLoading = false;
		}
	};

	const openKnowledgeFolder = async (path: string) => {
		debugAgent('knowledge.folder.open', { target_path: path });
		await loadKnowledgeTree(path);
	};

	const activeTaskStatuses = new Set(['pending', 'running']);

	const sortKnowledgeTasks = (items: AgentKnowledgeUploadTaskStatusResponse[]) => {
		return [...items].sort((a, b) => {
			const aTs = new Date(a.updated_at ?? a.created_at ?? 0).getTime();
			const bTs = new Date(b.updated_at ?? b.created_at ?? 0).getTime();
			return bTs - aTs;
		});
	};

	const formatTaskStatusLabel = (status: string) => {
		switch ((status || '').toLowerCase()) {
			case 'pending':
				return 'Pending';
			case 'running':
				return 'Processing';
			case 'succeeded':
				return 'Completed';
			case 'failed':
				return 'Failed';
			case 'expired':
				return 'Expired';
			default:
				return status || 'unknown';
		}
	};

	const formatTaskStatusClass = (status: string) => {
		switch ((status || '').toLowerCase()) {
			case 'pending':
				return 'bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300';
			case 'running':
				return 'bg-blue-100 text-blue-800 dark:bg-blue-950/40 dark:text-blue-300';
			case 'succeeded':
				return 'bg-green-100 text-green-800 dark:bg-green-950/40 dark:text-green-300';
			case 'failed':
			case 'expired':
				return 'bg-red-100 text-red-800 dark:bg-red-950/40 dark:text-red-300';
			default:
				return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
		}
	};

	const startTaskPolling = () => {
		if (taskPollTimer) return;
		taskPollTimer = setInterval(async () => {
			await refreshKnowledgeTasks();
		}, 2500);
	};

	const stopTaskPolling = () => {
		if (!taskPollTimer) return;
		clearInterval(taskPollTimer);
		taskPollTimer = null;
	};

	const refreshKnowledgeTasks = async () => {
		if (knowledgeTasksLoading) return;
		knowledgeTasksLoading = true;
		debugAgent('knowledge.tasks.refresh.start', {
			tracked_task_ids: [...trackedKnowledgeTaskIds]
		});

		try {
			const pending = await getAgentKnowledgePendingTasks(localStorage.token, $page.params.agent_id);

			const ids = new Set<string>(trackedKnowledgeTaskIds);
			for (const item of pending?.items ?? []) {
				ids.add(item.task_id);
			}
			for (const item of knowledgeTasks) {
				if (activeTaskStatuses.has((item.status || '').toLowerCase())) {
					ids.add(item.task_id);
				}
			}

			const nextTasks: AgentKnowledgeUploadTaskStatusResponse[] = [];
			for (const taskId of ids) {
				try {
					const task = await getAgentKnowledgeTaskStatus(localStorage.token, $page.params.agent_id, taskId);
					nextTasks.push(task);
				} catch (error) {
					if (`${error}`.toLowerCase().includes('not found')) {
						continue;
					}
					throw error;
				}
			}

			knowledgeTasks = sortKnowledgeTasks(nextTasks);

			let shouldRefreshTree = false;
			for (const task of knowledgeTasks) {
				const status = (task.status || '').toLowerCase();
				const previousStatus = (taskStatusById[task.task_id] || '').toLowerCase();
				taskStatusById[task.task_id] = status;
				if (previousStatus !== status) {
					debugAgent('knowledge.task.status.transition', {
						task_id: task.task_id,
						from: previousStatus || null,
						to: status,
						filename: task.filename ?? null,
						requested_path: task.requested_path ?? null
					});
				}

				if (status === 'succeeded' && previousStatus !== 'succeeded' && !taskTerminalNotified[task.task_id]) {
					taskTerminalNotified[task.task_id] = true;
					toast.success(`Upload completed: ${task.filename ?? task.requested_path}`);
					shouldRefreshTree = true;
				}

				if (
					(status === 'failed' || status === 'expired') &&
					previousStatus !== status &&
					!taskTerminalNotified[task.task_id]
				) {
					taskTerminalNotified[task.task_id] = true;
					toast.error(task.error_detail || `Upload ${status}: ${task.filename ?? task.requested_path}`);
				}
			}

			trackedKnowledgeTaskIds = knowledgeTasks
				.filter((task) => activeTaskStatuses.has((task.status || '').toLowerCase()))
				.map((task) => task.task_id);

			if (trackedKnowledgeTaskIds.length > 0) {
				startTaskPolling();
			} else {
				stopTaskPolling();
			}

			if (shouldRefreshTree) {
				debugAgent('knowledge.tasks.refresh.tree_reload', {
					reason: 'task_succeeded',
					path: currentKnowledgePath
				});
				await loadKnowledgeTree(currentKnowledgePath);
			}
		} catch (error) {
			console.error('Failed refreshing knowledge tasks', error);
			debugAgent('knowledge.tasks.refresh.error', { error: `${error}` });
		} finally {
			debugAgent('knowledge.tasks.refresh.end', {
				tracked_task_ids: [...trackedKnowledgeTaskIds],
				task_count: knowledgeTasks.length
			});
			knowledgeTasksLoading = false;
		}
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
			debugAgent('knowledge.folder.create.success', { folder_path: nextPath });
			toast.success('Folder created successfully');
			await loadKnowledgeTree(currentKnowledgePath);
		} catch (error) {
			debugAgent('knowledge.folder.create.error', { folder_path: nextPath, error: `${error}` });
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
			debugAgent('knowledge.folder.delete.success', { folder_path: itemPath, folder_name: itemName });
			toast.success('Folder deleted successfully');
			await loadKnowledgeTree(currentKnowledgePath);
		} catch (error) {
			debugAgent('knowledge.folder.delete.error', {
				folder_path: itemPath,
				folder_name: itemName,
				error: `${error}`
			});
			toast.error(`${error}`);
		}
	};


	const triggerKnowledgeUpload = () => {
		knowledgeFileInput?.click();
	};

	const queueKnowledgeUpload = async (file: File) => {
		const task = await uploadAgentKnowledgeFileBackground(
			localStorage.token,
			$page.params.agent_id,
			file,
			currentKnowledgePath
		);
		debugAgent('knowledge.file.upload.queued', {
			filename: file.name,
			target_path: currentKnowledgePath,
			task_id: task?.task_id ?? null
		});
		toast.success(`Upload queued: ${file.name}`);

		if (task?.task_id) {
			trackedKnowledgeTaskIds = Array.from(new Set([...trackedKnowledgeTaskIds, task.task_id]));
			startTaskPolling();
		}
	};

	const queueKnowledgeUploads = async (files: File[]) => {
		if (files.length === 0) return;
		let queuedCount = 0;

		for (const file of files) {
			try {
				await queueKnowledgeUpload(file);
				queuedCount += 1;
			} catch (error) {
				debugAgent('knowledge.file.upload.error', {
					filename: file.name,
					target_path: currentKnowledgePath,
					error: `${error}`
				});
				toast.error(`${error}`);
			}
		}

		if (queuedCount > 0) {
			await refreshKnowledgeTasks();
		}
	};

	const uploadKnowledgeFileHandler = async (event: Event) => {
		const input = event.currentTarget as HTMLInputElement;
		const files = input.files ? Array.from(input.files) : [];
		if (files.length === 0) return;

		try {
			await queueKnowledgeUploads(files);
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			input.value = '';
		}
	};

	const onKnowledgeDragOver = (event: DragEvent) => {
		event.preventDefault();
		if (knowledgeLoading) return;
		isKnowledgeDropActive = true;
	};

	const onKnowledgeDragLeave = (event: DragEvent) => {
		event.preventDefault();
		const target = event.currentTarget as HTMLElement | null;
		const related = event.relatedTarget as Node | null;
		if (target && related && target.contains(related)) return;
		isKnowledgeDropActive = false;
	};

	const onKnowledgeDrop = async (event: DragEvent) => {
		event.preventDefault();
		isKnowledgeDropActive = false;
		if (knowledgeLoading) return;
		const files = event.dataTransfer?.files ? Array.from(event.dataTransfer.files) : [];
		if (files.length === 0) return;
		debugAgent('knowledge.file.drop', {
			count: files.length,
			target_path: currentKnowledgePath
		});
		await queueKnowledgeUploads(files);
	};

	const onKnowledgeDropzoneKeydown = (event: KeyboardEvent) => {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			triggerKnowledgeUpload();
		}
	};

	const deleteKnowledgeFileHandler = async (itemPath: string, itemName: string) => {
		const confirmed = window.confirm(`Delete file "${itemName}" from knowledge?`);
		if (!confirmed) return;

		try {
			await deleteAgentKnowledgeFile(localStorage.token, $page.params.agent_id, itemPath);
			debugAgent('knowledge.file.delete.success', { file_path: itemPath, file_name: itemName });
			toast.success('File deleted successfully');
			await loadKnowledgeTree(currentKnowledgePath);
		} catch (error) {
			debugAgent('knowledge.file.delete.error', {
				file_path: itemPath,
				file_name: itemName,
				error: `${error}`
			});
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
			debugAgent('knowledge.file.preview.success', {
				file_path: itemPath,
				filename: knowledgePreview?.filename ?? null,
				mime_type: knowledgePreview?.mime_type ?? null,
				size_bytes: knowledgePreview?.size_bytes ?? null
			});
			showKnowledgePreviewModal = true;
		} catch (error) {
			debugAgent('knowledge.file.preview.error', { file_path: itemPath, error: `${error}` });
			toast.error(`${error}`);
		} finally {
			knowledgePreviewLoading = false;
		}
	};

	const downloadKnowledgeFileHandler = (itemPath: string) => {
		debugAgent('knowledge.file.download', { file_path: itemPath });
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

			const matches = payload.name === undefined || (currentAgent.name ?? '') === payload.name;

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
		debugAgent('agent.update.start', { payload });
		try {
			await updateAgent(localStorage.token, $page.params.agent_id, payload);
			await waitForUpdatedAgent(payload);
			debugAgent('agent.update.success', { payload });
			showEditAgentModal = false;
			toast.success('Agent updated successfully');
		} catch (error) {
			debugAgent('agent.update.error', { payload, error: `${error}` });
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
		debugAgent('agent.delete.start', {
			target_agent_id: agent.agent_id,
			target_agent_name: agent.name ?? null
		});
		try {
			await deleteAgent(localStorage.token, agent.agent_id, true);
			await waitForDeletedAgent(agent.agent_id);
			debugAgent('agent.delete.success', {
				target_agent_id: agent.agent_id,
				target_agent_name: agent.name ?? null
			});
			toast.success('Agent deleted successfully');
			await goto('/agents');
		} catch (error) {
			debugAgent('agent.delete.error', {
				target_agent_id: agent.agent_id,
				target_agent_name: agent.name ?? null,
				error: `${error}`
			});
			toast.error(`${error}`);
		} finally {
			deleteLoading = false;
		}
	};

	onMount(async () => {
		try {
			await loadAgent();
			await loadKnowledgeTree('');
			await refreshKnowledgeTasks();
		} catch (error) {
			errorMessage = `${error}`;
		} finally {
			loaded = true;
		}
	});

	onDestroy(() => {
		stopTaskPolling();
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
					<span class="text-gray-700 dark:text-gray-300">{humanizeAgentLabel(agent?.name) || humanizeAgentLabel($page.params.agent_id)}</span>
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
								{humanizeAgentLabel(agent.name) || humanizeAgentLabel(agent.agent_id)}
							</h1>
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

				<div class="rounded-2xl border border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-900">
					<div class="flex items-center justify-between gap-3">
						<div>
							<div class="text-sm font-medium text-gray-900 dark:text-gray-100">Knowledge</div>
							<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								Upload content to be used by this agent as reference knowledge.
							</div>
						</div>
						<div class="flex items-center gap-2">
							<input bind:this={knowledgeFileInput} type="file" multiple class="hidden" on:change={uploadKnowledgeFileHandler} />
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

					<div class="mt-4 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-800 dark:bg-gray-950">
						<div class="flex items-center justify-between gap-2">
							<div class="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-gray-400">
								Knowledge Upload Tasks
							</div>
							<div class="flex items-center gap-2">
								{#if knowledgeTasksLoading}
									<Spinner className="size-3.5" />
								{/if}
								<button
									type="button"
									class="rounded-lg border border-gray-200 px-2 py-1 text-xs text-gray-700 transition hover:bg-white dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-900"
									on:click={refreshKnowledgeTasks}
									disabled={knowledgeTasksLoading}
								>
									Refresh Tasks
								</button>
							</div>
						</div>

						{#if knowledgeTasks.length === 0}
							<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">No active upload tasks.</div>
						{:else}
							<div class="mt-2 space-y-2">
								{#each knowledgeTasks as task (task.task_id)}
									<div class="rounded-lg border border-gray-200 bg-white px-3 py-2 dark:border-gray-800 dark:bg-gray-900">
										<div class="flex flex-wrap items-center justify-between gap-2">
											<div class="min-w-0">
												<div class="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
													{task.filename ?? task.requested_path}
												</div>
											</div>
											<span class={`rounded-full px-2 py-0.5 text-[11px] font-medium ${formatTaskStatusClass(task.status)}`}>
												{formatTaskStatusLabel(task.status)}
											</span>
										</div>
										<div class="mt-1 text-[11px] text-gray-500 dark:text-gray-400">
											Updated: {formatKnowledgeDate(task.updated_at)}
										</div>
										{#if task.error_detail}
											<div class="mt-1 text-xs text-red-700 dark:text-red-300">
												{task.error_detail}
											</div>
										{/if}
									</div>
								{/each}
							</div>
						{/if}
					</div>

					<div
						class={`mt-4 rounded-xl border border-dashed px-4 py-7 text-center transition ${
							isKnowledgeDropActive
								? 'border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/30'
								: 'border-gray-300 bg-gray-50 dark:border-gray-700 dark:bg-gray-950'
						}`}
						role="button"
						tabindex="0"
						on:dragover={onKnowledgeDragOver}
						on:dragenter={onKnowledgeDragOver}
						on:dragleave={onKnowledgeDragLeave}
						on:drop={onKnowledgeDrop}
						on:click={triggerKnowledgeUpload}
						on:keydown={onKnowledgeDropzoneKeydown}
					>
						<div class="mx-auto max-w-xl">
							<div class="text-sm font-semibold text-gray-800 dark:text-gray-100">
								Drop files here or <span class="text-blue-700 dark:text-blue-300">browse</span>
							</div>
							<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								PDF, DOCX, TXT, JSON, CSV, MD supported
							</div>
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
	onSubmit={updateAgentHandler}
/>

<Modal size="lg" bind:show={showKnowledgePreviewModal}>
	<div class="space-y-4">
		<div class="overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
			<div class="border-b border-gray-200 bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-400">
				File
			</div>
				<div class="space-y-2 px-4 py-3">
					<div class="pl-1 text-lg font-semibold text-gray-900 break-words dark:text-gray-100">
						{knowledgePreview?.filename ?? 'Knowledge File'}
					</div>
				</div>
			</div>

		{#if knowledgePreview}
			<div class="overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
				<div class="border-b border-gray-200 bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-400">
					Metadata
				</div>
				<div class="grid gap-3 px-4 py-3 text-sm md:grid-cols-2">
					<div class="rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-950">
						<div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Mime</div>
						<div class="mt-1 text-gray-900 break-all dark:text-gray-100">{knowledgePreview.mime_type}</div>
					</div>
					<div class="rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-950">
						<div class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Size</div>
						<div class="mt-1 text-gray-900 dark:text-gray-100">{formatBytes(knowledgePreview.size_bytes)}</div>
					</div>
				</div>
			</div>
		{/if}

		<div class="overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
			<div class="border-b border-gray-200 bg-gray-50 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-400">
				Preview
			</div>
			<div class="px-4 py-3">
				{#if knowledgePreview && knowledgePreview.content_text !== null}
					<pre class="max-h-[60vh] overflow-auto rounded-xl bg-gray-50 p-4 text-xs leading-5 text-gray-700 dark:bg-gray-950 dark:text-gray-300">{knowledgePreview.content_text}</pre>
				{:else if knowledgePreview}
					<div class="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600 dark:border-gray-800 dark:bg-gray-950 dark:text-gray-300">
						Binary file preview is not available. Use Download instead.
					</div>
				{/if}
			</div>
		</div>
	</div>
</Modal>
