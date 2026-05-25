<script>
	import { onMount } from 'svelte';
	import { extractSkills, getAuthToken, logout, processMultiple } from '../lib/api.js';

	let jobDescription = '';
	let extractedSkills = [];
	let files = [];
	let candidates = [];

	let isExtracting = false;
	let isUploading = false;
	let error = '';
	let statusText = 'NEURAL CORE ACTIVE';
	let uploadInput;

	onMount(() => {
		if (!getAuthToken()) {
			window.location.href = '/login';
		}
	});

	function openFilePicker() {
		uploadInput?.click();
	}

	function handleFilesChange(event) {
		const selectedFiles = Array.from(event.currentTarget.files || []);
		if (selectedFiles.length === 0) return;

		const lookup = new Map(files.map((file) => [`${file.name}_${file.size}_${file.lastModified}`, file]));
		selectedFiles.forEach((file) => {
			lookup.set(`${file.name}_${file.size}_${file.lastModified}`, file);
		});
		files = Array.from(lookup.values());
		event.currentTarget.value = '';
	}

	function removeFile(index) {
		files = files.filter((_, fileIndex) => fileIndex !== index);
	}

	async function handleExtractSkills() {
		error = '';
		if (!jobDescription.trim()) {
			error = 'Add a role brief before extracting skills.';
			return;
		}

		isExtracting = true;
		statusText = 'EXTRACTING MUST-HAVES...';
		try {
			const response = await extractSkills(jobDescription);
			extractedSkills = response?.extracted_skills || [];
			statusText = extractedSkills.length ? 'SKILL MAP READY' : 'NO SKILLS IDENTIFIED';
		} catch (err) {
			error = err.message || 'Failed to extract skills.';
			statusText = 'NEURAL CORE ACTIVE';
		} finally {
			isExtracting = false;
		}
	}

	async function handleUpload() {
		error = '';

		if (!jobDescription.trim()) {
			error = 'Add a role brief before uploading resumes.';
			return;
		}

		if (files.length === 0) {
			error = 'Choose one or more resume files first.';
			return;
		}

		isUploading = true;
		statusText = 'RUNNING DEEP VERIFICATION...';

		try {
			const response = await processMultiple(jobDescription, files);
			candidates = response?.top_candidates || [];
			statusText = candidates.length ? 'VERIFICATION COMPLETE' : 'NO CANDIDATES FOUND';
		} catch (err) {
			error = err.message || 'Failed to upload resumes.';
			statusText = 'NEURAL CORE ACTIVE';
		} finally {
			isUploading = false;
		}
	}

	function formatScore(score) {
		const value = Number(score);
		return Number.isFinite(value) ? value.toFixed(0) : '0';
	}

	function getStatusClass(status) {
		if (status === 'Verified Professional') return 'verified';
		if (status === 'Academic/Partial') return 'partial';
		return 'missing';
	}

	function handleLogout() {
		logout();
		window.location.href = '/login';
	}
</script>

<div class="candidate-page">
	<aside class="sidebar">
		<div class="brand">
			<div class="brand-mark">HF</div>
			<div>
				<h1>HireForge Pro</h1>
				<p>Candidate Review</p>
			</div>
		</div>

		<nav class="nav">
			<a href="/dashboard" class="nav-link">Dashboard</a>
			<a href="/candidates" class="nav-link active">Candidates</a>
		</nav>

		<div class="sidebar-footer">
			<div class="status-badge">{statusText}</div>
			<p>Upload every resume file together, then review the AI-ranked results in one pass.</p>
			<button class="ghost-btn" type="button" on:click={handleLogout}>Logout</button>
		</div>
	</aside>

	<main class="content">
		<section class="hero">
			<div>
				<p class="eyebrow">Candidate workflow</p>
				<h2>Resume intake and ranking</h2>
				<p class="hero-copy">
					Paste the job requirements, extract must-have skills, then upload all resume files to run the screening pipeline.
				</p>
			</div>

			<div class="hero-actions">
				<div class="hero-pill">PDF / DOCX / TXT</div>
				<div class="hero-pill accent">Multi-file upload</div>
			</div>
		</section>

		<section class="stats">
			<div class="stat-card">
				<span>Selected files</span>
				<strong>{files.length}</strong>
			</div>
			<div class="stat-card">
				<span>Extracted skills</span>
				<strong>{extractedSkills.length}</strong>
			</div>
			<div class="stat-card">
				<span>Ranked candidates</span>
				<strong>{candidates.length}</strong>
			</div>
		</section>

		<section class="panel-grid">
			<div class="panel">
				<div class="panel-header">
					<div>
						<p class="eyebrow">Role brief</p>
						<h3>Job context</h3>
					</div>
				</div>

				<div class="field">
					<label for="candidate-job-description">Job Requirements & Context</label>
					<textarea
						id="candidate-job-description"
						bind:value={jobDescription}
						placeholder="Input the job requirements to begin extraction..."
					></textarea>
				</div>

				<div class="button-row">
					<button class="primary-btn outline" type="button" on:click={handleExtractSkills} disabled={isExtracting}>
						{isExtracting ? 'Extracting...' : 'Phase 1: Neural Skill Extraction'}
					</button>
					<button class="secondary-btn" type="button" on:click={openFilePicker}>Add Resume Files</button>
				</div>

				{#if error}
					<div class="alert error">{error}</div>
				{/if}

				{#if extractedSkills.length > 0}
					<div class="tag-row">
						{#each extractedSkills as skill}
							<span class="tag">{skill}</span>
						{/each}
					</div>
				{/if}
			</div>

			<div class="panel">
				<div class="panel-header">
					<div>
						<p class="eyebrow">Source resumes</p>
						<h3>Upload all files</h3>
					</div>
				</div>

				<button class="upload-zone" type="button" on:click={openFilePicker}>
					<div class="upload-icon">+</div>
					<p class="upload-title">Click to select resume files</p>
					<p class="upload-subtitle">The backend processes every selected file in one request.</p>
				</button>

				<input
					bind:this={uploadInput}
					class="file-input"
					type="file"
					multiple
					accept=".pdf,.doc,.docx,.txt"
					on:change={handleFilesChange}
				/>

				<div class="file-list">
					{#if files.length === 0}
						<p class="empty-copy">No files selected yet.</p>
					{:else}
						{#each files as file, index}
							<div class="file-card">
								<span>{file.name}</span>
								<button type="button" on:click={() => removeFile(index)}>Remove</button>
							</div>
						{/each}
					{/if}
				</div>

				<div class="button-row">
					<button class="primary-btn" type="button" on:click={handleUpload} disabled={isUploading}>
						{isUploading ? 'Uploading...' : 'Upload Resumes'}
					</button>
					<button class="secondary-btn" type="button" on:click={openFilePicker}>Add More Files</button>
				</div>
			</div>
		</section>

		<section class="results-panel">
			<div class="panel-header">
				<div>
					<p class="eyebrow">Talent ranking engine</p>
					<h3>Results</h3>
				</div>
			</div>

			{#if candidates.length === 0}
				<div class="empty-state">
					<p>Upload resumes to generate ranked candidate cards.</p>
				</div>
			{:else}
				<div class="candidate-list">
					{#each candidates as candidate}
						<article class="candidate-card">
							<div class="candidate-top">
								<div class="rank-badge">#{candidate.rank || '1'}</div>
								<div class="candidate-copy">
									<h4>{candidate.filename}</h4>
									<p>{candidate.ai_verdict || 'AI analysis unavailable.'}</p>
								</div>
								<div class="score-box">
									<span>Neural Score</span>
									<strong>{formatScore(candidate.final_score)}</strong>
								</div>
							</div>

							<div class="skill-grid">
								{#each candidate.evaluations || [] as evaluation}
									<div class={`skill-chip ${getStatusClass(evaluation.status)}`}>
										<span>{evaluation.skill}</span>
										<small>{evaluation.status}</small>
									</div>
								{/each}
							</div>
						</article>
					{/each}
				</div>
			{/if}
		</section>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		background:
			radial-gradient(circle at 0 0, rgba(59, 130, 246, 0.16), transparent 28%),
			linear-gradient(180deg, #061018 0%, #0b1120 100%);
		color: #e2e8f0;
	}

	.candidate-page {
		min-height: 100vh;
		display: grid;
		grid-template-columns: 280px 1fr;
		background:
			linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
			linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
		background-size: 30px 30px, 30px 30px;
	}

	.sidebar {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		padding: 24px;
		background: #0b1020;
		border-right: 1px solid rgba(148, 163, 184, 0.18);
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 14px;
	}

	.brand-mark {
		width: 48px;
		height: 48px;
		display: grid;
		place-items: center;
		border-radius: 14px;
		background: linear-gradient(135deg, #0f172a, #3b82f6);
		color: white;
		font-weight: 800;
	}

	.brand h1 {
		margin: 0;
		font-size: 18px;
	}

	.brand p {
		margin: 4px 0 0;
		color: #94a3b8;
	}

	.nav {
		display: grid;
		gap: 10px;
		margin-top: 32px;
	}

	.nav-link {
		padding: 12px 14px;
		border-radius: 14px;
		border: 1px solid rgba(148, 163, 184, 0.14);
		background: rgba(255, 255, 255, 0.04);
		color: #cbd5e1;
		text-decoration: none;
		font-weight: 700;
	}

	.nav-link.active {
		background: #0f172a;
		color: white;
	}

	.sidebar-footer {
		margin-top: 24px;
		padding: 18px;
		border-radius: 18px;
		background: #111827;
		border: 1px solid rgba(255, 255, 255, 0.06);
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
		margin-bottom: 14px;
	}

	.sidebar-footer p {
		margin: 0 0 14px;
		color: #cbd5e1;
		line-height: 1.6;
	}

	.ghost-btn,
	.primary-btn,
	.secondary-btn {
		border: none;
		border-radius: 12px;
		padding: 12px 16px;
		font: inherit;
		font-weight: 700;
		cursor: pointer;
	}

	.ghost-btn {
		width: 100%;
		background: white;
		color: #0f172a;
	}

	.content {
		padding: 32px;
	}

	.hero {
		display: flex;
		justify-content: space-between;
		gap: 20px;
		align-items: flex-start;
		padding: 28px;
		border-radius: 28px;
		background: #0f1117;
		border: 1px solid rgba(255, 255, 255, 0.08);
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
	}

	.eyebrow {
		margin: 0 0 8px;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		font-size: 12px;
		font-weight: 800;
		color: #00f2ff;
	}

	.hero h2,
	.panel h3 {
		margin: 0;
		font-size: 28px;
	}

	.hero-copy {
		margin: 12px 0 0;
		max-width: 720px;
		color: #94a3b8;
		line-height: 1.7;
	}

	.hero-actions {
		display: flex;
		flex-direction: column;
		gap: 10px;
		min-width: 180px;
	}

	.hero-pill {
		padding: 12px 14px;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.08);
		color: #cbd5e1;
		font-weight: 700;
		text-align: center;
	}

	.hero-pill.accent {
		background: rgba(0, 242, 255, 0.08);
		color: #00f2ff;
		border-color: rgba(0, 242, 255, 0.2);
	}

	.stats {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 16px;
		margin: 20px 0;
	}

	.stat-card {
		padding: 18px;
		border-radius: 20px;
		background: #0f1117;
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.stat-card span {
		display: block;
		margin-bottom: 8px;
		color: #94a3b8;
		font-size: 13px;
	}

	.stat-card strong {
		font-size: 30px;
	}

	.panel-grid {
		display: grid;
		grid-template-columns: 360px 1fr;
		gap: 20px;
		align-items: start;
	}

	.panel,
	.results-panel {
		padding: 24px;
		border-radius: 24px;
		background: #0f1117;
		border: 1px solid rgba(255, 255, 255, 0.08);
		box-shadow: 0 16px 32px rgba(0, 0, 0, 0.2);
	}

	.panel-header {
		margin-bottom: 18px;
	}

	.field {
		display: grid;
		gap: 10px;
	}

	label {
		font-size: 13px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #cbd5e1;
	}

	textarea {
		width: 100%;
		min-height: 200px;
		resize: vertical;
		background: #090b0f;
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 14px;
		padding: 16px;
		color: #e2e8f0;
		font: inherit;
		line-height: 1.6;
		box-sizing: border-box;
	}

	.button-row {
		display: flex;
		gap: 12px;
		flex-wrap: wrap;
		margin-top: 18px;
	}

	.primary-btn {
		background: linear-gradient(135deg, #00f2ff, #7000ff);
		color: white;
	}

	.primary-btn.outline {
		background: transparent;
		border: 1px solid rgba(0, 242, 255, 0.45);
		color: #00f2ff;
	}

	.secondary-btn {
		background: rgba(255, 255, 255, 0.04);
		color: #cbd5e1;
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.primary-btn:disabled,
	.secondary-btn:disabled {
		cursor: not-allowed;
		opacity: 0.65;
	}

	.alert {
		margin-top: 16px;
		padding: 12px 14px;
		border-radius: 12px;
		font-weight: 600;
	}

	.alert.error {
		background: rgba(239, 68, 68, 0.12);
		color: #fecaca;
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

	.upload-zone {
		border: 1px dashed rgba(0, 242, 255, 0.35);
		background: #090b0f;
		border-radius: 18px;
		padding: 20px;
		text-align: center;
		cursor: pointer;
		display: grid;
		gap: 8px;
	}

	.upload-icon {
		width: 46px;
		height: 46px;
		margin: 0 auto 6px;
		display: grid;
		place-items: center;
		border-radius: 14px;
		background: rgba(0, 242, 255, 0.12);
		color: #00f2ff;
		font-size: 28px;
	}

	.upload-title {
		font-weight: 700;
		color: #e2e8f0;
	}

	.upload-subtitle {
		color: #94a3b8;
		font-size: 13px;
	}

	.file-input {
		display: none;
	}

	.file-list {
		display: grid;
		gap: 10px;
		margin-top: 16px;
	}

	.empty-copy {
		color: #94a3b8;
		font-size: 14px;
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

	.file-card button {
		border: none;
		background: transparent;
		color: #fca5a5;
		font: inherit;
		cursor: pointer;
	}

	.empty-state {
		padding: 44px 12px;
		text-align: center;
		color: #94a3b8;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.03);
		border: 1px dashed rgba(255, 255, 255, 0.08);
	}

	.candidate-list {
		display: grid;
		gap: 16px;
	}

	.candidate-card {
		padding: 18px;
		border-radius: 18px;
		background: #0b0f14;
		border: 1px solid rgba(255, 255, 255, 0.08);
	}

	.candidate-top {
		display: grid;
		grid-template-columns: auto 1fr auto;
		gap: 14px;
		align-items: start;
	}

	.rank-badge {
		width: 44px;
		height: 44px;
		display: grid;
		place-items: center;
		border-radius: 12px;
		background: rgba(112, 0, 255, 0.95);
		color: white;
		font-weight: 800;
	}

	.candidate-copy h4 {
		margin: 0 0 6px;
		font-size: 18px;
	}

	.candidate-copy p {
		color: #94a3b8;
		line-height: 1.6;
		font-size: 14px;
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

	.skill-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
		gap: 10px;
		margin-top: 16px;
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

	@media (max-width: 1100px) {
		.candidate-page {
			grid-template-columns: 1fr;
		}

		.sidebar {
			border-right: none;
			border-bottom: 1px solid rgba(148, 163, 184, 0.18);
		}

		.panel-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 720px) {
		.content {
			padding: 16px;
		}

		.hero {
			flex-direction: column;
		}

		.stats {
			grid-template-columns: 1fr;
		}

		.candidate-top {
			grid-template-columns: 1fr;
		}

		.score-box {
			text-align: left;
		}
	}
</style>
