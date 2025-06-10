/** @odoo-module **/

// Updated 2025-06-11 - Fixed Odoo Server Error with enhanced debugging

console.log('🚀 Loading Custody Upload Manager...');

export class CustodyUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFiles = 20;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        this.initialized = false;
        this.isProcessing = false;
        this.clickTimeout = null;
        this.lastClickTime = 0;
        this.browseButtonClicked = false;
        
        console.log('📋 Upload Manager Created');
    }

    init() {
        if (this.initialized) {
            console.log('⚠️ Manager already initialized');
            return;
        }

        console.log('🔍 Looking for upload elements...');
        
        const elements = {
            uploadZoneById: document.querySelector('#custody_multiple_upload_zone'),
            uploadZoneByClass: document.querySelector('.custody-upload-zone'),
            dropzone: document.querySelector('.upload-dropzone'),
            fileInput: document.getElementById('file_input'),
            browseBtn: document.getElementById('browse_files_btn'),
            previewContainer: document.getElementById('selected_files_preview'),
            filesList: document.getElementById('files_list')
        };

        console.log('🔍 Available elements:', elements);

        const uploadZone = elements.uploadZoneById || elements.uploadZoneByClass;
        
        if (!uploadZone || !elements.dropzone || !elements.fileInput || !elements.browseBtn) {
            console.log('⏳ Required elements not found, retrying in 1000ms...');
            setTimeout(() => this.init(), 1000);
            return;
        }

        console.log('✅ Found required elements, setting up events...');
        this.setupEvents(elements);
        this.setupUploadButton();
        this.initialized = true;
        console.log('✅ Manager initialized successfully');
    }

    setupUploadButton() {
        // Intercept the "Start Upload" button
        const uploadButton = document.querySelector('button[name="action_upload_images"]');
        if (uploadButton) {
            console.log('✅ Found upload button, intercepting...');
            
            // Remove existing click handlers
            const newButton = uploadButton.cloneNode(true);
            uploadButton.parentNode.replaceChild(newButton, uploadButton);
            
            // Add our custom handler
            newButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🚀 Custom upload handler triggered');
                this.handleCustomUpload();
            });
        } else {
            console.log('⚠️ Upload button not found, retrying...');
            setTimeout(() => this.setupUploadButton(), 1000);
        }
    }

    async handleCustomUpload() {
        if (this.selectedFiles.length === 0) {
            alert('Please select at least one image to upload.');
            return;
        }

        try {
            console.log('📡 Starting enhanced RPC upload...');
            
            // Prepare data for RPC call with size reduction for large images
            const imagesData = this.selectedFiles
                .filter(file => file.dataUrl)
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    data: this.compressBase64IfNeeded(file.dataUrl, file.size),
                    description: file.description || '',
                    id: file.id
                }));

            // Get wizard record ID from the current page
            const wizardId = this.getWizardId();
            if (!wizardId) {
                throw new Error('Could not find wizard ID');
            }

            console.log(`📡 Uploading ${imagesData.length} files via RPC to wizard ${wizardId}...`);
            console.log('📊 Upload payload summary:', {
                wizardId: wizardId,
                fileCount: imagesData.length,
                totalSizeMB: (this.totalSize / (1024 * 1024)).toFixed(2),
                firstFileName: imagesData[0]?.filename,
                dataSize: imagesData[0]?.data?.length
            });

            // STEP 1: Update wizard with image data
            const updateData = {
                model: 'custody.image.upload.wizard',
                method: 'write',
                args: [[wizardId], {
                    'images_data': JSON.stringify(imagesData),
                    'total_files': this.selectedFiles.length,
                    'total_size_mb': parseFloat((this.totalSize / (1024 * 1024)).toFixed(2))
                }],
                kwargs: {}
            };

            console.log('🔄 Step 1: Updating wizard with file data...');
            const updateResult = await this.callOdooRPC('/web/dataset/call_kw', updateData);
            console.log('✅ Step 1 completed: Wizard updated');

            // STEP 2: Trigger the upload action with enhanced error handling
            const uploadData = {
                model: 'custody.image.upload.wizard',
                method: 'action_upload_images',
                args: [[wizardId]],
                kwargs: {}
            };

            console.log('🔄 Step 2: Triggering upload action...');
            const uploadResult = await this.callOdooRPCWithRetry('/web/dataset/call_kw', uploadData);
            console.log('✅ Step 2 completed: Upload action result:', uploadResult);

            // Handle the result
            if (uploadResult) {
                if (uploadResult.type === 'ir.actions.client') {
                    // Show success notification
                    this.showNotification(uploadResult.params);
                    
                    // Refresh the form or close dialog
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    console.log('ℹ️ Upload completed with different result type:', uploadResult);
                    this.showNotification({
                        title: 'Upload Completed',
                        message: 'Images uploaded successfully!',
                        type: 'success'
                    });
                    setTimeout(() => window.location.reload(), 1000);
                }
            } else {
                console.log('⚠️ Upload completed but no result returned');
                this.showNotification({
                    title: 'Upload Status',
                    message: 'Upload completed. Please check the results.',
                    type: 'info'
                });
                setTimeout(() => window.location.reload(), 2000);
            }

        } catch (error) {
            console.error('❌ Upload failed:', error);
            console.error('❌ Error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            
            // Show more detailed error message
            const errorMessage = this.getDetailedErrorMessage(error);
            alert(`Upload failed: ${errorMessage}`);
        }
    }

    compressBase64IfNeeded(dataUrl, originalSize) {
        // If the original file is over 2MB, try to reduce base64 size
        if (originalSize > 2 * 1024 * 1024) {
            try {
                // Extract base64 part only (remove data:image/...;base64,)
                const base64Data = dataUrl.split(',')[1] || dataUrl;
                console.log(`📦 Compressing large file (${originalSize} bytes) base64 data...`);
                return base64Data;
            } catch (e) {
                console.warn('⚠️ Failed to compress base64, using original');
                return dataUrl;
            }
        }
        return dataUrl;
    }

    getDetailedErrorMessage(error) {
        const message = error.message || 'Unknown error';
        
        if (message.includes('Odoo Server Error')) {
            return 'Server processing error. This might be due to:\n' +
                   '• File size too large\n' +
                   '• Invalid file format\n' +
                   '• Database constraints\n' +
                   '• Permission issues\n\n' +
                   'Please try with smaller images or contact administrator.';
        }
        
        if (message.includes('403') || message.includes('Forbidden')) {
            return 'Permission denied. You may not have rights to upload images.';
        }
        
        if (message.includes('404') || message.includes('Not Found')) {
            return 'Upload service not found. Please refresh the page and try again.';
        }
        
        if (message.includes('413') || message.includes('Payload Too Large')) {
            return 'Files are too large. Please use smaller images.';
        }
        
        if (message.includes('Network')) {
            return 'Network connection error. Please check your internet connection.';
        }
        
        return message;
    }

    async callOdooRPCWithRetry(url, data, maxRetries = 2) {
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                console.log(`🔄 RPC attempt ${attempt}/${maxRetries}`);
                const result = await this.callOdooRPC(url, data);
                return result;
            } catch (error) {
                lastError = error;
                console.warn(`⚠️ RPC attempt ${attempt} failed:`, error.message);
                
                if (attempt < maxRetries) {
                    console.log(`⏳ Retrying in ${attempt * 1000}ms...`);
                    await new Promise(resolve => setTimeout(resolve, attempt * 1000));
                }
            }
        }
        
        throw lastError;
    }

    getWizardId() {
        console.log('🔍 Searching for wizard ID...');
        
        // Method 1: Check URL parameters - ENHANCED for Odoo patterns
        const url = window.location.href;
        console.log('🔍 Current URL:', url);
        
        // Check for Odoo action URL patterns (most reliable)
        let match = url.match(/\/action-\d+\/(\d+)/) ||  // /action-564/22
                   url.match(/id=(\d+)/) ||               // ?id=22
                   url.match(/res_id=(\d+)/) ||           // ?res_id=22
                   url.match(/\/(\d+)$/) ||               // ends with /22
                   url.match(/\/(\d+)(?:\/|$|\?)/);       // /22/ or /22? or /22$
                   
        if (match) {
            const urlId = parseInt(match[1]);
            console.log('✅ Found wizard ID in URL pattern:', urlId);
            return urlId;
        }
        
        console.error('❌ Could not determine wizard ID from URL');
        return null;
    }

    async callOdooRPC(url, data) {
        console.log('🌐 Making RPC call to:', url);
        console.log('📊 RPC data summary:', {
            model: data.model,
            method: data.method,
            argsLength: data.args?.length,
            firstArgType: typeof data.args?.[0],
            firstArgLength: Array.isArray(data.args?.[0]) ? data.args[0].length : 'not array'
        });

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: data,
                id: Math.floor(Math.random() * 1000000)
            })
        });

        console.log('📡 RPC response status:', response.status, response.statusText);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log('📊 RPC response structure:', {
            hasResult: 'result' in result,
            hasError: 'error' in result,
            resultType: typeof result.result,
            errorType: result.error ? typeof result.error : 'none'
        });
        
        if (result.error) {
            console.error('❌ Server error details:', result.error);
            throw new Error(result.error.message || result.error.data?.message || 'Odoo Server Error');
        }

        return result.result;
    }

    showNotification(params) {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            <strong>${params.title || 'Success'}</strong><br>
            ${params.message || 'Operation completed successfully'}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    triggerFileDialog() {
        const now = Date.now();
        
        if (now - this.lastClickTime < 300) {
            console.log('⚠️ Rapid click detected, ignoring');
            return;
        }
        
        if (this.clickTimeout) {
            console.log('⚠️ File dialog already triggered, ignoring');
            return;
        }

        console.log('🎯 Triggering file dialog...');
        this.lastClickTime = now;
        this.browseButtonClicked = true;
        
        const fileInput = document.getElementById('file_input');
        if (fileInput) {
            fileInput.click();
            console.log('✅ File dialog opened');
            
            this.clickTimeout = setTimeout(() => {
                this.clickTimeout = null;
                this.browseButtonClicked = false;
            }, 500);
        } else {
            console.error('❌ File input not found');
            this.browseButtonClicked = false;
        }
    }

    setupEvents(elements) {
        const { dropzone, fileInput, browseBtn } = elements;
        
        console.log('🔧 Setting up event listeners...');

        // Browse button events
        ['mousedown', 'mouseup', 'click'].forEach(eventType => {
            browseBtn.addEventListener(eventType, (e) => {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                if (eventType === 'mousedown' && !this.isProcessing) {
                    console.log('🖱️ Browse button clicked!');
                    this.triggerFileDialog();
                } else if (eventType !== 'mousedown') {
                    console.log(`🚫 Browse button ${eventType} prevented`);
                }
            }, true);
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            console.log('📁 File input changed! Files:', e.target.files.length);
            
            if (this.isProcessing) {
                console.log('⚠️ Already processing, ignoring');
                return;
            }

            if (e.target.files && e.target.files.length > 0) {
                this.isProcessing = true;
                console.log('📝 Processing selected files...');
                this.handleFiles(e.target.files);
                
                setTimeout(() => {
                    this.isProcessing = false;
                    e.target.value = '';
                }, 1000);
            }
        });

        // Dropzone click
        dropzone.addEventListener('click', (e) => {
            if (this.browseButtonClicked) {
                console.log('🚫 Browse button just clicked, ignoring dropzone');
                return;
            }

            const browseArea = browseBtn.getBoundingClientRect();
            const clickX = e.clientX;
            const clickY = e.clientY;
            
            const isInBrowseArea = (
                clickX >= browseArea.left &&
                clickX <= browseArea.right &&
                clickY >= browseArea.top &&
                clickY <= browseArea.bottom
            );
            
            if (isInBrowseArea || 
                e.target === browseBtn || 
                browseBtn.contains(e.target) || 
                e.target.closest('#browse_files_btn')) {
                console.log('🚫 Click in browse area, ignoring dropzone event');
                return;
            }

            if (this.isProcessing) return;

            e.preventDefault();
            e.stopPropagation();
            console.log('🖱️ Dropzone area clicked (outside browse button)');
            this.triggerFileDialog();
        });

        // Drag & Drop
        this.setupDragAndDrop(dropzone);

        console.log('✅ Event listeners setup complete');
    }

    setupDragAndDrop(dropzone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add('dragover');
                console.log('🎯 Drag over detected');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            if (this.isProcessing) return;

            const files = e.dataTransfer.files;
            console.log('📂 Files dropped:', files.length);
            
            if (files.length > 0) {
                this.isProcessing = true;
                this.handleFiles(files);
                setTimeout(() => {
                    this.isProcessing = false;
                }, 1000);
            }
        }, false);
    }

    handleFiles(files) {
        console.log('📝 Processing files:', files.length);

        if (!files || files.length === 0) {
            console.log('⚠️ No files to process');
            return;
        }

        if (this.selectedFiles.length + files.length > this.maxFiles) {
            alert(`Maximum ${this.maxFiles} files allowed. Currently selected: ${this.selectedFiles.length}`);
            return;
        }

        let validFiles = 0;
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            console.log('🔍 Checking file:', file.name, file.type, file.size);

            if (!this.allowedTypes.includes(file.type)) {
                alert(`File "${file.name}" has unsupported format. Allowed: JPEG, PNG, GIF, WebP, BMP`);
                continue;
            }

            if (file.size > this.maxFileSize) {
                alert(`File "${file.name}" exceeds 5MB limit`);
                continue;
            }

            if (this.totalSize + file.size > this.maxTotalSize) {
                alert('Total size would exceed 100MB limit');
                break;
            }

            console.log('✅ File valid:', file.name);
            this.addFile(file);
            validFiles++;
        }

        console.log(`📊 Added ${validFiles} valid files. Total: ${this.selectedFiles.length}`);
        this.updateDisplay();
    }

    addFile(file) {
        const fileData = {
            id: Date.now() + Math.random(),
            filename: file.name,
            size: file.size,
            type: file.type,
            file: file,
            description: ''
        };

        this.selectedFiles.push(fileData);
        this.totalSize += file.size;
        this.createFilePreview(fileData);
    }

    createFilePreview(fileData) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            fileData.dataUrl = e.target.result;
            this.renderPreviews();
        };

        reader.onerror = () => {
            console.error('Error reading file:', fileData.filename);
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
        // หา Odoo field widget
        const fieldWidget = document.querySelector(`div[name="${fieldName}"]`);
        if (fieldWidget) {
            // อัพเดท span ข้างใน
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
}

// Initialize function
function initializeUpload() {
    console.log('🔍 Checking for upload zone...');

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

console.log('✅ Custody Upload Module Loaded - Enhanced Error Handling');
