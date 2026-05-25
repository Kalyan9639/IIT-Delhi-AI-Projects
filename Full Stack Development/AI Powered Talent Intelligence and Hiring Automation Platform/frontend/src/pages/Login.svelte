<script>
	import { googleLogin, getAuthToken, GOOGLE_CLIENT_ID } from '../lib/api.js';
	import { onMount } from 'svelte';

	let isLoading = false;
	let error = null;
	let googleButtonHost;
	let gisScriptLoaded = false;

	function loadGoogleScript() {
		return new Promise((resolve, reject) => {
			if (window.google?.accounts?.id) {
				resolve();
				return;
			}

			const existingScript = document.querySelector('script[data-google-gis="true"]');
			if (existingScript) {
				existingScript.addEventListener('load', () => resolve(), { once: true });
				existingScript.addEventListener('error', () => reject(new Error('Failed to load Google sign-in')), {
					once: true
				});
				return;
			}

			const script = document.createElement('script');
			script.src = 'https://accounts.google.com/gsi/client';
			script.async = true;
			script.defer = true;
			script.dataset.googleGis = 'true';
			script.onload = () => resolve();
			script.onerror = () => reject(new Error('Failed to load Google sign-in'));
			document.head.appendChild(script);
		});
	}

	function renderGoogleButton() {
		if (!GOOGLE_CLIENT_ID) {
			error = 'Missing VITE_GOOGLE_CLIENT_ID in the frontend environment.';
			return;
		}

		if (!googleButtonHost || !window.google?.accounts?.id) {
			return;
		}

		window.google.accounts.id.initialize({
			client_id: GOOGLE_CLIENT_ID,
			callback: handleCredentialResponse,
			auto_select: false,
			cancel_on_tap_outside: true
		});

		googleButtonHost.innerHTML = '';
		window.google.accounts.id.renderButton(googleButtonHost, {
			theme: 'outline',
			size: 'large',
			shape: 'rectangular',
			width: 320,
			text: 'signin_with'
		});
		gisScriptLoaded = true;
	}

	async function handleCredentialResponse(response) {
		isLoading = true;
		error = null;

		try {
			await googleLogin(response.credential);
			window.location.href = '/dashboard';
		} catch (err) {
			error = err.message || 'Google sign-in failed';
		} finally {
			isLoading = false;
		}
	}

	onMount(async () => {
		const token = getAuthToken();
		const userData = localStorage.getItem('user');
		if (token && userData) {
			window.location.href = '/dashboard';
			return;
		}

		try {
			await loadGoogleScript();
			renderGoogleButton();
		} catch (err) {
			error = err.message || 'Unable to load Google sign-in';
		}
	});
</script>

<div class="login-page">
	<div class="login-container">
		<div class="login-header">
			<h1>HireForge Pro</h1>
			<p class="subtitle">AI-Powered Talent Intelligence</p>
		</div>

		<div class="login-content">
			<div class="login-box">
				<h2>Sign in to continue</h2>
				<p class="login-description">
					Welcome to HireForge Pro. Sign in with your Google account to access the
					advanced resume screening platform.
				</p>

				<div class="login-form">
					{#if error}
						<div class="error-message">{error}</div>
					{/if}

					<div class="google-button-shell">
						<div bind:this={googleButtonHost} class="google-button-host" aria-busy={isLoading}></div>
						{#if isLoading && !gisScriptLoaded}
							<div class="button-loading">
								<span class="spinner"></span>
								<span>Loading sign-in...</span>
							</div>
						{/if}
					</div>
				</div>

				<div class="terms">
					<p>
						By signing in, you agree to our <a href="/">Terms of Service</a> and
						<a href="/"> Privacy Policy</a>.
					</p>
				</div>
			</div>
		</div>

		<div class="login-footer">
			<p>© 2026 HireForge Pro. All rights reserved.</p>
		</div>
	</div>
</div>

<style>
	.login-page {
		min-height: 100vh;
		display: flex;
		justify-content: center;
		align-items: center;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	}

	.login-container {
		width: 100%;
		max-width: 480px;
		background: white;
		border-radius: 24px;
		box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
		overflow: hidden;
	}

	.login-header {
		text-align: center;
		padding: 40px 24px 24px;
	}

	.login-header h1 {
		font-size: 32px;
		font-weight: 800;
		color: #1a1a2e;
		margin: 0 0 8px;
	}

	.subtitle {
		font-size: 16px;
		color: #6b7280;
		margin: 0;
	}

	.login-content {
		padding: 24px;
	}

	.login-box {
		text-align: center;
	}

	.login-box h2 {
		font-size: 24px;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 12px;
	}

	.login-description {
		font-size: 15px;
		color: #6b7280;
		line-height: 1.6;
		margin: 0 0 32px;
	}

	.login-form {
		display: flex;
		justify-content: center;
		flex-direction: column;
		align-items: center;
		gap: 12px;
	}

	.google-button-shell {
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
	}

	.google-button-host {
		min-height: 44px;
		display: flex;
		justify-content: center;
	}

	.button-loading {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 14px;
		color: #6b7280;
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid #f3f3f3;
		border-top: 2px solid #667eea;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	.terms {
		margin-top: 24px;
	}

	.terms p {
		font-size: 13px;
		color: #6b7280;
		line-height: 1.6;
	}

	.terms a {
		color: #667eea;
		text-decoration: none;
	}

	.terms a:hover {
		text-decoration: underline;
	}

	.login-footer {
		text-align: center;
		padding: 16px 24px;
		background: #f9fafb;
	}

	.login-footer p {
		font-size: 13px;
		color: #6b7280;
		margin: 0;
	}

	/* Error message */
	.error-message {
		background: #fee2e2;
		color: #dc2626;
		padding: 12px;
		border-radius: 8px;
		margin-bottom: 16px;
		font-size: 14px;
		text-align: left;
	}
</style>
