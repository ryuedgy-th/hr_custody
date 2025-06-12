/** @odoo-module **/

/**
 * Modern Custody Upload Manager - Enhanced Debug Version
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
        
        // Enhanced debug mode - default ON for troubleshooting
        this.debugMode = true;
        
        // Services will be set up when available
        this.servicesReady = false;
        this.setupServices();
    }

    setupServices() {
        try {
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

    setupLegacyServices() {
        this.servicesReady = false;
        this.orm = null;
        this.notification = null;
        this.rpc = window.odoo?.rpc || null;
        this.log("📦 Using legacy service mode");
    }

    log(message, data = null) {
        if (this.debugMode) {
            console.log(`🔍 [CustodyUpload] ${message}`, data || '');
        }
    }

    error(message, data = null) {
        console.error(`❌ [CustodyUpload] ${message}`, data || '');
    }

    init() {
        this.log('🚀 Initializing Modern Custody Upload Manager...');
        try {
            this.setupEventListeners();
            this.updateDisplay();
            this.logDOMState();
            this.log('✅ Initialization completed successfully');
        } catch (error) {
            this.error('Initialization failed:', error);
        }
    }

    logDOMState() {
        this.log('📋 Current DOM State Check:');
        
        const possibleFields = document.querySelectorAll('input, textarea, select');
        this.log(`Found ${possibleFields.length} form elements`);
        
        const imageFields = Array.from(possibleFields).filter(el => 
            el.name && el.name.includes('images') || 
            el.getAttribute('data-field') && el.getAttribute('data-field').includes('images')
        );
        
        this.log('Images-related fields:', imageFields);
        
        const forms = document.querySelectorAll('form, .o_form_view');
        this.log(`Found ${forms.length} forms`);
        
        const uploadZone = this.findUploadZone();
        this.log('Upload zone found:', !!uploadZone);
    }

    setupEventListeners() {
        const uploadZone = this.findUploadZone();
        const fileInput = document.querySelector('#file_input');
        const browseBtn = document.querySelector('#browse_files_btn');

        if (!uploadZone || !fileInput) {
            this.error('⚠️ Required upload elements not found');
            this.logDOMState();
            return;
        }

        this.setupDragAndDrop(uploadZone);
        this.setupFileInput(fileInput);
        if (browseBtn) {
            this.setupBrowseButton(browseBtn, fileInput);
        }

        this.log('✅ Event listeners configured');
    }

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

    setupFileInput(fileInput) {
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.log(`📁 File input changed, files: ${files.length}`);
            this.handleFiles(files);
            e.target.value = '';
        });
    }

    setupBrowseButton(browseBtn, fileInput) {
        browseBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.log('🖱️ Browse button clicked');
            fileInput.click();
        });
    }

    handleFiles(files) {
        this.log(`📂 Processing ${files.length} files`);

        for (const file of files) {
            this.log(`🔍 Validating file: ${file.name} (${file.type}, ${file.size} bytes)`);
            if (this.validateFile(file)) {
                this.addFile(file);
            }
        }

        this.renderPreviews();
        this.updateDisplay();
        
        this.log('🔄 About to update images_data field...');
        this.updateImagesDataField();
        
        setTimeout(() => this.verifyDataUpdate(), 100);
    }

    verifyDataUpdate() {
        this.log('🔍 Verifying data update...');
        
        const imagesDataField = this.findImagesDataField();
        const hasFallbackData = window.custodyUploadData && window.custodyUploadData.images_data;
        
        this.log('Field verification:', {
            fieldFound: !!imagesDataField,
            fieldValue: imagesDataField ? imagesDataField.value.length : 0,
            fallbackData: hasFallbackData,
            fallbackLength: hasFallbackData ? window.custodyUploadData.images_data.length : 0,
            selectedFiles: this.selectedFiles.length,
            readyFiles: this.selectedFiles.filter(f => f.dataUrl).length
        });
    }

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

        this.log(`✅ File validation passed: ${file.name}`);
        return true;
    }

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

    generatePreview(fileData) {
        this.log(`📸 Generating preview for: ${fileData.filename}`);
        
        const reader = new FileReader();
        
        reader.onload = (e) => {
            fileData.dataUrl = e.target.result;
            this.log(`✅ Preview generated for: ${fileData.filename} (${e.target.result.length} chars)`);
            this.renderPreviews();
            setTimeout(() => {
                this.updateImagesDataField();
                this.verifyDataUpdate();
            }, 100);
        };

        reader.onerror = () => {
            this.error(`❌ Failed to read file: ${fileData.filename}`);
        };

        reader.readAsDataURL(fileData.file);
    }

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

    updateDisplay() {
        const totalFiles = this.selectedFiles.length;
        const totalSizeMB = (this.totalSize / (1024 * 1024)).toFixed(2);
        
        this.log(`📊 Display updated: ${totalFiles} files, ${totalSizeMB}MB`);
        
        this.updateOdooField('total_files', totalFiles);
        this.updateOdooField('total_size_mb', totalSizeMB);
    }

    updateOdooField(fieldName, value) {
        const fieldWidget = document.querySelector(`div[name="${fieldName}"] span`);
        if (fieldWidget) {
            fieldWidget.textContent = value;
            this.log(`✅ Updated field ${fieldName}: ${value}`);
        }
    }

    findImagesDataField() {
        this.log('🔍 Starting enhanced field detection...');
        
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

        this.log('🔍 Strategy 2: Iterating through all inputs...');
        const allInputs = document.querySelectorAll('input, textarea');
        this.log(`Found ${allInputs.length} total input/textarea elements`);
        
        for (const input of allInputs) {
            if (input.name === 'images_data' || 
                input.getAttribute('data-field') === 'images_data' ||
                input.getAttribute('data-field-name') === 'images_data') {
                this.log('✅ Found images_data field via iteration');
                return input;
            }
        }

        this.log('🔍 Strategy 3: Looking in form containers...');
        const forms = document.querySelectorAll('form, .o_form_view');
        this.log(`Found ${forms.length} form containers`);
        
        for (const form of forms) {
            const field = form.querySelector('[name="images_data"], [data-field="images_data"]');
            if (field) {
                this.log('✅ Found images_data field in form container');
                return field;
            }
        }

        this.log('🔍 Strategy 4: Field not found, attempting to create fallback...');
        return this.createFallbackField();
    }

    createFallbackField() {
        this.log('🛠️ Creating fallback images_data field...');
        
        try {
            const uploadZone = this.findUploadZone();
            const forms = document.querySelectorAll('form, .o_form_view');
            const parentContainer = uploadZone || forms[0] || document.body;
            
            const fallbackField = document.createElement('input');
            fallbackField.type = 'hidden';
            fallbackField.name = 'images_data';
            fallbackField.id = 'custody_images_data_fallback';
            fallbackField.value = '';
            
            parentContainer.appendChild(fallbackField);
            
            this.log('✅ Created fallback field successfully');
            return fallbackField;
            
        } catch (error) {
            this.error('❌ Failed to create fallback field:', error);
            return null;
        }
    }

    updateImagesDataField() {
        this.log('🔄 Starting images_data field update...');
        
        const imagesDataField = this.findImagesDataField();
        
        const readyFiles = this.selectedFiles.filter(file => file.dataUrl);
        this.log(`📊 Ready files for processing: ${readyFiles.length}/${this.selectedFiles.length}`);
        
        const imagesData = readyFiles.map(file => ({
            filename: file.filename,
            size: file.size,
            type: file.type,
            description: file.description || '',
            data: file.dataUrl
        }));

        const jsonData = JSON.stringify(imagesData);
        this.log(`📋 Generated JSON data: ${jsonData.length} characters`);

        if (imagesDataField) {
            imagesDataField.value = jsonData;
            this.log('✅ Updated images_data field successfully', {
                fileCount: imagesData.length,
                fieldFound: true,
                dataLength: jsonData.length,
                fieldElement: imagesDataField.tagName + '#' + (imagesDataField.id || 'no-id')
            });
        } else {
            this.log('⚠️ Field not found, using fallback storage...');
        }
        
        if (!window.custodyUploadData) {
            window.custodyUploadData = {};
        }
        
        window.custodyUploadData.images_data = jsonData;
        window.custodyUploadData.timestamp = Date.now();
        window.custodyUploadData.fileCount = imagesData.length;
        
        this.log('📋 Updated fallback storage', {
            fileCount: imagesData.length,
            fallbackStorage: true,
            dataLength: jsonData.length
        });
    }

    removeFile(fileId) {
        this.log(`🗑️ Removing file: ${fileId}`);
        
        const fileIndex = this.selectedFiles.findIndex(f => f.id === fileId);
        if (fileIndex !== -1) {
            this.totalSize -= this.selectedFiles[fileIndex].size;
            this.selectedFiles.splice(fileIndex, 1);
            this.renderPreviews();
            this.updateDisplay();
            this.updateImagesDataField();
        }
    }

    updateFileDescription(fileId, description) {
        const file = this.selectedFiles.find(f => f.id === fileId);
        if (file) {
            file.description = description;
            this.updateImagesDataField();
            this.log(`📝 Updated description for: ${file.filename}`);
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
        this.error(`Validation Error: ${message}`);
        
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
        
        this.showDOMError(message);
    }

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

    async startUpload() {
        this.log('🚀 Starting upload process...');
        
        const readyFiles = this.selectedFiles.filter(file => file.dataUrl);
        
        this.log('📊 Upload validation:', {
            totalSelected: this.selectedFiles.length,
            readyFiles: readyFiles.length,
            servicesReady: this.servicesReady
        });
        
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

        this.log('🔍 Pre-upload data verification...');
        this.updateImagesDataField();
        this.verifyDataUpdate();
        
        const imagesDataField = this.findImagesDataField();
        const hasFieldData = imagesDataField && imagesDataField.value && imagesDataField.value.length > 0;
        const hasFallbackData = window.custodyUploadData && window.custodyUploadData.images_data && window.custodyUploadData.images_data.length > 0;
        
        this.log('📋 Data preparation check:', {
            fieldFound: !!imagesDataField,
            hasFieldData: hasFieldData,
            fieldDataLength: hasFieldData ? imagesDataField.value.length : 0,
            hasFallbackData: hasFallbackData,
            fallbackDataLength: hasFallbackData ? window.custodyUploadData.images_data.length : 0
        });
        
        if (!hasFieldData && !hasFallbackData) {
            this.error('❌ No data prepared for upload');
            this.showError('Failed to prepare upload data. Please try selecting files again.');
            return false;
        }

        if (!hasFieldData && hasFallbackData && imagesDataField) {
            imagesDataField.value = window.custodyUploadData.images_data;
            this.log('✅ Copied fallback data to field');
        }

        if (this.servicesReady) {
            return await this.performModernUpload();
        } else {
            return this.performLegacyUpload();
        }
    }

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

            this.log(`📤 Uploading data:`, {
                wizardId: wizardId,
                imageCount: imagesData.length,
                totalSize: this.totalSize,
                dataSize: JSON.stringify(imagesData).length
            });

            await this.orm.write('custody.image.upload.wizard', [wizardId], {
                'images_data': JSON.stringify(imagesData),
                'total_files': this.selectedFiles.length,
                'total_size_mb': parseFloat((this.totalSize / (1024 * 1024)).toFixed(2))
            });

            this.log('✅ Step 1: Wizard data updated via ORM');

            const result = await this.orm.call(
                'custody.image.upload.wizard', 
                'action_upload_images', 
                [wizardId]
            );

            this.log('✅ Step 2: Upload action completed', result);

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

    performLegacyUpload() {
        this.log('📦 Using legacy upload method');
        return true;
    }

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

    getFilesData() {
        return this.selectedFiles.map(file => ({
            filename: file.filename,
            size: file.size,
            type: file.type,
            description: file.description,
            dataUrl: file.dataUrl
        }));
    }

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
        const fieldValue = imagesDataField ? imagesDataField.value : '';
        const fallbackData = window.custodyUploadData ? window.custodyUploadData.images_data : '';
        
        return {
            selectedFiles: this.selectedFiles.length,
            readyFiles: this.selectedFiles.filter(f => f.dataUrl).length,
            totalSize: this.formatFileSize(this.totalSize),
            debugMode: this.debugMode,
            servicesReady: this.servicesReady,
            fieldFound: !!imagesDataField,
            fieldDataLength: fieldValue.length,
            fallbackDataExists: !!fallbackData,
            fallbackDataLength: fallbackData.length,
            wizardId: this.getWizardId(),
            version: '2.0.2-enhanced-debug',
            url: window.location.href,
            fieldDetails: imagesDataField ? {
                tagName: imagesDataField.tagName,
                name: imagesDataField.name,
                id: imagesDataField.id
            } : null
        };
    }

    // 🔧 Manual test injection for troubleshooting
    injectTestData() {
        this.log('🧪 Injecting test data for debugging...');
        
        const testData = [{
            filename: 'test-image.jpg',
            size: 12345,
            type: 'image/jpeg',
            description: 'Test image for debugging',
            data: 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwAA'
        }];
        
        // Update field directly
        const imagesDataField = this.findImagesDataField();
        if (imagesDataField) {
            imagesDataField.value = JSON.stringify(testData);
            this.log('✅ Test data injected to field');
        }
        
        // Update fallback storage
        if (!window.custodyUploadData) {
            window.custodyUploadData = {};
        }
        window.custodyUploadData.images_data = JSON.stringify(testData);
        
        this.log('🧪 Test data injected successfully');
        return testData;
    }
}

function initializeUpload() {
    try {
        const uploadZone = document.querySelector('#custody_multiple_upload_zone') || 
                          document.querySelector('.custody-upload-zone');

        if (uploadZone) {
            if (!window.custodyUploadManager) {
                const manager = new CustodyUploadManager();
                window.custodyUploadManager = manager;
                manager.init();
                
                // Enhanced debug helpers
                window.enableCustodyDebug = () => manager.enableDebug();
                window.disableCustodyDebug = () => manager.disableDebug();
                window.getCustodyDebugInfo = () => manager.getDebugInfo();
                window.injectCustodyTestData = () => manager.injectTestData();
                
                console.log('✅ Enhanced Debug Custody Upload Manager initialized');
            }
        } else {
            setTimeout(initializeUpload, 1000);
        }
    } catch (error) {
        console.error('❌ Upload initialization error:', error);
        setTimeout(initializeUpload, 2000);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeUpload);
} else {
    initializeUpload();
}

window.addEventListener('load', () => {
    setTimeout(initializeUpload, 1000);
});

setTimeout(initializeUpload, 2000);

console.log('✅ Custody Upload Module v2.0.2 - Enhanced Debug Version (Auto Fallback Field Creation)');