/** @odoo-module **/

/**
 * Modern Custody Upload Manager - Odoo 18 Standards
 * Enhanced field detection with modern service patterns
 */
class CustodyUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB per file
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB total
        this.maxFiles = 20;
        this.allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        
        // Debug mode - can be toggled via console
        this.debugMode = false;
        
        // Services will be set up when available
        this.servicesReady = false;
        this.setupServices();
    }

    /**
     * Setup Odoo 18 services with fallback
     */
    setupServices() {
        try {
            // Try to use modern Odoo 18 services
            if (typeof useService !== 'undefined') {
                this.orm = useService("orm");
                this.notification = useService("notification");
                this.rpc = useService("rpc");
                this.servicesReady = true;
                this.log("✅ Modern Odoo 18 services initialized");
            } else {
                this.setupLegacyServices();
            }
        } catch (error) {
            this.log("⚠️ Services not available, using legacy mode");
            this.setupLegacyServices();
        }
    }

    /**
     * Fallback to legacy methods when services unavailable
     */
    setupLegacyServices() {
        this.servicesReady = false;
        this.orm = null;
        this.notification = null;
        this.rpc = window.odoo?.rpc || null;
        this.log("📦 Using legacy service mode");
    }

    /**
     * Smart logging with debug mode
     */
    log(message, data = null) {
        if (this.debugMode) {
            console.log(`🔍 [CustodyUpload] ${message}`, data || '');
        }
    }

    /**
     * Always log errors
     */
    error(message, data = null) {
        console.error(`❌ [CustodyUpload] ${message}`, data || '');
    }

    /**
     * Initialize upload functionality
     */
    init() {
        this.log('🚀 Initializing Modern Custody Upload Manager...');
        try {
            this.setupEventListeners();
            this.updateDisplay();
            this.log('✅ Initialization completed successfully');
        } catch (error) {
            this.error('Initialization failed:', error);
        }
    }

    /**
     * Setup event listeners for file handling
     */
    setupEventListeners() {
        const uploadZone = this.findUploadZone();
        const fileInput = document.querySelector('#file_input');
        const browseBtn = document.querySelector('#browse_files_btn');

        if (!uploadZone || !fileInput) {
            this.error('⚠️ Required upload elements not found');
            return;
        }

        this.setupDragAndDrop(uploadZone);
        this.setupFileInput(fileInput);
        if (browseBtn) {
            this.setupBrowseButton(browseBtn, fileInput);
        }

        this.log('✅ Event listeners configured');
    }

    /**
     * Enhanced upload zone detection
     */
    findUploadZone() {
        const selectors = [
            '#custody_multiple_upload_zone',
            '.custody-upload-zone',
            '[data-upload-zone="custody"]',
            '.o_file_upload_zone'
        ];

        for (const selector of selectors) {
            const element = document.querySelector(selector);
            if (element) {
                this.log(`✅ Found upload zone: ${selector}`);
                return element;
            }
        }
        
        this.log('⚠️ No upload zone found');
        return null;
    }

    /**
     * Drag and drop functionality
     */
    setupDragAndDrop(uploadZone) {
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
    }

    /**
     * File input change handler
     */
    setupFileInput(fileInput) {
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files);
            e.target.value = '';
        });
    }

    /**
     * Browse button handler
     */
    setupBrowseButton(browseBtn, fileInput) {
        browseBtn.addEventListener('click', (e) => {
            e.preventDefault();
            fileInput.click();
        });
    }

    /**
     * Process selected files
     */
    handleFiles(files) {
        this.log(`📂 Processing ${files.length} files`);

        for (const file of files) {
            if (this.validateFile(file)) {
                this.addFile(file);
            }
        }

        this.renderPreviews();
        this.updateDisplay();
        this.updateImagesDataField(); // 🔧 FIXED: Correct method name
    }

    /**
     * Enhanced file validation
     */
    validateFile(file) {
        if (!this.allowedTypes.includes(file.type)) {
            this.showError(`File type not supported: ${file.name}. Allowed: JPG, PNG, GIF, WebP, BMP`);
            return false;
        }

        if (file.size > this.maxFileSize) {
            this.showError(`File too large: ${file.name} (max ${this.formatFileSize(this.maxFileSize)})`);
            return false;
        }

        if (this.selectedFiles.length >= this.maxFiles) {
            this.showError(`Maximum ${this.maxFiles} files allowed`);
            return false;
        }

        if (this.totalSize + file.size > this.maxTotalSize) {
            this.showError(`Total size would exceed ${this.formatFileSize(this.maxTotalSize)} limit`);
            return false;
        }

        return true;
    }

    /**
     * Add file to selection
     */
    addFile(file) {
        const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
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

        this.log(`✅ File added: ${file.name} (${this.formatFileSize(file.size)})`);
    }

    /**
     * Generate file preview
     */
    generatePreview(fileData) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            fileData.dataUrl = e.target.result;
            this.renderPreviews();
            setTimeout(() => this.updateImagesDataField(), 100); // 🔧 FIXED: Correct method name
        };

        reader.onerror = () => {
            this.error(`❌ Failed to read file: ${fileData.filename}`);
        };

        reader.readAsDataURL(fileData.file);
    }

    /**
     * Render file previews
     */
    renderPreviews() {
        this.log(`🖼️ Rendering ${this.selectedFiles.length} previews`);

        const previewContainer = document.getElementById('selected_files_preview');
        const filesList = document.getElementById('files_list');

        if (!previewContainer || !filesList) {
            this.error('⚠️ Preview containers not found');
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
    }

    /**
     * Update display information
     */
    updateDisplay() {
        const totalFiles = this.selectedFiles.length;
        const totalSizeMB = (this.totalSize / (1024 * 1024)).toFixed(2);
        
        this.log(`📊 Display updated: ${totalFiles} files, ${totalSizeMB}MB`);
        
        // Update Odoo field widgets
        this.updateOdooField('total_files', totalFiles);
        this.updateOdooField('total_size_mb', totalSizeMB);
    }

    /**
     * Update individual Odoo field widget
     */
    updateOdooField(fieldName, value) {
        const fieldWidget = document.querySelector(`div[name="${fieldName}"] span`);
        if (fieldWidget) {
            fieldWidget.textContent = value;
            this.log(`✅ Updated field ${fieldName}: ${value}`);
        }
    }

    /**
     * 🎯 ENHANCED: Smart images_data field detection with multiple strategies
     */
    findImagesDataField() {
        // Strategy 1: Direct selectors
        const directSelectors = [
            'input[name="images_data"]',
            'field[name="images_data"] input',
            'div[name="images_data"] input',
            '.o_field_widget[name="images_data"] input',
            '[data-field-name="images_data"] input',
            'input[data-field="images_data"]',
            '.o_field_text[name="images_data"] textarea',
            'textarea[name="images_data"]'
        ];

        for (const selector of directSelectors) {
            const field = document.querySelector(selector);
            if (field) {
                this.log(`✅ Found images_data field via direct selector: ${selector}`);
                return field;
            }
        }

        // Strategy 2: Iterate through all inputs
        const allInputs = document.querySelectorAll('input, textarea');
        for (const input of allInputs) {
            if (input.name === 'images_data' || 
                input.getAttribute('data-field') === 'images_data' ||
                input.getAttribute('data-field-name') === 'images_data') {
                this.log('✅ Found images_data field via iteration');
                return input;
            }
        }

        // Strategy 3: Look in form containers
        const forms = document.querySelectorAll('form, .o_form_view');
        for (const form of forms) {
            const field = form.querySelector('[name="images_data"], [data-field="images_data"]');
            if (field) {
                this.log('✅ Found images_data field in form container');
                return field;
            }
        }

        this.log('❌ images_data field not found with any strategy');
        return null;
    }

    /**
     * 🎯 ENHANCED: Update images_data field with smart detection and fallback
     */
    updateImagesDataField() {
        const imagesDataField = this.findImagesDataField();
        
        const imagesData = this.selectedFiles
            .filter(file => file.dataUrl)
            .map(file => ({
                filename: file.filename,
                size: file.size,
                type: file.type,
                description: file.description || '',
                data: file.dataUrl
            }));

        const jsonData = JSON.stringify(imagesData);

        if (imagesDataField) {
            imagesDataField.value = jsonData;
            this.log('📋 Updated images_data field successfully', {
                fileCount: imagesData.length,
                fieldFound: true,
                dataLength: jsonData.length
            });
        } else {
            // 🎯 ENHANCED: Fallback system with better organization
            if (!window.custodyUploadData) {
                window.custodyUploadData = {};
            }
            
            window.custodyUploadData.images_data = jsonData;
            window.custodyUploadData.timestamp = Date.now();
            window.custodyUploadData.fileCount = imagesData.length;
            
            this.log('📋 Stored in fallback system', {
                fileCount: imagesData.length,
                fallbackStorage: true,
                dataLength: jsonData.length
            });
        }
    }

    /**
     * Remove file from selection
     */
    removeFile(fileId) {
        this.log(`🗑️ Removing file: ${fileId}`);
        
        const fileIndex = this.selectedFiles.findIndex(f => f.id === fileId);
        if (fileIndex !== -1) {
            this.totalSize -= this.selectedFiles[fileIndex].size;
            this.selectedFiles.splice(fileIndex, 1);
            this.renderPreviews();
            this.updateDisplay();
            this.updateImagesDataField(); // 🔧 FIXED: Correct method name
        }
    }

    /**
     * Update file description
     */
    updateFileDescription(fileId, description) {
        const file = this.selectedFiles.find(f => f.id === fileId);
        if (file) {
            file.description = description;
            this.updateImagesDataField();
            this.log(`📝 Updated description for: ${file.filename}`);
        }
    }

    /**
     * Format file size for display
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 🎯 ENHANCED: Modern error display with notification service
     */
    showError(message) {
        this.error(`Validation Error: ${message}`);
        
        // Try modern notification service first
        if (this.servicesReady && this.notification) {
            try {
                this.notification.add({
                    title: "Upload Error",
                    message: message,
                    type: "danger",
                    sticky: false
                });
                return;
            } catch (error) {
                this.log('⚠️ Modern notification failed, using fallback');
            }
        }
        
        // Fallback to DOM notification
        this.showDOMError(message);
    }

    /**
     * Fallback DOM error display
     */
    showDOMError(message) {
        let errorContainer = document.getElementById('upload_errors');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.id = 'upload_errors';
            errorContainer.style.marginTop = '10px';
            
            const uploadZone = this.findUploadZone();
            if (uploadZone) {
                uploadZone.appendChild(errorContainer);
            }
        }
        
        errorContainer.innerHTML = `<div class="alert alert-danger" role="alert">${message}</div>`;
        setTimeout(() => {
            errorContainer.innerHTML = '';
        }, 5000);
    }

    /**
     * 🎯 ENHANCED: Modern upload process with ORM service
     */
    async startUpload() {
        const readyFiles = this.selectedFiles.filter(file => file.dataUrl);
        
        if (this.selectedFiles.length === 0) {
            this.showError('No images selected for upload');
            return false;
        }

        if (readyFiles.length === 0) {
            this.showError('Images are still being processed. Please wait...');
            return false;
        }

        if (readyFiles.length !== this.selectedFiles.length) {
            this.showError(`${this.selectedFiles.length - readyFiles.length} images still processing. Please wait...`);
            return false;
        }

        this.log('🚀 Starting modern upload process', {
            selectedFiles: this.selectedFiles.length,
            readyFiles: readyFiles.length,
            useModernServices: this.servicesReady
        });

        // Update field data before upload
        this.updateImagesDataField();
        
        // Validate data preparation
        const imagesDataField = this.findImagesDataField();
        const hasFieldData = imagesDataField && imagesDataField.value;
        const hasFallbackData = window.custodyUploadData && window.custodyUploadData.images_data;
        
        if (!hasFieldData && !hasFallbackData) {
            this.showError('Failed to prepare upload data. Please try again.');
            return false;
        }

        // 🎯 NEW: Copy fallback data to field if needed
        if (!hasFieldData && hasFallbackData && imagesDataField) {
            imagesDataField.value = window.custodyUploadData.images_data;
            this.log('✅ Copied fallback data to field');
        }

        // Try modern upload first, then fallback
        if (this.servicesReady) {
            return await this.performModernUpload();
        } else {
            return this.performLegacyUpload();
        }
    }

    /**
     * 🎯 NEW: Modern upload using ORM service
     */
    async performModernUpload() {
        try {
            const wizardId = this.getWizardId();
            if (!wizardId) {
                throw new Error('Could not detect wizard ID');
            }

            this.log(`📡 Using modern ORM service for wizard ${wizardId}`);

            const imagesData = this.selectedFiles
                .filter(file => file.dataUrl)
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    description: file.description || '',
                    data: file.dataUrl
                }));

            // Step 1: Update wizard data
            await this.orm.write('custody.image.upload.wizard', [wizardId], {
                'images_data': JSON.stringify(imagesData),
                'total_files': this.selectedFiles.length,
                'total_size_mb': parseFloat((this.totalSize / (1024 * 1024)).toFixed(2))
            });

            this.log('✅ Step 1: Wizard data updated via ORM');

            // Step 2: Trigger upload action
            const result = await this.orm.call(
                'custody.image.upload.wizard', 
                'action_upload_images', 
                [wizardId]
            );

            this.log('✅ Step 2: Upload action completed', result);

            // Handle success
            if (this.notification) {
                this.notification.add({
                    title: "Upload Successful!",
                    message: `Successfully uploaded ${imagesData.length} images`,
                    type: "success"
                });
            }

            setTimeout(() => window.location.reload(), 1000);
            return true;

        } catch (error) {
            this.error('Modern upload failed:', error);
            this.showError(`Upload failed: ${error.message || 'Unknown error'}`);
            return false;
        }
    }

    /**
     * Fallback to legacy upload method
     */
    performLegacyUpload() {
        this.log('📦 Using legacy upload method');
        // Let Odoo wizard handle the upload with the prepared data
        return true;
    }

    /**
     * Extract wizard ID from URL
     */
    getWizardId() {
        const url = window.location.href;
        const match = url.match(/\/(\d+)(?:\?|$|\/)/);
        if (match) {
            const wizardId = parseInt(match[1]);
            this.log(`✅ Detected wizard ID: ${wizardId}`);
            return wizardId;
        }
        
        this.log('❌ Could not extract wizard ID from URL');
        return null;
    }

    /**
     * Get files data for external use
     */
    getFilesData() {
        return this.selectedFiles.map(file => ({
            filename: file.filename,
            size: file.size,
            type: file.type,
            description: file.description,
            dataUrl: file.dataUrl
        }));
    }

    /**
     * 🔧 Debug helper methods
     */
    enableDebug() {
        this.debugMode = true;
        console.log('🐛 Debug mode enabled for Custody Upload');
    }

    disableDebug() {
        this.debugMode = false;
        console.log('🚫 Debug mode disabled');
    }

    getDebugInfo() {
        const imagesDataField = this.findImagesDataField();
        return {
            selectedFiles: this.selectedFiles.length,
            readyFiles: this.selectedFiles.filter(f => f.dataUrl).length,
            totalSize: this.formatFileSize(this.totalSize),
            debugMode: this.debugMode,
            servicesReady: this.servicesReady,
            fieldFound: !!imagesDataField,
            imagesDataLength: imagesDataField ? imagesDataField.value.length : 0,
            fallbackDataExists: !!(window.custodyUploadData && window.custodyUploadData.images_data),
            wizardId: this.getWizardId(),
            version: '2.0.1-hotfix'
        };
    }
}

/**
 * Smart initialization with multiple strategies
 */
function initializeUpload() {
    try {
        const uploadZone = document.querySelector('#custody_multiple_upload_zone') || 
                          document.querySelector('.custody-upload-zone');

        if (uploadZone) {
            if (!window.custodyUploadManager) {
                const manager = new CustodyUploadManager();
                window.custodyUploadManager = manager;
                manager.init();
                
                // 🔧 Global debug helpers
                window.enableCustodyDebug = () => manager.enableDebug();
                window.disableCustodyDebug = () => manager.disableDebug();
                window.getCustodyDebugInfo = () => manager.getDebugInfo();
                
                console.log('✅ Modern Custody Upload Manager initialized');
            }
        } else {
            setTimeout(initializeUpload, 1000);
        }
    } catch (error) {
        console.error('❌ Upload initialization error:', error);
        setTimeout(initializeUpload, 2000);
    }
}

// Multiple initialization strategies for reliability
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpload);
} else {
    initializeUpload();
}

window.addEventListener('load', () => {
    setTimeout(initializeUpload, 1000);
});

setTimeout(initializeUpload, 2000);

// Production info
console.log('✅ Custody Upload Module v2.0.1 - Hotfix (Method Name Corrections)');