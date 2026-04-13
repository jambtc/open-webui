<script lang="ts">
	import { getContext } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let loading = false;
	export let onSubmit: (payload: { name: string }) => Promise<void> = async () => {};

	let name = '';

	$: if (!show) {
		name = '';
	}

	const submitHandler = async () => {
		await onSubmit({
			name: name.trim()
		});
	};
</script>

<Modal size="sm" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
			<div class="text-lg font-medium self-center">{$i18n.t('Create Agent')}</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<XMark className={'size-5'} />
			</button>
		</div>

		<div class="flex flex-col w-full px-5 pb-4 dark:text-gray-200">
			<form
				class="flex flex-col w-full"
				on:submit|preventDefault={submitHandler}
			>
				<div class="flex flex-col w-full mt-2">
					<div class="mb-1 text-xs text-gray-500">{$i18n.t('Agent Name')}</div>
					<input
						class="w-full text-sm bg-transparent placeholder:text-gray-300 dark:placeholder:text-gray-700 outline-hidden"
						type="text"
						bind:value={name}
						placeholder="assistant"
						autocomplete="off"
						required
					/>
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
							{$i18n.t('Create Agent')}
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
</Modal>
