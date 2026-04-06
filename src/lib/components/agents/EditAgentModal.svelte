<script lang="ts">
	import { getContext } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let loading = false;
	export let initialName = '';
	export let initialWorkspace = '';
	export let initialModel = '';
	export let initialAvatar = '';
	export let onSubmit: (payload: { name?: string; workspace?: string; model?: string; avatar?: string }) => Promise<void> = async () => {};

	let name = '';
	let workspace = '';
	let model = '';
	let avatar = '';
	let showWorkspaceError = false;

	$: if (show) {
		name = initialName;
		workspace = initialWorkspace;
		model = initialModel;
		avatar = initialAvatar;
		showWorkspaceError = false;
	}

	const submitHandler = async () => {
		showWorkspaceError = !workspace.trim();
		if (showWorkspaceError) return;

		const payload: { name?: string; workspace?: string; model?: string; avatar?: string } = {};

		if (name.trim()) payload.name = name.trim();
		if (workspace.trim()) payload.workspace = workspace.trim();
		if (model.trim()) payload.model = model.trim();
		if (avatar.trim()) payload.avatar = avatar.trim();

		await onSubmit(payload);
	};
</script>

<Modal size="sm" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class="text-lg font-medium self-center">{$i18n.t('Edit Agent')}</div>
			<button class="self-center" on:click={() => { show = false; }}>
				<XMark className={'size-5'} />
			</button>
		</div>

		<div class="flex flex-col w-full px-5 pb-4 dark:text-gray-200">
			<form class="flex flex-col w-full" on:submit|preventDefault={submitHandler}>
				<div class="flex flex-col w-full mt-2">
					<div class="mb-1 text-xs text-gray-500">{$i18n.t('Agent Name')}</div>
					<input class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden" type="text" bind:value={name} autocomplete="off" required />
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-1 text-xs text-gray-500">{$i18n.t('Workspace')}</div>
					<input class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden" type="text" bind:value={workspace} autocomplete="off" placeholder="/workspace/..." on:input={() => { if (workspace.trim()) showWorkspaceError = false; }} required />
					<div class="mt-1 text-xs text-gray-500">La workspace deve stare sotto <code>/workspace</code>.</div>
					{#if showWorkspaceError}
						<div class="mt-1 text-xs text-red-600 dark:text-red-400">Workspace is required.</div>
					{/if}
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-1 text-xs text-gray-500">{$i18n.t('Model')}</div>
					<input class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden" type="text" bind:value={model} autocomplete="off" placeholder="optional" />
				</div>

				<div class="flex flex-col w-full mt-3">
					<div class="mb-1 text-xs text-gray-500">{$i18n.t('Avatar URL')}</div>
					<input class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden" type="text" bind:value={avatar} autocomplete="off" placeholder="optional" />
				</div>

				<div class="flex justify-end mt-5">
					<button
						type="submit"
						class="min-w-28 rounded-xl bg-black px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-black"
						disabled={loading || !name.trim()}
					>
						{#if loading}
							<Spinner className="size-4" />
						{:else}
							{$i18n.t('Save')}
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
</Modal>
