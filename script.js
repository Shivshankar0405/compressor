document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileDetails = document.getElementById('file-details');
    const fileName = document.getElementById('file-name');
    const fileOriginalSize = document.getElementById('file-original-size');
    const removeBtn = document.getElementById('remove-btn');
    const targetSizeInput = document.getElementById('target-size');
    const compressBtn = document.getElementById('compress-btn');
    const sizeUnit = document.getElementById('size-unit');
    const statusMessage = document.getElementById('status-message');
    const btnText = compressBtn.querySelector('span');
    const loader = compressBtn.querySelector('.loader');

    let currentFile = null;

    // Drag and Drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp'];

            if (validTypes.includes(file.type) || file.name.match(/\.(pdf|jpg|jpeg|png|webp)$/i)) {
                currentFile = file;
                displayFileDetails(file);
            } else {
                showStatus('Unsupported file type. Please upload PDF, JPG, PNG, or WEBP.', 'error');
            }
        }
    }

    function displayFileDetails(file) {
        dropZone.classList.add('hidden');
        fileDetails.classList.remove('hidden');
        fileName.textContent = file.name;
        fileOriginalSize.textContent = formatBytes(file.size);
        validateForm();
        hideStatus();
    }

    removeBtn.addEventListener('click', () => {
        currentFile = null;
        fileInput.value = '';
        dropZone.classList.remove('hidden');
        fileDetails.classList.add('hidden');
        validateForm();
        hideStatus();
    });

    targetSizeInput.addEventListener('input', validateForm);

    function validateForm() {
        const size = parseFloat(targetSizeInput.value);
        if (currentFile && !isNaN(size) && size > 0) {
            compressBtn.disabled = false;
        } else {
            compressBtn.disabled = true;
        }
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    compressBtn.addEventListener('click', async () => {
        if (!currentFile || compressBtn.disabled) return;

        const targetSize = parseFloat(targetSizeInput.value);
        let targetSizeKB = targetSize;
        if (sizeUnit.value === 'MB') {
            targetSizeKB = targetSize * 1024;
        }

        const originalSizeKB = currentFile.size / 1024;
        if (targetSizeKB >= originalSizeKB) {
            showStatus("Target size should be smaller than the original size for compression.", "error");
            return;
        }

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('targetSizeKB', targetSizeKB);

        compressBtn.disabled = true;
        btnText.textContent = 'Processing...';
        loader.classList.remove('hidden');
        hideStatus();

        try {
            // Replace this with your actual Render URL when deploying (e.g., 'https://your-app-name.onrender.com')
            const API_BASE_URL = 'https://compressor-api-3771.onrender.com';

            const response = await fetch(`${API_BASE_URL}/api/compress`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();

                const finalSizeArr = formatBytes(blob.size);

                const disposition = response.headers.get('Content-Disposition');
                let targetFilename = "compressed_file";
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    var matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) {
                        targetFilename = matches[1].replace(/['"]/g, '');
                    }
                } else {
                    targetFilename = "compressed_" + currentFile.name;
                }

                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;
                a.download = targetFilename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(downloadUrl);
                document.body.removeChild(a);

                showStatus(`Success! Compressed file size is exactly ${blob.size} bytes (${finalSizeArr}). Download starting...`, 'success');
                updateStats(false); // Refresh the counters
            } else {
                const errorData = await response.json();
                showStatus(errorData.error || 'Failed to compress file.', 'error');
            }
        } catch (error) {
            showStatus('An error occurred during compression. Make sure backend is running.', 'error');
            console.error(error);
        } finally {
            validateForm();
            btnText.textContent = 'Compress File';
            loader.classList.add('hidden');
        }
    });

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.classList.remove('hidden');
    }

    function hideStatus() {
        statusMessage.classList.add('hidden');
    }

    const API_BASE_URL = 'https://compressor-api-3771.onrender.com';

    // Live Stats Logic connected to the backend
    function updateStats(isNewView = false) {
        const method = isNewView ? 'POST' : 'GET';
        // Add cache-buster to prevent mobile browsers from aggressively caching the old response
        const cacheBuster = `?t=${new Date().getTime()}`;

        fetch(`${API_BASE_URL}/api/stats${cacheBuster}`, { method })
            .then(res => res.json())
            .then(data => {
                const viewsEl = document.getElementById('views-count');
                const pdfsEl = document.getElementById('pdfs-count');
                const imagesEl = document.getElementById('images-count');

                if (viewsEl) viewsEl.textContent = data.views.toLocaleString();
                if (pdfsEl) pdfsEl.textContent = data.pdfs.toLocaleString();
                if (imagesEl) imagesEl.textContent = data.images.toLocaleString();
            })
            .catch(err => {
                console.error("Failed to fetch stats", err);
                const viewsEl = document.getElementById('views-count');
                if (viewsEl && viewsEl.textContent === 'Loading...') {
                    viewsEl.textContent = "Error";
                }
            });
    }

    // Call initially to register a page view
    updateStats(true);
});
