<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import {
		getAgentById,
		updateAgent,
		deleteAgent,
		type AgentDetailResponse,
		type UpdateAgentPayload
	} from '$lib/apis/agents';
	import { mobile, showArchivedChats, showSidebar, user } from '$lib/stores';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import EditAgentModal from '$lib/components/agents/EditAgentModal.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');

	let loaded = false;
	let errorMessage = '';
	let agent: AgentDetailResponse | null = null;
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
