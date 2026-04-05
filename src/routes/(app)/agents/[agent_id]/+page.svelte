<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';

	import { getAgentById, type AgentDetailResponse } from '$lib/apis/agents';
	import { mobile, showArchivedChats, showSidebar, user } from '$lib/stores';

	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Sidebar from '$lib/components/icons/Sidebar.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	const i18n = getContext('i18n');

	let loaded = false;
	let errorMessage = '';
	let agent: AgentDetailResponse | null = null;

	onMount(async () => {
		try {
			agent = await getAgentById(localStorage.token, $page.params.agent_id);
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
						{#if agent.is_default}
							<span class="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-200">
								Default
							</span>
						{/if}
					</div>
				</div>

				<div class="grid gap-4 md:grid-cols-2">
					<div class="rounded-2xl border border-gray-200 bg-white px-5 py-4 dark:border-gray-800 dark:bg-gray-900">
						<div class="text-sm font-medium text-gray-900 dark:text-gray-100">Summary</div>
						<dl class="mt-3 space-y-2 text-sm">
							<div>
								<dt class="text-gray-500 dark:text-gray-400">Workspace</dt>
								<dd class="text-gray-900 dark:text-gray-100">{agent.workspace ?? 'n/a'}</dd>
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
