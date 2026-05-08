<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';

	const i18n = getContext<Writable<i18nType>>('i18n');

	export let size = 'md';
</script>

{#if size === 'md'}
	<span class="inline-flex items-center gap-2 my-2 mx-1">
		<span class="shimmer-text text-sm font-medium">{$i18n.t('BoxedAI is processing your request')}</span>
		<span class="inline-flex items-center gap-1">
			<span class="wave-dot dot-1"></span>
			<span class="wave-dot dot-2"></span>
			<span class="wave-dot dot-3"></span>
		</span>
	</span>
{:else}
	<span
		class="relative flex {size === 'xs' ? 'size-1.5 my-1' : 'size-2 my-1'} mx-1"
	>
		<span
			class="absolute inline-flex h-full w-full animate-pulse rounded-full bg-gray-700 dark:bg-gray-200 opacity-75"
		></span>
		<span
			class="relative inline-flex {size === 'xs' ? 'size-1.5' : 'size-2'} rounded-full bg-black dark:bg-white animate-size"
		></span>
	</span>
{/if}

<style>
	@keyframes size {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.25);
		}
	}

	.animate-size {
		animation: size 1.5s ease-in-out infinite;
	}

	@keyframes shimmer {
		0% {
			background-position: -200% center;
		}
		100% {
			background-position: 200% center;
		}
	}

	.shimmer-text {
		background: linear-gradient(
			90deg,
			#6b7280 0%,
			#6b7280 35%,
			#ffffff 50%,
			#6b7280 65%,
			#6b7280 100%
		);
		background-size: 200% auto;
		background-clip: text;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		animation: shimmer 2.5s linear infinite;
	}

	:global(.dark) .shimmer-text {
		background: linear-gradient(
			90deg,
			#9ca3af 0%,
			#9ca3af 35%,
			#ffffff 50%,
			#9ca3af 65%,
			#9ca3af 100%
		);
		background-size: 200% auto;
		background-clip: text;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		animation: shimmer 2.5s linear infinite;
	}

	@keyframes wave-dot {
		0%, 60%, 100% {
			transform: translateY(0) scale(1);
			opacity: 0.5;
		}
		30% {
			transform: translateY(-6px) scale(1.2);
			opacity: 1;
		}
	}

	.wave-dot {
		display: inline-block;
		width: 6px;
		height: 6px;
		border-radius: 50%;
		animation: wave-dot 1.4s ease-in-out infinite;
	}

	.dot-1 {
		background: #4db8f0;
		animation-delay: 0s;
	}
	.dot-2 {
		background: #1e6fcc;
		animation-delay: 0.15s;
	}
	.dot-3 {
		background: #0d2f7a;
		animation-delay: 0.3s;
	}
</style>
