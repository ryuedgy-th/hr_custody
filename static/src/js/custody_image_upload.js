/** @odoo-module **/

console.log('📦 Loading Custody Upload Module with Chunked Upload...');

class CustodyUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB per file
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB total
        this.allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        
        // Chunked upload settings
        this.chunkSize = 1024 * 1024; // 1MB default chunk size
        this.minChunkSize = 256 * 1024; // 256KB minimum
        this.maxRetries = 3;
        this.uploadInProgress = false;
        
        console.log('📋 Upload Manager initialized with chunked upload support');
    }

    init() {
        console.log('🚀 Initializing upload functionality...');
        this.setupEventListeners();
        this.renderPreviews();
        this.updateDisplay();
    }

    setupEventListeners() {
        const uploadZone = document.querySelector('#custody_multiple_upload_zone, .custody-upload-zone');
        const fileInput = document.querySelector('#file_input');

        if (!uploadZone || !fileInput) {
            console.warn('⚠️ Upload elements not found');
            return;
        }

        // Drag & Drop events
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('drag-over');
        });

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            if (!uploadZone.contains(e.relatedTarget)) {
                uploadZone.classList.remove('drag-over');
            }
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('drag-over');
            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files);
        });

        // Click to select files
        const browseBtn = document.querySelector('#browse_files_btn');
        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.preventDefault();
                fileInput.click();
            });
        }

        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files);
            e.target.value = ''; // Reset input
        });

        console.log('✅ Event listeners setup complete');
    }

    handleFiles(files) {
        console.log('📂 Processing', files.length, 'files...');

        for (const file of files) {
            if (this.validateFile(file)) {
                this.addFile(file);
            }
        }

        this.renderPreviews();
        this.updateDisplay();
    }

    validateFile(file) {
        // Check file type
        if (!this.allowedTypes.includes(file.type)) {
            this.showError(`File type not allowed: ${file.name}. Supported: JPG, PNG, GIF, WebP, BMP`);
            return false;
        }

        // Check file size
        if (file.size > this.maxFileSize) {
            this.showError(`File too large: ${file.name} (max 5MB per file)`);
            return false;
        }

        // Check total files limit
        if (this.selectedFiles.length >= 20) {
            this.showError('Maximum 20 images allowed');
            return false;
        }

        // Check total size
        if (this.totalSize + file.size > this.maxTotalSize) {
            this.showError('Total file size exceeds 100MB limit');
            return false;
        }

        return true;
    }

    addFile(file) {
        const fileId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        const fileData = {
            id: fileId,
            file: file,
            filename: file.name,
            size: file.size,
            type: file.type,
            description: '',
            dataUrl: null
        };

        this.selectedFiles.push(fileData);
        this.totalSize += file.size;
        this.generatePreview(fileData);

        console.log('✅ File added:', file.name);
    }

    generatePreview(fileData) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            fileData.dataUrl = e.target.result;
            this.renderPreviews();
        };

        reader.onerror = () => {
            console.error('❌ Error reading file:', fileData.filename);
            this.showError(`Error reading file: ${fileData.filename}`);
        };

        reader.readAsDataURL(fileData.file);
    }

    renderPreviews() {
        console.log('🖼️ Rendering previews for', this.selectedFiles.length, 'files');

        const previewContainer = document.getElementById('selected_files_preview');
        const filesList = document.getElementById('files_list');

        if (!previewContainer || !filesList) {
            console.warn('⚠️ Preview containers not found');
            return;
        }

        if (this.selectedFiles.length === 0) {
            previewContainer.style.display = 'none';
            return;
        }

        previewContainer.style.display = 'block';
        filesList.innerHTML = '';

        this.selectedFiles.forEach(file => {
            if (file.dataUrl) {
                const fileItem = document.createElement('div');
                fileItem.className = 'col-md-3 col-sm-4 col-6';
                fileItem.innerHTML = `
                    <div class="file-preview-item" data-file-id="${file.id}">
                        <button type="button" class="file-remove-btn" onclick="window.custodyUploadManager?.removeFile('${file.id}')">
                            ×
                        </button>
                        <img src="${file.dataUrl}" alt="${file.filename}" class="file-preview-img">
                        <div class="file-preview-name">${file.filename}</div>
                        <div class="file-preview-size">${this.formatFileSize(file.size)}</div>
                        <div class="file-preview-desc">
                            <input type="text" placeholder="Description (optional)" value="${file.description}" 
                                   onchange="window.custodyUploadManager?.updateFileDescription('${file.id}', this.value)">
                        </div>
                    </div>
                `;
                filesList.appendChild(fileItem);
            }
        });

        console.log('✅ Previews rendered');
    }

    updateDisplay() {
        console.log('💾 Updating Odoo field widgets...');
        
        // อัพเดท Odoo field widgets
        this.updateOdooField('total_files', this.selectedFiles.length);
        this.updateOdooField('total_size_mb', (this.totalSize / (1024 * 1024)).toFixed(2));
        
        console.log('📊 Display updated:', {
            files: this.selectedFiles.length,
            totalSizeMB: (this.totalSize / (1024 * 1024)).toFixed(2)
        });
    }

    updateOdooField(fieldName, value) {
        const fieldWidget = document.querySelector(`div[name="${fieldName}"]`);
        if (fieldWidget) {
            const span = fieldWidget.querySelector('span');
            if (span) {
                span.textContent = value;
                console.log(`✅ Updated Odoo field ${fieldName}: ${value}`);
            } else {
                console.warn(`⚠️ Span not found in field widget: ${fieldName}`);
            }
        } else {
            console.warn(`⚠️ Odoo field widget not found: ${fieldName}`);
        }
    }

    removeFile(fileId) {
        console.log('🗑️ Removing file:', fileId);
        
        const fileIndex = this.selectedFiles.findIndex(f => f.id == fileId);
        if (fileIndex !== -1) {
            this.totalSize -= this.selectedFiles[fileIndex].size;
            this.selectedFiles.splice(fileIndex, 1);
            this.renderPreviews();
            this.updateDisplay();
            console.log('✅ File removed. Remaining:', this.selectedFiles.length);
        }
    }

    updateFileDescription(fileId, description) {
        const file = this.selectedFiles.find(f => f.id == fileId);
        if (file) {
            file.description = description;
            console.log('📝 Updated description for:', file.filename);
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showError(message) {
        console.error('❌ Error:', message);
        
        let errorContainer = document.getElementById('upload_errors');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.id = 'upload_errors';
            errorContainer.style.marginTop = '10px';
            
            const uploadZone = document.querySelector('#custody_multiple_upload_zone');
            if (uploadZone) {
                uploadZone.appendChild(errorContainer);
            }
        }
        
        errorContainer.innerHTML = `<div class="alert alert-danger" role="alert">${message}</div>`;
        setTimeout(() => {
            errorContainer.innerHTML = '';
        }, 5000);
    }

    showProgress(message, percent = 0) {
        let progressContainer = document.getElementById('upload_progress');
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.id = 'upload_progress';
            progressContainer.style.marginTop = '10px';
            
            const uploadZone = document.querySelector('#custody_multiple_upload_zone');
            if (uploadZone) {
                uploadZone.appendChild(progressContainer);
            }
        }
        
        progressContainer.innerHTML = `
            <div class="alert alert-info" role="alert">
                <div class="d-flex justify-content-between">
                    <span>${message}</span>
                    <span>${percent}%</span>
                </div>
                <div class="progress" style="height: 6px; margin-top: 5px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                         style="width: ${percent}%"></div>
                </div>
            </div>
        `;
    }

    hideProgress() {
        const progressContainer = document.getElementById('upload_progress');
        if (progressContainer) {
            progressContainer.innerHTML = '';
        }
    }

    // 🚀 Chunked Upload Methods
    async uploadFiles() {
        if (this.uploadInProgress) {
            console.log('🚫 Upload already in progress');
            return;
        }

        if (this.selectedFiles.length === 0) {
            this.showError('No files selected for upload');
            return;
        }

        this.uploadInProgress = true;
        console.log(`📡 Starting chunked upload for ${this.selectedFiles.length} files...`);

        try {
            await this.processFilesInChunks();
            this.showProgress('✅ Upload completed successfully!', 100);
            setTimeout(() => this.hideProgress(), 3000);
        } catch (error) {
            console.error('❌ Upload failed:', error);
            this.showError(`Upload failed: ${error.message}`);
        } finally {
            this.uploadInProgress = false;
        }
    }

    async processFilesInChunks() {
        const chunkSize = this.calculateOptimalChunkSize();
        const chunks = this.createFileChunks(chunkSize);
        
        console.log(`📦 Created ${chunks.length} chunks with size ${this.formatFileSize(chunkSize)}`);

        for (let i = 0; i < chunks.length; i++) {
            const chunk = chunks[i];
            const progress = Math.round(((i + 1) / chunks.length) * 100);
            
            this.showProgress(`📤 Uploading chunk ${i + 1}/${chunks.length}...`, progress);
            
            let retries = 0;
            while (retries < this.maxRetries) {
                try {
                    await this.uploadChunk(chunk, i);
                    console.log(`✅ Chunk ${i + 1} uploaded successfully`);
                    break;
                } catch (error) {
                    retries++;
                    console.warn(`⚠️ Chunk ${i + 1} failed (attempt ${retries}):`, error);
                    
                    if (error.status === 413 && retries < this.maxRetries) {
                        // HTTP 413 - reduce chunk size and retry
                        const newChunkSize = Math.max(this.minChunkSize, chunkSize / 2);
                        console.log(`🔄 Reducing chunk size to ${this.formatFileSize(newChunkSize)} and retrying...`);
                        
                        const smallerChunks = this.createFileChunks(newChunkSize);
                        return this.processSpecificChunks(smallerChunks.slice(i));
                    }
                    
                    if (retries >= this.maxRetries) {
                        throw new Error(`Chunk ${i + 1} failed after ${this.maxRetries} attempts`);
                    }
                    
                    // Wait before retry
                    await new Promise(resolve => setTimeout(resolve, 1000 * retries));
                }
            }
        }
    }

    calculateOptimalChunkSize() {
        const avgFileSize = this.totalSize / this.selectedFiles.length;
        
        // Adjust chunk size based on total size and file count
        if (this.totalSize > 50 * 1024 * 1024) { // > 50MB
            return Math.max(this.minChunkSize, Math.min(2 * 1024 * 1024, avgFileSize)); // 2MB max
        } else if (this.totalSize > 10 * 1024 * 1024) { // > 10MB
            return Math.max(this.minChunkSize, Math.min(1 * 1024 * 1024, avgFileSize)); // 1MB max
        } else {
            return Math.max(this.minChunkSize, avgFileSize); // Use average file size
        }
    }

    createFileChunks(chunkSize) {
        const chunks = [];
        let currentChunk = [];
        let currentChunkSize = 0;

        for (const file of this.selectedFiles) {
            if (currentChunkSize + file.size > chunkSize && currentChunk.length > 0) {
                chunks.push(currentChunk);
                currentChunk = [];
                currentChunkSize = 0;
            }
            
            currentChunk.push(file);
            currentChunkSize += file.size;
        }

        if (currentChunk.length > 0) {
            chunks.push(currentChunk);
        }

        return chunks;
    }

    async uploadChunk(files, chunkIndex) {
        const formData = new FormData();
        
        // Add chunk metadata
        formData.append('chunk_index', chunkIndex);
        formData.append('total_files', files.length);
        formData.append('chunk_info', JSON.stringify({
            index: chunkIndex,
            fileCount: files.length,
            totalSize: files.reduce((sum, f) => sum + f.size, 0),
            uploadMethod: 'chunked'
        }));

        // Add files to form data
        files.forEach((file, index) => {
            formData.append(`file_${index}`, file.file);
            formData.append(`filename_${index}`, file.filename);
            formData.append(`description_${index}`, file.description || '');
        });

        // Send chunk to server
        const response = await fetch('/web/dataset/call_kw', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        });

        if (!response.ok) {
            throw { status: response.status, message: response.statusText };
        }

        return response.json();
    }

    async processSpecificChunks(chunks) {
        for (let i = 0; i < chunks.length; i++) {
            const chunk = chunks[i];
            const progress = Math.round(((i + 1) / chunks.length) * 100);
            
            this.showProgress(`📤 Uploading smaller chunk ${i + 1}/${chunks.length}...`, progress);
            await this.uploadChunk(chunk, i);
        }
    }

    getFilesData() {
        return this.selectedFiles.map(file => ({
            filename: file.filename,
            size: file.size,
            type: file.type,
            description: file.description,
            dataUrl: file.dataUrl
        }));
    }
}

// Initialize function with enhanced error handling
function initializeUpload() {
    console.log('🔍 Checking for upload zone...');

    try {
        const uploadZone = document.querySelector('#custody_multiple_upload_zone') || 
                          document.querySelector('.custody-upload-zone');

        if (uploadZone) {
            console.log('✅ Upload zone found!');
            
            if (!window.custodyUploadManager) {
                const manager = new CustodyUploadManager();
                window.custodyUploadManager = manager;
                manager.init();
            } else {
                console.log('ℹ️ Manager already exists');
            }
        } else {
            console.log('⏳ Upload zone not found, retrying in 1000ms...');
            setTimeout(initializeUpload, 1000);
        }
    } catch (error) {
        console.error('❌ Error initializing upload:', error);
        setTimeout(initializeUpload, 2000);
    }
}

// Multiple initialization strategies
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpload);
} else {
    initializeUpload();
}

window.addEventListener('load', () => {
    setTimeout(initializeUpload, 1000);
});

// Additional safety for Odoo environment
setTimeout(initializeUpload, 2000);

console.log('✅ Custody Upload Module Loaded - Complete with Chunked Upload Strategy');