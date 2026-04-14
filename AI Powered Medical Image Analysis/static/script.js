document.addEventListener("DOMContentLoaded", () => {
    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("file-input");
    const imagePreview = document.getElementById("image-preview");
    const uploadContent = document.getElementById("upload-content");
    const analyzeBtn = document.getElementById("analyze-btn");
    const btnText = document.getElementById("btn-text");
    const spinner = document.getElementById("loading-spinner");
    const scanLine = document.getElementById("scan-line");
    
    const resultsDashboard = document.getElementById("results-dashboard");
    const diagnosticLabel = document.getElementById("diagnostic-label");
    const statusIndicator = document.getElementById("status-indicator");
    const confidencePercent = document.getElementById("confidence-percent");
    const confidenceFill = document.getElementById("confidence-fill");
    
    const heatmapSkeleton = document.getElementById("heatmap-skeleton");
    const heatmapWrapper = document.getElementById("heatmap-wrapper");
    const heatmapResult = document.getElementById("heatmap-result");

    let currentFile = null;

    // --- Neural Network Background Initialization ---
    async function initParticles() {
        try {
            await tsParticles.load("tsparticles", {
                fullScreen: { enable: true, zIndex: -2 },
                fpsLimit: 60,
                particles: {
                    number: { value: 60, density: { enable: true, value_area: 800 } },
                    color: { value: "#06b6d4" },
                    links: { enable: true, color: "#3b82f6", distance: 150, opacity: 0.3, width: 1 },
                    move: { enable: true, speed: 0.8, direction: "none", random: false, straight: false, outModes: "out" },
                    size: { value: { min: 1, max: 3 } },
                    opacity: { value: 0.5 }
                },
                interactivity: {
                    events: {
                        onHover: { enable: true, mode: "grab" }
                    },
                    modes: {
                        grab: { distance: 140, links: { opacity: 0.8 } }
                    }
                },
                detectRetina: true,
            });
        } catch(e) {
            console.error("tsParticles failed to load", e);
        }
    }
    initParticles();

    // --- File Drag & Drop Handlers ---
    uploadZone.addEventListener("click", () => fileInput.click());

    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.classList.add("drag-over");
    });

    uploadZone.addEventListener("dragleave", () => {
        uploadZone.classList.remove("drag-over");
    });

    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.type.startsWith("image/")) {
            alert("Please upload a valid image file (JPEG, PNG).");
            return;
        }

        currentFile = file;
        
        // Setup Image Preview
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.classList.remove("hidden");
            document.getElementById("preview-placeholder").classList.add("hidden");
            analyzeBtn.disabled = false;
            
            // Hide previous results
            resultsDashboard.classList.remove("visible");
            setTimeout(() => {
                resultsDashboard.classList.add("hidden");
                resetDashboard();
            }, 500);
        };
        reader.readAsDataURL(file);
    }

    // --- Analysis ---
    analyzeBtn.addEventListener("click", async () => {
        if (!currentFile) return;

        // UI State -> Loading
        analyzeBtn.disabled = true;
        btnText.textContent = "Scanning Anatomy...";
        spinner.classList.remove("hidden");
        scanLine.classList.remove("hidden");

        const formData = new FormData();
        formData.append("file", currentFile);

        try {
            // Unhide Dashboard (but empty)
            resultsDashboard.classList.remove("hidden");
            // small delay to allow display:block to apply before adding opacity class
            setTimeout(() => resultsDashboard.classList.add("visible"), 50);

            // 1. Fetch Prediction
            const predResponse = await fetch("/predict", {
                method: "POST",
                body: formData
            });
            
            if (!predResponse.ok) throw new Error("Prediction API Failed");
            const predData = await predResponse.json();

            // Populate Prediction
            updatePredictionUI(predData.prediction, predData.confidence);

            // 2. Fetch Grad-CAM
            const camResponse = await fetch("/gradcam", {
                method: "POST",
                body: formData
            });

            if (!camResponse.ok) throw new Error("Grad-CAM API Failed");
            const camBlob = await camResponse.blob();
            const camUrl = URL.createObjectURL(camBlob);

            // Populate Grad-CAM
            heatmapResult.src = camUrl;
            heatmapResult.onload = () => {
                heatmapSkeleton.classList.add("hidden");
                heatmapWrapper.classList.remove("hidden");
                heatmapWrapper.classList.add("visible");
            };

        } catch (error) {
            console.error(error);
            alert("An error occurred during analysis. Check console.");
        } finally {
            // UI State -> Idle
            btnText.textContent = "Initiate Diagnostic Scan";
            spinner.classList.add("hidden");
            scanLine.classList.add("hidden");
            analyzeBtn.disabled = false;
        }
    });

    function updatePredictionUI(label, confidence) {
        diagnosticLabel.textContent = label;
        
        // Remove old classes
        diagnosticLabel.classList.remove("success", "danger");
        statusIndicator.classList.remove("success", "danger");

        if (label === "PNEUMONIA") {
            diagnosticLabel.classList.add("danger");
            statusIndicator.classList.add("danger");
        } else {
            diagnosticLabel.classList.add("success");
            statusIndicator.classList.add("success");
        }

        const percentage = (confidence * 100).toFixed(1);
        confidencePercent.textContent = `${percentage}%`;
        
        // trigger animation
        setTimeout(() => {
            confidenceFill.style.width = `${percentage}%`;
        }, 100);
    }

    function resetDashboard() {
        diagnosticLabel.textContent = "--";
        diagnosticLabel.classList.remove("success", "danger");
        statusIndicator.classList.remove("success", "danger");
        confidencePercent.textContent = "0%";
        confidenceFill.style.width = "0%";
        
        heatmapWrapper.classList.remove("visible");
        heatmapWrapper.classList.add("hidden");
        heatmapSkeleton.classList.remove("hidden");
        heatmapResult.src = "";
    }
});
