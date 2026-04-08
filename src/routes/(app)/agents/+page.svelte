<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { toast } from 'svelte-sonner';
	import { createAgent, getAgentById, getAgents, type AgentItem, type CreateAgentPayload } from '$lib/apis/agents';
	import { mobile, showArchivedChats, showSidebar, user } from '$lib/stores';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import CreateAgentModal from '$lib/components/agents/CreateAgentModal.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');

	let loaded = false;
	let errorMessage = '';
	let agents: AgentItem[] = [];
	let defaultAgentId: string | null = null;
	let showCreateAgentModal = false;
	let createLoading = false;
	let refreshing = false;

	const loadAgents = async () => {
		const res = await getAgents(localStorage.token);
		agents = res?.items ?? [];
		defaultAgentId = res?.default_agent_id ?? null;
	};

	const refreshAgents = async () => {
		refreshing = true;
		errorMessage = '';
		try {
			await loadAgents();
		} catch (error) {
			errorMessage = `${error}`;
		} finally {
			loaded = true;
			refreshing = false;
		}
	};

	const waitForAgentDetail = async (agentId: string, attempts: number = 10, delayMs: number = 250) => {
		for (let attempt = 0; attempt < attempts; attempt += 1) {
			try {
				await getAgentById(localStorage.token, agentId);
				return true;
			} catch (error) {
				if (`${error}`.includes('not found') && attempt < attempts - 1) {
					await new Promise((resolve) => setTimeout(resolve, delayMs));
					continue;
				}
				throw error;
			}
		}

		return false;
	};

	const createAgentHandler = async (payload: CreateAgentPayload) => {
		createLoading = true;
		try {
			const res = await createAgent(localStorage.token, payload);
			toast.success('Agent created successfully');
			showCreateAgentModal = false;
			await loadAgents();
			if (res?.agent_id) {
				await waitForAgentDetail(res.agent_id);
				goto(`/agents/${res.agent_id}`);
			}
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			createLoading = false;
		}
	};

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
			return;
		}
		await refreshAgents();
	});

	afterNavigate(async () => {
		if ($user?.role !== 'admin') {
			return;
		}
		if ($page.url.pathname === '/agents' && !refreshing) {
			await refreshAgents();
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
				<div>
					<div class="flex gap-1 scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium bg-transparent py-1 touch-auto pointer-events-auto">
						<a class="min-w-fit transition" href="/agents">{$i18n.t('Agents')}</a>
					</div>
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
		{:else}
			<div class="mx-auto w-full max-w-4xl space-y-4">
				<div class="flex items-start justify-between gap-4">
					<div>
						<h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">{$i18n.t('Agents')}</h1>
						<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
							Lista agenti esposta dal backend tramite gateway.
						</p>
					</div>
					<button
						type="button"
						class="rounded-xl bg-black px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 dark:bg-white dark:text-black"
						on:click={() => {
							showCreateAgentModal = true;
						}}
					>
						{$i18n.t('Create Agent')}
					</button>
				</div>

				<div class="grid gap-3">
					{#each agents as agent (`${agent.agent_id}`)}
						<button
							type="button"
							class="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-left hover:bg-gray-50 dark:border-gray-800 dark:bg-gray-900 dark:hover:bg-gray-850 transition"
							on:click={() => goto(`/agents/${agent.agent_id}`)}
						>
							<div class="flex items-start justify-between gap-3">
								<div>
									<div class="text-sm font-medium text-gray-900 dark:text-gray-100">
										{agent.name ?? agent.agent_id}
									</div>
									<div class="mt-1 font-mono text-xs text-gray-500 dark:text-gray-400">
										{agent.agent_id}
									</div>
								</div>

								{#if agent.is_default || agent.agent_id === defaultAgentId}
									<span class="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-200">
										Default
									</span>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<CreateAgentModal bind:show={showCreateAgentModal} loading={createLoading} onSubmit={createAgentHandler} />
