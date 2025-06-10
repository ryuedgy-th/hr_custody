/** @odoo-module **/

// Updated 2025-06-11 - Enhanced wizard ID detection

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
            console.log('📡 Starting direct RPC upload...');
            
            // Prepare data for RPC call
            const imagesData = this.selectedFiles
                .filter(file => file.dataUrl)
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    data: file.dataUrl,
                    description: file.description || '',
                    id: file.id
                }));

            // Get wizard record ID from the current page
            const wizardId = this.getWizardId();
            if (!wizardId) {
                throw new Error('Could not find wizard ID');
            }

            console.log(`📡 Uploading ${imagesData.length} files via RPC to wizard ${wizardId}...`);

            // Use Odoo RPC to update wizard and trigger upload
            const rpcData = {
                model: 'custody.image.upload.wizard',
                method: 'write',
                args: [[wizardId], {
                    'images_data': JSON.stringify(imagesData),
                    'total_files': this.selectedFiles.length,
                    'total_size_mb': (this.totalSize / (1024 * 1024)).toFixed(2)
                }],
                kwargs: {}
            };

            // Call Odoo RPC
            const result = await this.callOdooRPC('/web/dataset/call_kw', rpcData);
            console.log('✅ Wizard updated via RPC');

            // Now trigger the upload action
            const uploadData = {
                model: 'custody.image.upload.wizard',
                method: 'action_upload_images',
                args: [[wizardId]],
                kwargs: {}
            };

            const uploadResult = await this.callOdooRPC('/web/dataset/call_kw', uploadData);
            console.log('✅ Upload completed:', uploadResult);

            // Handle the result
            if (uploadResult && uploadResult.type === 'ir.actions.client') {
                // Show success notification
                this.showNotification(uploadResult.params);
                
                // Refresh the form or close dialog
                window.location.reload();
            }

        } catch (error) {
            console.error('❌ Upload failed:', error);
            alert(`Upload failed: ${error.message}`);
        }
    }

    getWizardId() {
        console.log('🔍 Searching for wizard ID...');
        
        // Method 1: Check URL parameters
        const url = window.location.href;
        console.log('🔍 Current URL:', url);
        
        let match = url.match(/id=(\d+)/);
        if (match) {
            console.log('✅ Found wizard ID in URL:', match[1]);
            return parseInt(match[1]);
        }
        
        // Method 2: Check for data attributes on modal/dialog
        const modal = document.querySelector('.modal') || document.querySelector('.o_dialog');
        if (modal) {
            const recordId = modal.getAttribute('data-record-id') || 
                           modal.getAttribute('data-id') ||
                           modal.querySelector('[data-record-id]')?.getAttribute('data-record-id');
            if (recordId) {
                console.log('✅ Found wizard ID in modal:', recordId);
                return parseInt(recordId);
            }
        }
        
        // Method 3: Check form data attributes
        const form = document.querySelector('form');
        if (form) {
            const formId = form.getAttribute('data-record-id') || 
                          form.getAttribute('data-id') ||
                          form.dataset.recordId ||
                          form.dataset.id;
            if (formId) {
                console.log('✅ Found wizard ID in form:', formId);
                return parseInt(formId);
            }
        }
        
        // Method 4: Check hidden inputs
        const hiddenId = document.querySelector('input[name="id"]')?.value ||
                        document.querySelector('input[type="hidden"][value*="custody.image.upload.wizard"]')?.nextElementSibling?.value;
        if (hiddenId && !isNaN(hiddenId)) {
            console.log('✅ Found wizard ID in hidden input:', hiddenId);
            return parseInt(hiddenId);
        }
        
        // Method 5: Extract from action context (Odoo specific)
        try {
            const scripts = document.querySelectorAll('script');
            for (const script of scripts) {
                const content = script.textContent || '';
                if (content.includes('custody.image.upload.wizard')) {
                    const idMatch = content.match(/"res_id":\s*(\d+)/) || 
                                   content.match(/"active_id":\s*(\d+)/) ||
                                   content.match(/wizard.*?(\d+)/);
                    if (idMatch) {
                        console.log('✅ Found wizard ID in script:', idMatch[1]);
                        return parseInt(idMatch[1]);
                    }
                }
            }
        } catch (e) {
            console.log('⚠️ Error searching scripts:', e);
        }
        
        // Method 6: Use Odoo web client context (if available)
        if (window.odoo && window.odoo.define) {
            try {
                // Try to access current action from Odoo web client
                const webClient = document.querySelector('.o_web_client');
                if (webClient && webClient.__owl__) {
                    const context = webClient.__owl__.ctx || {};
                    if (context.active_id) {
                        console.log('✅ Found wizard ID in Owl context:', context.active_id);
                        return parseInt(context.active_id);
                    }
                }
            } catch (e) {
                console.log('⚠️ Error accessing Owl context:', e);
            }
        }
        
        // Method 7: Try to find any number that looks like a record ID
        const bodyText = document.body.innerHTML;
        const possibleIds = bodyText.match(/\b\d{1,6}\b/g);
        if (possibleIds) {
            // Filter out obvious non-IDs (like years, small numbers, etc.)
            const candidateIds = possibleIds
                .map(id => parseInt(id))
                .filter(id => id > 10 && id < 999999)
                .filter((id, index, arr) => arr.indexOf(id) === index); // unique
                
            if (candidateIds.length === 1) {
                console.log('✅ Found candidate wizard ID:', candidateIds[0]);
                return candidateIds[0];
            } else if (candidateIds.length > 1) {
                console.log('⚠️ Multiple candidate IDs found:', candidateIds);
                // Return the most likely one (usually the largest reasonable ID)
                const likelyId = candidateIds.sort((a, b) => b - a)[0];
                console.log('✅ Using most likely ID:', likelyId);
                return likelyId;
            }
        }
        
        console.error('❌ Could not determine wizard ID with any method');
        console.log('🔍 Available elements for debugging:');
        console.log('- Modal:', !!modal);
        console.log('- Form:', !!form);
        console.log('- Hidden inputs:', document.querySelectorAll('input[type="hidden"]').length);
        console.log('- Scripts with wizard:', Array.from(document.querySelectorAll('script')).filter(s => s.textContent.includes('wizard')).length);
        
        return null;
    }

    async callOdooRPC(url, data) {
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

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error.message || 'RPC call failed');
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

console.log('✅ Custody Upload Module Loaded - Enhanced Wizard ID Detection');
