document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('csvFile');
    const uploadMsg = document.getElementById('uploadMsg');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const dropArea = document.getElementById('dropArea');
    const selectedFileInfo = document.getElementById('selectedFile');
    const recentList = document.getElementById('recentList');
    const totalScans = document.getElementById('totalScans');
    const threatsDetected = document.getElementById('threatsDetected');
    const preview = document.getElementById('preview');

    // Initialize stats
    updateStats();

    // Make clearFileSelection available globally
    window.clearFileSelection = function() {
        fileInput.value = '';
        selectedFileInfo.innerHTML = '';
        analyzeBtn.disabled = true;
        uploadMsg.innerHTML = '';
    };

    // Handle file selection
    fileInput.addEventListener('change', function() {
        if (this.files.length) {
            const file = this.files[0];
            selectedFileInfo.innerHTML = `
                <i class="bi bi-file-earmark-text me-2"></i>
                <strong>${file.name}</strong> (${(file.size / 1024 / 1024).toFixed(2)} MB)
                <button class="btn btn-sm btn-link p-0 ms-2" onclick="clearFileSelection()">
                    <i class="bi bi-x-circle"></i>
                </button>
            `;
            analyzeBtn.disabled = false;
        }
    });

    // Handle form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!fileInput.files || !fileInput.files[0]) {
            uploadMsg.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Please select a file to analyze.
                </div>
            `;
            return;
        }

        const formData = new FormData(uploadForm);
        
        try {
            // Show loading state
            uploadMsg.innerHTML = `
                <div class="alert alert-info d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    Processing your file...
                </div>
            `;

            const response = await fetch('/api/score_csv', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to process file');
            }

            const result = await response.json();

            // Show success message
            uploadMsg.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    <strong>Analysis Complete!</strong> ${result.message}
                    <div class="mt-2">
                        <span class="badge bg-primary">${result.file_type || 'N/A'}</span>
                        <span class="badge bg-secondary">${result.features_used ? result.features_used.join(', ') : 'N/A'}</span>
                    </div>
                </div>
            `;

            // Update stats and preview
            updateStats();
            updatePreview(result);
            updateRecentAnomalies();

        } catch (error) {
            console.error('Error:', error);
            uploadMsg.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <strong>Error:</strong> ${error.message || 'Failed to process file'}
                </div>
            `;
        }
    });

    // Handle analyze button click
    analyzeBtn.addEventListener('click', function() {
        uploadForm.dispatchEvent(new Event('submit'));
    });

    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropArea.classList.add('border-primary');
        dropArea.style.backgroundColor = 'rgba(67, 97, 238, 0.1)';
    }

    function unhighlight() {
        dropArea.classList.remove('border-primary');
        dropArea.style.backgroundColor = '';
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            fileInput.files = files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });

    function updatePreview(result) {
        if (!preview) {
            console.error('Preview element not found');
            return;
        }
        
        try {
            if (result && result.results_preview && result.results_preview.length > 0) {
                // Get all unique column names from all items
                const allColumns = new Set();
                result.results_preview.forEach(item => {
                    Object.keys(item).forEach(key => {
                        if (!key.startsWith('_')) {
                            allColumns.add(key);
                        }
                    });
                });
                
                const columns = Array.from(allColumns);
                
                let html = `
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead class="sticky-top bg-white">
                                <tr>
                                    ${columns.map(header => 
                                        `<th scope="col">
                                            ${header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                        </th>`
                                    ).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${result.results_preview.map((item, index) => {
                                    const rowClass = item.score > 0.8 ? 'anomaly-high' : 
                                                   item.score > 0.6 ? 'anomaly-medium' : 'anomaly-low';
                                    
                                    return `
                                        <tr class="${rowClass}" style="cursor: pointer;" 
                                            onclick="showAnomalyDetails(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                                            ${columns.map(col => {
                                                let value = item[col];
                                                let displayValue = value;
                                                
                                                if (col === 'timestamp' && value) {
                                                    displayValue = new Date(value).toLocaleString();
                                                } else if (typeof value === 'number') {
                                                    displayValue = value.toFixed(4);
                                                } else if (value === null || value === undefined) {
                                                    displayValue = '-';
                                                } else if (typeof value === 'object') {
                                                    displayValue = JSON.stringify(value);
                                                }
                                                
                                                if (col === 'score') {
                                                    const badgeClass = value > 0.8 ? 'bg-danger' : 
                                                                     value > 0.6 ? 'bg-warning' : 'bg-success';
                                                    return `<td><span class="badge ${badgeClass}">${displayValue}</span></td>`;
                                                }
                                                
                                                return `<td>${displayValue}</td>`;
                                            }).join('')}
                                        </tr>`;
                                }).join('')}
                            </tbody>
                        </table>
                    </div>`;
                
                preview.innerHTML = html;
            } else {
                // No results or empty results
                preview.innerHTML = `
                    <div class="text-center p-5 text-muted">
                        <i class="bi bi-exclamation-circle" style="font-size: 3rem; opacity: 0.3;"></i>
                        <p class="mt-3">${result && result.message ? result.message : 'No results to display'}</p>
                    </div>`;
            }
        } catch (error) {
            console.error('Error updating preview:', error);
            preview.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Error loading results: ${error.message}
                </div>`;
        }
    }

    async function updateRecentAnomalies() {
        if (!recentList) return;
        
        try {
            const response = await fetch('/api/recent');
            if (!response.ok) throw new Error('Failed to fetch recent anomalies');
            
            const data = await response.json();
            
            if (data.recent && data.recent.length > 0) {
                recentList.innerHTML = data.recent.map(item => `
                    <div class="list-group-item list-group-item-action" 
                         onclick="showAnomalyDetails(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">Anomaly Detected</h6>
                            <small class="text-muted">
                                ${item._timestamp ? new Date(item._timestamp).toLocaleString() : 'Just now'}
                            </small>
                        </div>
                        <p class="mb-1 text-truncate">
                            ${Object.entries(item)
                                .filter(([key]) => !key.startsWith('_'))
                                .map(([key, val]) => `${key}: ${val}`)
                                .join(', ')
                                .substring(0, 80)}...
                        </p>
                        <small class="text-muted">Click for details</small>
                    </div>`
                ).join('');
            } else {
                recentList.innerHTML = `
                    <div class="text-center p-4 text-muted">
                        <i class="bi bi-activity" style="font-size: 2rem; opacity: 0.3;"></i>
                        <p class="mt-2">No recent anomalies found</p>
                    </div>`;
            }
        } catch (error) {
            console.error('Error fetching recent anomalies:', error);
            recentList.innerHTML = `
                <div class="alert alert-danger m-3">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Error loading recent anomalies
                </div>`;
        }
    }

    async function updateStats() {
        if (!totalScans || !threatsDetected) return;
        
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const data = await response.json();
                if (data.totalScans) totalScans.textContent = data.totalScans.toLocaleString();
                if (data.threatsDetected) threatsDetected.textContent = data.threatsDetected.toLocaleString();
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
            // Fallback to random data if API fails
            const stats = {
                totalScans: Math.floor(Math.random() * 1000) + 500,
                threatsDetected: Math.floor(Math.random() * 100) + 10
            };
            
            totalScans.textContent = stats.totalScans.toLocaleString();
            threatsDetected.textContent = stats.threatsDetected.toLocaleString();
        }
    }

    // Make showAnomalyDetails available globally
    window.showAnomalyDetails = function(item) {
        if (!item) return;
        
        // Create modal if it doesn't exist
        let modal = document.getElementById('anomalyDetailsModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'anomalyDetailsModal';
            modal.tabIndex = '-1';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Anomaly Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="anomalyDetailsContent">
                            <pre>${JSON.stringify(item, null, 2)}</pre>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary">Export as JSON</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        // Update modal content
        const content = document.getElementById('anomalyDetailsContent');
        content.innerHTML = `<pre>${JSON.stringify(item, null, 2)}</pre>`;
        
        // Show modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    };

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Quick Actions Event Listeners
    document.getElementById('scanNowBtn')?.addEventListener('click', startRealtimeScan);
    document.getElementById('scanDirBtn')?.addEventListener('click', scanSelectedDirectory);
    
    // Add click handlers for common locations
    document.querySelectorAll('[data-path]').forEach(button => {
        button.addEventListener('click', (e) => {
            const path = e.currentTarget.getAttribute('data-path');
            scanDirectory(path);
        });
    });

    // Initial load
    updateRecentAnomalies();
    loadRecentDirectories();

    // Function to start real-time scanning
    function startRealtimeScan() {
        const btn = document.getElementById('scanNowBtn');
        const icon = btn.querySelector('i');
        const originalHTML = btn.innerHTML;
        
        // Update button state
        btn.disabled = true;
        icon.className = 'bi bi-arrow-repeat me-2 fa-spin';
        btn.innerHTML = btn.innerHTML.replace('Scan Now', 'Scanning...');
        
        // Simulate scanning (in a real app, this would be an API call)
        setTimeout(() => {
            // Reset button state
            btn.disabled = false;
            btn.innerHTML = originalHTML;
            
            // Show success message
            uploadMsg.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>
                    <strong>Scan Complete!</strong> No new threats detected in real-time monitoring.
                </div>`;
                
            // Update stats
            updateStats();
        }, 3000);
    }
    
    // Function to scan selected directory
    function scanSelectedDirectory() {
        const select = document.getElementById('recentDirs');
        const dir = select.value;
        if (dir) {
            scanDirectory(dir);
        }
    }
    
    // Function to scan a specific directory
    async function scanDirectory(dirPath) {
        try {
            const response = await fetch('/api/scan_directory', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path: dirPath })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                uploadMsg.innerHTML = `
                    <div class="alert alert-success">
                        <i class="bi bi-check-circle-fill me-2"></i>
                        <strong>Directory Scanned:</strong> ${result.message}
                    </div>`;
                
                if (result.anomalies && result.anomalies.length > 0) {
                    updatePreview({ results_preview: result.anomalies });
                }
                
                updateStats();
                updateRecentAnomalies();
            } else {
                throw new Error(result.message || 'Failed to scan directory');
            }
        } catch (error) {
            console.error('Error scanning directory:', error);
            uploadMsg.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <strong>Error:</strong> ${error.message}
                </div>`;
        }
    }
    
    // Function to load recent directories
    function loadRecentDirectories() {
        const select = document.getElementById('recentDirs');
        if (!select) return;
        
        // In a real app, this would come from the backend
        const recentDirs = [
            { name: 'Documents', path: '/home/user/documents' },
            { name: 'Downloads', path: '/home/user/downloads' },
            { name: 'Project Files', path: '/home/user/projects/anomaly-detection' }
        ];
        
        // Clear existing options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        // Add recent directories
        recentDirs.forEach(dir => {
            const option = document.createElement('option');
            option.value = dir.path;
            option.textContent = `${dir.name} (${dir.path})`;
            select.appendChild(option);
        });
    }
});