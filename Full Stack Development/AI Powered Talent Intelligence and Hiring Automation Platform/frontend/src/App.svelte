	<script>
		import { onMount } from 'svelte';
		import Login from './pages/Login.svelte';
		import Dashboard from './pages/Dashboard.svelte';

	function resolveViewFromPath(path) {
		try {
			const token = localStorage.getItem('auth_token');
			const hasProfile = !!localStorage.getItem('user');

			if (!token || !hasProfile) {
				return 'login';
			}

			if (path === '/login') {
				return 'login';
			}

			if (path === '/dashboard' || path === '/' || path.startsWith('/jobs/') || path.startsWith('/billing')) {
				return 'dashboard';
			}

			return 'dashboard';
		} catch {
			return 'login';
		}
	}

	// State
	let view = resolveViewFromPath(window.location.pathname);

	// Check auth status on mount
	onMount(() => {
		view = resolveViewFromPath(window.location.pathname);

		// Listen for route changes
		window.addEventListener('routeChange', handleRouteChange);
		return () => {
			window.removeEventListener('routeChange', handleRouteChange);
		};
	});

	function handleRouteChange(event) {
		const path = event.detail.path;
		view = resolveViewFromPath(path);
	}

</script>

{#if view === 'login'}
	<Login />
{:else if view === 'dashboard'}
	<Dashboard />
{/if}
