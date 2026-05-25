/**
 * Simple client-side router for Svelte
 */

export let navigate;
export let currentRoute;

/**
 * Initialize the router
 */
export function initRouter(setNavigate, setRoute) {
	navigate = setNavigate;
	currentRoute = setRoute;
}

/**
 * Navigate to a new route
 */
export function navigateTo(path) {
	window.history.pushState({}, '', path);
	updateRoute();
}

/**
 * Update the current route
 */
function updateRoute() {
	const path = window.location.pathname;
	currentRoute = path;

	// Dispatch event for components to listen
	window.dispatchEvent(new CustomEvent('routeChange', { detail: { path } }));
}

/**
 * Router component
 */
export const Router = {
	onMount: (callback) => {
		window.addEventListener('routeChange', callback);
		return () => {
			window.removeEventListener('routeChange', callback);
		};
	}
};

// Initialize on load
window.addEventListener('popstate', updateRoute);
updateRoute();
