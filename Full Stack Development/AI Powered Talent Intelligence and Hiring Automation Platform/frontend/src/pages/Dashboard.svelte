<script>
	import { onMount } from 'svelte';
	import {
		createJob,
		deleteJob,
		extractSkills,
		getAuthToken,
		getJobs,
		logout,
		processMultiple,
		updateJob
	} from '../lib/api.js';

	const blankJobForm = {
		title: '',
		location: '',
		description: ''
	};

	let user = { name: 'User', email: 'user@example.com' };
	let jobs = [];
	let jobsLoading = true;
	let jobsError = '';
	let activeSection = 'dashboard';
	let sectionTitle = 'Dashboard';
	let statusText = 'NEURAL CORE ACTIVE';

	let selectedJob = null;
	let jobForm = { ...blankJobForm };
	let editingJobId = null;
	let jobFormError = '';
	let jobFormSaving = false;

	let screenJobDescription = '';
	let skillPreview = [];
	let skillPreviewLoading = false;
	let verificationLoading = false;
	let screenError = '';
	let screenResults = [];
	let screenFiles = [];
	let screenFileInput;

	let deleteConfirmJob = null;

	onMount(async () => {
		if (!getAuthToken()) {
			window.location.href = '/login';
			return;
		}

		const userData = localStorage.getItem('user');
		if (userData) {
			try {
				user = JSON.parse(userData);
			} catch {
				user = { name: 'User', email: 'user@example.com' };
			}
		}

		await loadJobs();
	});

	async function loadJobs() {
		jobsLoading = true;
		jobsError = '';

		try {
			jobs = await getJobs();
		} catch (error) {
			jobsError = error.message || 'Failed to load jobs.';
			if (error.message === 'Not authenticated') {
				window.location.href = '/login';
			}
		} finally {
			jobsLoading = false;
		}
	}

	function setSection(section) {
		activeSection = section;
		selectedJob = null;
		screenResults = [];
		screenFiles = [];
		screenError = '';
		statusText = section === 'billing' ? 'COMING SOON' : 'NEURAL CORE ACTIVE';

		if (section === 'dashboard') {
			sectionTitle = 'Dashboard';
		} else if (section === 'create-job') {
			sectionTitle = editingJobId ? 'Edit Job' : 'Create Job';
		} else if (section === 'billing') {
			sectionTitle = 'Billing';
		}

		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function openDashboard() {
		editingJobId = null;
		jobFormError = '';
		setSection('dashboard');
	}

	function openCreateJob() {
		jobForm = { ...blankJobForm };
		editingJobId = null;
		jobFormError = '';
		setSection('create-job');
	}

	function openEditJob(job) {
		jobForm = {
			title: job.title || '',
			location: job.location || '',
			description: job.description || ''
		};
		editingJobId = job.id;
		jobFormError = '';
		setSection('create-job');
	}

	function openJob(job) {
		selectedJob = job;
		screenJobDescription = job.description || '';
		skillPreview = [];
		screenResults = [];
		screenFiles = [];
		screenError = '';
		activeSection = 'job-view';
		sectionTitle = job.title || 'Job Workspace';
		statusText = 'NEURAL CORE ACTIVE';
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function handleLogout() {
		logout();
		window.location.href = '/login';
	}

	function getJobInitials(job) {
		const source = `${job.title || ''}`.trim();
		const parts = source.split(/\s+/).filter(Boolean);
		if (parts.length === 0) return 'HF';
		if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
		return `${parts[0][0] || 'H'}${parts[1][0] || 'F'}`.toUpperCase();
	}

	function formatDate(dateString) {
		if (!dateString) return 'Unknown';
		return new Date(dateString).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function formatScore(score) {
		const value = Number(score);
		return Number.isFinite(value) ? value.toFixed(0) : '0';
	}

	function updateJobMenu(job, action) {
		if (action === 'edit') {
			openEditJob(job);
			return;
		}

		if (action === 'delete') {
			deleteConfirmJob = job;
		}
	}

	async function handleJobFormSave() {
		jobFormError = '';

		if (!jobForm.title.trim() || !jobForm.location.trim() || !jobForm.description.trim()) {
			jobFormError = 'Title, location, and job description are required.';
			return;
		}

		jobFormSaving = true;

		try {
			const payload = {
				...jobForm,
				company_name: jobForm.title.trim()
			};

			if (editingJobId) {
				await updateJob(editingJobId, payload);
			} else {
				await createJob(payload);
			}

			await loadJobs();
			openDashboard();
		} catch (error) {
			jobFormError = error.message || 'Failed to save the job.';
		} finally {
			jobFormSaving = false;
		}
	}

	async function handleDeleteJob(jobId) {
		try {
			await deleteJob(jobId);
			deleteConfirmJob = null;
			await loadJobs();
			if (selectedJob?.id === jobId) {
				openDashboard();
			}
		} catch (error) {
			jobsError = error.message || 'Failed to delete job.';
		}
	}

	async function handleAnalyzeJob() {
		screenError = '';

		if (!screenJobDescription.trim()) {
			screenError = 'Paste a job description first.';
			return;
		}

		skillPreviewLoading = true;
		try {
			const response = await extractSkills(screenJobDescription);
			skillPreview = response?.extracted_skills || [];
			if (skillPreview.length === 0) {
				screenError = 'No keywords were extracted. Please improve the job description and try again.';
			}
		} catch (error) {
			screenError = error.message || 'Failed to extract skills.';
		} finally {
			skillPreviewLoading = false;
		}
	}

	function selectJobFiles(event) {
		screenFiles = Array.from(event.currentTarget.files || []);
		event.currentTarget.value = '';
	}

	function shouldShowAiVerdict(result) {
		if (!skillPreview.length) return false;
		if (!result) return false;
		if (Number(result.final_score || 0) <= 0) return false;
		const evaluations = result.evaluations || [];
		return evaluations.some((evaluation) => evaluation.status !== 'Missing');
	}

	function getEvidenceLog(result) {
		return result?.evaluations?.find((evaluation) => evaluation.status === 'Verified Professional')?.evidence_chunk || 'No professional evidence found.';
	}

	async function handleEngageVerification() {
		screenError = '';

		if (!screenJobDescription.trim()) {
			screenError = 'Paste a job description first.';
			return;
		}

		if (skillPreview.length === 0) {
			screenError = 'Run phase 1 first and extract keywords before engaging verification.';
			return;
		}

		if (screenFiles.length === 0) {
			screenError = 'Upload one or more resume files first.';
			return;
		}

		statusText = 'RUNNING DEEP VERIFICATION...';
		verificationLoading = true;

		try {
			const response = await processMultiple(screenJobDescription, screenFiles);
			screenResults = response?.top_candidates || [];
			if (screenResults.length === 0) {
				screenError = 'No ranked candidates were returned.';
			}
			statusText = screenResults.length ? 'VERIFICATION COMPLETE' : 'NO CANDIDATES FOUND';
		} catch (error) {
			screenError = error.message || 'Failed to screen resumes.';
			statusText = 'NEURAL CORE ACTIVE';
		} finally {
			verificationLoading = false;
		}
	}
</script>

<div class="app-shell">
	<aside class="sidebar">
		<div class="brand-block">
			<div class="brand-mark">HF</div>
			<div>
				<h1>HireForge Pro</h1>
				<p>AI Talent Workbench</p>
			</div>
		</div>

		<div class="profile-card">
			<div class="profile-avatar">{(user.name || 'U').slice(0, 1).toUpperCase()}</div>
			<div class="profile-meta">
				<div class="profile-name">{user.name || 'User'}</div>
				<div class="profile-email">{user.email || 'user@example.com'}</div>
			</div>
		</div>

		<nav class="nav">
			<button class:active={activeSection === 'dashboard'} type="button" on:click={openDashboard}>
				Dashboard
			</button>
			<button class:active={activeSection === 'create-job'} type="button" on:click={openCreateJob}>
				Create Job
			</button>
			<button class:active={activeSection === 'billing'} type="button" on:click={() => setSection('billing')}>
				Billing
			</button>
		</nav>

		<div class="sidebar-foot">
			<div class="status-badge">{statusText}</div>
			<p>Recruiting workspace with live jobs, edit controls, and resume uploads under each job.</p>
			<button type="button" class="ghost-btn" on:click={handleLogout}>Logout</button>
		</div>
	</aside>

	<main class="main">
		<header class="topbar">
			<div>
				<p class="eyebrow">Profile / Dashboard / Create Job / Billing</p>
				<h2>{sectionTitle}</h2>
			</div>

			<div class="topbar-actions">
				{#if activeSection === 'dashboard'}
					<button class="primary-btn" type="button" on:click={openCreateJob}>Create Job</button>
				{/if}
				<button class="secondary-btn danger" type="button" on:click={handleLogout}>Logout</button>
			</div>
		</header>

		{#if activeSection === 'dashboard'}
			<section class="stats-row">
				<div class="stat-card">
					<span>Total Jobs</span>
					<strong>{jobs.length}</strong>
				</div>
				<div class="stat-card">
					<span>Selected Job</span>
					<strong>{selectedJob ? '1' : '0'}</strong>
				</div>
				<div class="stat-card">
					<span>Status</span>
					<strong>Live</strong>
				</div>
			</section>

			{#if jobsError}
				<div class="alert error">{jobsError}</div>
			{/if}

			<section class="feed">
				{#if jobsLoading}
					<div class="empty-state">Loading jobs...</div>
				{:else if jobs.length === 0}
					<div class="empty-state">
						<h3>No jobs yet</h3>
						<p>Use Create Job to add your first posting.</p>
						<button class="primary-btn" type="button" on:click={openCreateJob}>Create Job</button>
					</div>
				{:else}
					{#each jobs as job}
						<article class="job-card">
							<div class="job-hero">
								<div class="job-thumb">{getJobInitials(job)}</div>

								<div class="job-copy">
									<div class="job-topline">
										<button class="job-title" type="button" on:click={() => openJob(job)}>{job.title}</button>

										<div class="job-menu">
											<details>
												<summary aria-label="Job actions">⋯</summary>
												<div class="menu-popover">
													<button type="button" on:click={() => updateJobMenu(job, 'edit')}>Edit</button>
													<button type="button" class="danger" on:click={() => updateJobMenu(job, 'delete')}>Delete</button>
												</div>
											</details>
										</div>
									</div>
								</div>
							</div>
						</article>
					{/each}
				{/if}
			</section>
		{:else if activeSection === 'create-job'}
			<section class="form-shell">
				<div class="panel">
					<div class="panel-header">
						<p class="eyebrow">Create Job</p>
						<h3>{editingJobId ? 'Edit existing job' : 'Add a new job'}</h3>
						<p class="panel-copy">Title, location, and job description are enough to save the job into the database.</p>
					</div>

					<div class="form-grid">
						<label>
							Job Title
							<input bind:value={jobForm.title} type="text" placeholder="Senior Software Engineer" />
						</label>
						<label>
							Location
							<input bind:value={jobForm.location} type="text" placeholder="New York, NY" />
						</label>
						<label class="wide">
							Job Description
							<textarea bind:value={jobForm.description} placeholder="Paste the job description here..."></textarea>
						</label>
					</div>

					<div class="form-actions">
						<button class="primary-btn" type="button" on:click={handleJobFormSave} disabled={jobFormSaving}>
							{jobFormSaving ? 'Saving...' : 'Save'}
						</button>
					</div>

					{#if jobFormError}
						<div class="alert error">{jobFormError}</div>
					{/if}
				</div>
			</section>
		{:else if activeSection === 'billing'}
			<section class="billing-shell">
				<div class="billing-card">
					<p class="eyebrow">Billing</p>
					<h3>COMING SOON</h3>
					<p>Billing and plan management will be available here in a future update.</p>
				</div>
			</section>
		{:else if activeSection === 'job-view' && selectedJob}
			<section class="job-workspace">
				<div class="hero-panel">
					<div class="hero-left">
						<div class="hero-badge">{getJobInitials(selectedJob)}</div>
						<div>
							<p class="eyebrow">Job Workspace</p>
							<h3>{selectedJob.title}</h3>
							<p class="hero-company">{selectedJob.location || 'No location set'}</p>
						</div>
					</div>
					<div class="hero-actions">
						<button class="secondary-btn" type="button" on:click={openDashboard}>Back to Dashboard</button>
						<div class="job-menu">
							<details>
								<summary aria-label="Job actions">⋯</summary>
								<div class="menu-popover">
									<button type="button" on:click={() => openEditJob(selectedJob)}>Edit</button>
									<button type="button" class="danger" on:click={() => (deleteConfirmJob = selectedJob)}>Delete</button>
								</div>
							</details>
						</div>
					</div>
				</div>

				<div class="workspace-grid">
					<section class="panel">
						<div class="panel-header">
							<p class="eyebrow">Job specification</p>
							<h3>Paste or review the job description</h3>
						</div>

						<div class="field">
							<label for="screen-job-description">Job Requirements & Context</label>
							<textarea
								id="screen-job-description"
								bind:value={screenJobDescription}
								placeholder="Input the job requirements to begin extraction..."
							></textarea>
						</div>

						<div class="button-row">
							<button class="primary-btn outline" type="button" on:click={handleAnalyzeJob} disabled={skillPreviewLoading}>
								{skillPreviewLoading ? 'Extracting...' : 'Phase 1: Neural Skill Extraction'}
							</button>
							<button class="secondary-btn" type="button" on:click={() => (screenFileInput?.click())}>
								Choose Resume Files
							</button>
						</div>

						{#if skillPreview.length > 0}
							<div class="tag-row">
								{#each skillPreview as skill}
									<span class="tag">{skill}</span>
								{/each}
							</div>
						{/if}

						{#if screenError}
							<div class="alert error">{screenError}</div>
						{/if}
					</section>

					<section class="panel">
						<div class="panel-header">
							<p class="eyebrow">Source resumes</p>
							<h3>Upload files</h3>
						</div>

						<div class="upload-zone">
							<div class="upload-icon">+</div>
							<p class="upload-title">Choose resume files</p>
							<p class="upload-subtitle">PDF / DOCX / TXT files are supported</p>
						</div>

						<input
							bind:this={screenFileInput}
							class="file-input"
							type="file"
							multiple
							accept=".pdf,.doc,.docx,.txt"
							on:change={selectJobFiles}
						/>

						<div class="file-list">
							{#if screenFiles.length === 0}
								<p class="file-empty">No resumes selected yet.</p>
							{:else}
								{#each screenFiles as file}
									<div class="file-card">
										<span>{file.name}</span>
									</div>
								{/each}
							{/if}
						</div>

						<div class="button-stack">
							<button class="primary-btn" type="button" on:click={handleEngageVerification} disabled={verificationLoading}>
								{#if verificationLoading}
									<span class="btn-spinner" aria-hidden="true"></span>
									<span>Engaging...</span>
								{:else}
									<span>Engage Verification</span>
								{/if}
							</button>
						</div>
					</section>
				</div>

				<section class="panel results-panel">
					<div class="panel-header">
						<p class="eyebrow">Talent ranking engine</p>
						<h3>Screened candidates</h3>
					</div>

					{#if screenResults.length === 0}
						<div class="empty-state">
							<p>Run screening to view ranked candidates and AI verdicts.</p>
						</div>
					{:else}
						<div class="comment-stream">
							{#each screenResults as result}
								<div class="comment-card">
									<div class="comment-head">
										<div>
											<div class="comment-title">{result.filename}</div>
											<div class="comment-subtitle">Rank #{result.rank || '1'}</div>
										</div>
										<div class="score-box">
											<span>Score</span>
											<strong>{formatScore(result.final_score)}</strong>
										</div>
									</div>

									{#if shouldShowAiVerdict(result)}
										<p class="verdict">{result.ai_verdict || 'AI analysis unavailable.'}</p>
									{:else}
										<p class="verdict muted">No verified evidence found yet. AI verdict suppressed.</p>
									{/if}

									<div class="skill-grid">
										{#each result.evaluations || [] as evaluation}
											<div class={`skill-chip ${evaluation.status === 'Verified Professional' ? 'verified' : evaluation.status === 'Academic/Partial' ? 'partial' : 'missing'}`}>
												<span>{evaluation.skill}</span>
												<small>{evaluation.status}</small>
											</div>
										{/each}
									</div>

									{#if shouldShowAiVerdict(result)}
										<div class="evidence-box">
											<p class="evidence-label">AI Verdict</p>
											<p>{result.ai_verdict || 'AI analysis unavailable.'}</p>
											<p class="evidence-label">System Evidence Log</p>
											<p>"{getEvidenceLog(result)}"</p>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					{/if}
				</section>
			</section>
		{/if}
	</main>
</div>

{#if deleteConfirmJob}
	<div class="modal-overlay">
		<div class="modal-card">
			<h3>Delete job?</h3>
			<p>This will remove the job and all associated candidate records from the database.</p>
			<div class="modal-actions">
				<button class="secondary-btn" type="button" on:click={() => (deleteConfirmJob = null)}>Cancel</button>
				<button class="secondary-btn danger" type="button" on:click={() => handleDeleteJob(deleteConfirmJob.id)}>
					Delete
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	:global(html, body, #app) {
		margin: 0;
		width: 100%;
		min-height: 100%;
	}

	:global(body) {
		background:
			radial-gradient(circle at top left, rgba(0, 242, 255, 0.08), transparent 26%),
			radial-gradient(circle at 80% 0%, rgba(112, 0, 255, 0.12), transparent 22%),
			linear-gradient(180deg, #05070a 0%, #0b1020 100%);
		color: #e2e8f0;
		overflow-x: hidden;
	}

	:global(#app) {
		width: 100vw;
		max-width: none;
		border-inline: none;
	}

	.app-shell {
		min-height: 100vh;
		width: 100%;
		display: grid;
		grid-template-columns: 300px minmax(0, 1fr);
		background:
			linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
			linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
		background-size: 30px 30px, 30px 30px;
	}

	.sidebar {
		padding: 24px;
		display: flex;
		flex-direction: column;
		gap: 20px;
		background: rgba(7, 10, 18, 0.92);
		border-right: 1px solid rgba(255, 255, 255, 0.08);
	}

	.brand-block {
		display: flex;
		align-items: center;
		gap: 14px;
	}

	.brand-mark {
		width: 52px;
		height: 52px;
		display: grid;
		place-items: center;
		border-radius: 16px;
		background: linear-gradient(135deg, #00f2ff, #7000ff);
		color: white;
		font-weight: 800;
		letter-spacing: 0.05em;
	}

	.brand-block h1 {
		margin: 0;
		font-size: 19px;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.brand-block p {
		margin: 4px 0 0;
		color: #94a3b8;
	}

	.profile-card {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 14px;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.profile-avatar {
		width: 44px;
		height: 44px;
		display: grid;
		place-items: center;
		border-radius: 14px;
		background: rgba(0, 242, 255, 0.12);
		color: #00f2ff;
		font-weight: 800;
	}

	.profile-name {
		font-weight: 700;
	}

	.profile-email {
		color: #94a3b8;
		font-size: 13px;
	}

	.nav {
		display: grid;
		gap: 10px;
	}

	.nav button,
	.ghost-btn,
	.primary-btn,
	.secondary-btn {
		border: 1px solid transparent;
		border-radius: 14px;
		padding: 12px 16px;
		font: inherit;
		font-weight: 700;
		cursor: pointer;
	}

	.nav button {
		background: rgba(255, 255, 255, 0.04);
		color: #e2e8f0;
		text-align: left;
		border-color: rgba(255, 255, 255, 0.08);
	}

	.nav button.active {
		background: #0f172a;
		color: white;
	}

	.sidebar-foot {
		margin-top: auto;
		padding: 18px;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.status-badge {
		display: inline-flex;
		padding: 8px 12px;
		border-radius: 999px;
		background: rgba(16, 185, 129, 0.12);
		color: #34d399;
		border: 1px solid rgba(16, 185, 129, 0.22);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 12px;
	}

	.sidebar-foot p {
		margin: 0 0 14px;
		line-height: 1.6;
		color: #cbd5e1;
	}

	.ghost-btn {
		width: 100%;
		background: white;
		color: #0f172a;
	}

	.main {
		padding: 28px;
		min-width: 0;
	}

	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 20px;
		padding: 22px 24px;
		border-radius: 22px;
		background: rgba(15, 17, 23, 0.95);
		border: 1px solid rgba(255, 255, 255, 0.08);
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18);
	}

	.eyebrow {
		margin: 0 0 8px;
		font-size: 12px;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: #00f2ff;
	}

	.topbar h2 {
		margin: 0;
		font-size: 28px;
	}

	.topbar-actions {
		display: flex;
		gap: 10px;
		flex-wrap: wrap;
	}

	.primary-btn {
		background: linear-gradient(135deg, #00f2ff, #7000ff);
		color: white;
	}

	.primary-btn:disabled {
		opacity: 0.9;
		cursor: wait;
	}

	.primary-btn.outline {
		background: transparent;
		border-color: rgba(0, 242, 255, 0.45);
		color: #00f2ff;
	}

	.secondary-btn {
		background: rgba(255, 255, 255, 0.04);
		border-color: rgba(255, 255, 255, 0.08);
		color: #cbd5e1;
	}

	.secondary-btn.danger {
		color: #fca5a5;
	}

	.stats-row {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 16px;
		margin: 20px 0;
	}

	.stat-card {
		padding: 18px;
		border-radius: 20px;
		background: rgba(15, 17, 23, 0.95);
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.stat-card span {
		display: block;
		margin-bottom: 8px;
		font-size: 13px;
		color: #94a3b8;
	}

	.stat-card strong {
		font-size: 30px;
	}

	.feed {
		display: grid;
		gap: 20px;
		margin-top: 10px;
	}

	.job-card,
	.panel,
	.billing-card,
	.empty-state,
	.modal-card {
		background: rgba(15, 17, 23, 0.95);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 24px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18);
	}

	.job-card {
		padding: 18px;
	}

	.job-hero {
		display: grid;
		grid-template-columns: 120px 1fr;
		gap: 18px;
		align-items: start;
	}

	.job-thumb {
		min-height: 150px;
		border-radius: 18px;
		display: grid;
		place-items: center;
		background:
			radial-gradient(circle at 30% 30%, rgba(0, 242, 255, 0.18), transparent 40%),
			linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(112, 0, 255, 0.75));
		font-size: 32px;
		font-weight: 800;
		letter-spacing: 0.08em;
		color: white;
	}

	.job-copy {
		display: grid;
		gap: 14px;
	}

	.job-topline {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
	}

	.job-title {
		border: none;
		padding: 0;
		background: transparent;
		color: #fff;
		font: inherit;
		font-size: 24px;
		line-height: 1.2;
		font-weight: 800;
		cursor: pointer;
		text-align: left;
	}

	.job-title:hover {
		color: #00f2ff;
	}

	.job-menu {
		position: relative;
	}

	.job-menu details {
		position: relative;
	}

	.job-menu summary {
		list-style: none;
		cursor: pointer;
		padding: 6px 10px;
		border-radius: 12px;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		font-size: 22px;
		line-height: 1;
		color: #cbd5e1;
	}

	.job-menu summary::-webkit-details-marker {
		display: none;
	}

	.menu-popover {
		position: absolute;
		top: calc(100% + 8px);
		right: 0;
		display: grid;
		min-width: 120px;
		padding: 8px;
		border-radius: 14px;
		background: #10131a;
		border: 1px solid rgba(255, 255, 255, 0.08);
		box-shadow: 0 16px 32px rgba(0, 0, 0, 0.32);
		z-index: 10;
	}

	.menu-popover button {
		border: none;
		background: transparent;
		color: #e2e8f0;
		text-align: left;
		padding: 10px 12px;
		border-radius: 10px;
		cursor: pointer;
		font: inherit;
	}

	.menu-popover button:hover {
		background: rgba(255, 255, 255, 0.06);
	}

	.menu-popover button.danger {
		color: #fca5a5;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.chips span {
		padding: 7px 10px;
		border-radius: 999px;
		font-size: 12px;
		color: #cbd5e1;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.form-shell,
	.billing-shell,
	.job-workspace {
		margin-top: 20px;
	}

	.panel {
		padding: 24px;
	}

	.panel-header h3,
	.billing-card h3,
	.empty-state h3 {
		margin: 0;
		font-size: 24px;
	}

	.panel-copy {
		margin: 10px 0 0;
		color: #94a3b8;
		line-height: 1.7;
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 16px;
	}

	.form-grid label {
		display: grid;
		gap: 8px;
		font-size: 13px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #cbd5e1;
	}

	.form-grid label.wide {
		grid-column: 1 / -1;
	}

	.form-grid input,
	.form-grid textarea,
	.field textarea,
	.file-input {
		width: 100%;
		padding: 12px 14px;
		border-radius: 14px;
		border: 1px solid rgba(255, 255, 255, 0.08);
		background: #090b0f;
		color: #e2e8f0;
		font: inherit;
		box-sizing: border-box;
	}

	.form-grid textarea,
	.field textarea {
		min-height: 220px;
		resize: vertical;
		line-height: 1.6;
	}

	.form-actions,
	.button-row,
	.button-stack {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
		margin-top: 18px;
	}

	.alert {
		margin-top: 14px;
		padding: 12px 14px;
		border-radius: 12px;
		font-weight: 600;
	}

	.alert.error {
		color: #fecaca;
		background: rgba(239, 68, 68, 0.12);
		border: 1px solid rgba(239, 68, 68, 0.22);
	}

	.tag-row {
		display: flex;
		flex-wrap: wrap;
		gap: 10px;
		margin-top: 18px;
	}

	.tag {
		padding: 8px 12px;
		border-radius: 999px;
		background: rgba(112, 0, 255, 0.12);
		border: 1px solid rgba(112, 0, 255, 0.28);
		color: #e2e8f0;
		font-size: 13px;
		font-weight: 600;
	}

	.billing-card {
		padding: 42px 28px;
		text-align: center;
	}

	.billing-card p {
		margin: 12px auto 0;
		max-width: 540px;
		color: #94a3b8;
		line-height: 1.8;
	}

	.job-workspace {
		display: grid;
		gap: 20px;
	}

	.hero-panel {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 18px;
		padding: 24px;
		border-radius: 24px;
		background: rgba(15, 17, 23, 0.95);
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.hero-left {
		display: flex;
		align-items: center;
		gap: 16px;
	}

	.hero-badge {
		width: 74px;
		height: 74px;
		display: grid;
		place-items: center;
		border-radius: 18px;
		background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(112, 0, 255, 0.8));
		color: white;
		font-size: 28px;
		font-weight: 800;
	}

	.hero-panel h3 {
		margin: 0;
		font-size: 28px;
	}

	.hero-company {
		margin: 8px 0 0;
		color: #94a3b8;
	}

	.hero-actions {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
	}

	.workspace-grid {
		display: grid;
		grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.9fr);
		gap: 20px;
		align-items: start;
	}

	.field {
		display: grid;
		gap: 10px;
	}

	.field label {
		font-size: 13px;
		font-weight: 700;
		color: #cbd5e1;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.upload-zone {
		border: 1px dashed rgba(0, 242, 255, 0.35);
		background: #090b0f;
		border-radius: 18px;
		padding: 20px;
		text-align: center;
		display: grid;
		gap: 8px;
	}

	.upload-icon {
		width: 46px;
		height: 46px;
		border-radius: 14px;
		margin: 0 auto 6px;
		display: grid;
		place-items: center;
		background: rgba(0, 242, 255, 0.12);
		color: #00f2ff;
		font-size: 28px;
		line-height: 1;
	}

	.upload-title {
		font-weight: 700;
		color: #e2e8f0;
	}

	.btn-spinner {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		border: 2px solid rgba(255, 255, 255, 0.35);
		border-top-color: white;
		display: inline-block;
		animation: spin 0.8s linear infinite;
	}

	.upload-subtitle {
		color: #94a3b8;
		font-size: 13px;
	}

	.file-list {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin: 14px 0 0;
	}

	.file-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 12px 14px;
		border-radius: 12px;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		color: #e2e8f0;
		font-size: 13px;
	}

	.file-empty {
		color: #94a3b8;
		font-size: 14px;
	}

	.comment-stream {
		display: grid;
		gap: 14px;
	}

	.comment-card {
		padding: 16px;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.06);
	}

	.comment-head {
		display: flex;
		align-items: start;
		justify-content: space-between;
		gap: 12px;
	}

	.comment-title {
		font-weight: 700;
	}

	.comment-subtitle {
		margin-top: 4px;
		color: #94a3b8;
		font-size: 13px;
	}

	.score-box {
		text-align: right;
	}

	.score-box span {
		display: block;
		margin-bottom: 4px;
		color: #94a3b8;
		font-size: 11px;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.12em;
	}

	.score-box strong {
		font-size: 34px;
		line-height: 1;
		color: #00f2ff;
	}

	.verdict {
		margin: 12px 0 0;
		color: #cbd5e1;
		line-height: 1.7;
	}

	.verdict.muted {
		color: #94a3b8;
		font-style: italic;
	}

	.evidence-box {
		margin-top: 14px;
		padding: 14px;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid rgba(255, 255, 255, 0.06);
	}

	.evidence-label {
		margin: 0 0 6px;
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: #00f2ff;
	}

	.evidence-box p {
		margin: 0 0 10px;
		color: #cbd5e1;
		line-height: 1.7;
	}

	.evidence-box p:last-child {
		margin-bottom: 0;
	}

	.skill-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
		gap: 10px;
		margin-top: 14px;
	}

	.skill-chip {
		padding: 10px 12px;
		border-radius: 12px;
		font-size: 12px;
		font-weight: 700;
		display: grid;
		gap: 4px;
	}

	.skill-chip small {
		opacity: 0.8;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	.skill-chip.verified {
		background: rgba(16, 185, 129, 0.08);
		border: 1px solid rgba(16, 185, 129, 0.35);
		color: #34d399;
	}

	.skill-chip.partial {
		background: rgba(245, 158, 11, 0.08);
		border: 1px solid rgba(245, 158, 11, 0.35);
		color: #fbbf24;
	}

	.skill-chip.missing {
		background: rgba(239, 68, 68, 0.08);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: #fca5a5;
	}

	.empty-state {
		padding: 44px 24px;
		text-align: center;
	}

	.empty-state p {
		margin: 10px 0 0;
		color: #94a3b8;
	}

	.modal-overlay {
		position: fixed;
		inset: 0;
		z-index: 1000;
		display: grid;
		place-items: center;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(8px);
		padding: 20px;
	}

	.modal-card {
		width: min(520px, 100%);
		padding: 24px;
		text-align: center;
		background: rgba(15, 17, 23, 0.98);
		border-radius: 24px;
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.modal-card p {
		margin: 12px 0 0;
		color: #94a3b8;
		line-height: 1.7;
	}

	.modal-actions {
		display: flex;
		justify-content: center;
		gap: 12px;
		flex-wrap: wrap;
		margin-top: 20px;
	}

	@media (max-width: 1100px) {
		.app-shell {
			grid-template-columns: 1fr;
		}

		.sidebar {
			border-right: none;
			border-bottom: 1px solid rgba(255, 255, 255, 0.08);
		}

		.stats-row {
			grid-template-columns: 1fr;
		}

		.job-hero,
		.workspace-grid,
		.hero-panel {
			grid-template-columns: 1fr;
			display: grid;
		}
	}

	@media (max-width: 720px) {
		.main {
			padding: 16px;
		}

		.topbar {
			flex-direction: column;
			align-items: start;
		}

		.form-grid {
			grid-template-columns: 1fr;
		}

		.job-topline,
		.comment-head,
		.resume-panel-head {
			flex-direction: column;
		}

		.score-box {
			text-align: left;
		}
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
