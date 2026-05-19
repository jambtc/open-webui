<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	import { mapChatError } from '$lib/utils/chatErrors';

	const i18n = getContext<Writable<i18nType>>('i18n');

	export let content: unknown = '';

	$: mapped = mapChatError(content);
</script>

<div class="my-2 text-gray-800 dark:text-gray-100">
	<div class="font-medium mb-1">
		{$i18n.t(mapped.titleKey)}
	</div>
	<div class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
		{$i18n.t(mapped.bodyKey)}
	</div>
</div>
