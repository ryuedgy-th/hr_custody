/** @odoo-module **/

// Production-ready version with enhanced field detection
class CustodyUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB per file
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB total
        this.allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        
        // Debug mode สามารถ toggle ได้
        this.debugMode = false; // เปลี่ยนเป็น true เมื่อต้องการ debug
    }

    log(message, data = null) {
        if (this.debugMode) {
            console.log(message, data || '');
        }
    }

    error(message, data = null) {
        // Error logs ควรเก็บไว้เสมอ
        console.error(message, data || '');
    }

    init() {
        this.log('🚀 Initializing upload functionality...');
        this.setupEventListeners();
        this.updateDisplay();
    }

    setupEventListeners() {
        const uploadZone = document.querySelector('#custody_multiple_upload_zone, .custody-upload-zone');
        const fileInput = document.querySelector('#file_input');
        const browseBtn = document.querySelector('#browse_files_btn');

        if (!uploadZone || !fileInput) {
            this.error('⚠️ Upload elements not found');
            return;
        }

        // Drag & Drop
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

        // Browse button
        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.preventDefault();
                fileInput.click();
            });
        }

        // File input change
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files);
            e.target.value = '';
        });

        this.log('✅ Event listeners setup complete');
    }

    handleFiles(files) {
        this.log('📂 Processing files', { count: files.length });

        for (const file of files) {
            if (this.validateFile(file)) {
                this.addFile(file);
            }
        }

        this.renderPreviews();
        this.updateDisplay();
        this.updateOdooFields();
    }

    validateFile(file) {
        if (!this.allowedTypes.includes(file.type)) {
            this.showError(`File type not allowed: ${file.name}. Supported: JPG, PNG, GIF, WebP, BMP`);
            return false;
        }

        if (file.size > this.maxFileSize) {
            this.showError(`File too large: ${file.name} (max 5MB per file)`);
            return false;
        }

        if (this.selectedFiles.length >= 20) {
            this.showError('Maximum 20 images allowed');
            return false;
        }

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

        this.log('✅ File added', { filename: file.name, size: file.size });
    }

    generatePreview(fileData) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            fileData.dataUrl = e.target.result;
            this.renderPreviews();
            // เรียก updateOdooFields ใน setTimeout เพื่อให้ DOM update เสร็จก่อน
            setTimeout(() => this.updateOdooFields(), 100);
        };

        reader.onerror = () => {
            this.error('❌ Error reading file', fileData.filename);
        };

        reader.readAsDataURL(fileData.file);
    }

    renderPreviews() {
        this.log('🖼️ Rendering previews', { count: this.selectedFiles.length });

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
        // Essential display updates only
        const totalFiles = this.selectedFiles.length;
        const totalSizeMB = (this.totalSize / (1024 * 1024)).toFixed(2);
        
        this.log('📊 Display updated', { files: totalFiles, totalSizeMB: totalSizeMB });
    }

    updateOdooFields() {
        // อัพเดท Odoo field widgets
        this.updateOdooField('total_files', this.selectedFiles.length);
        this.updateOdooField('total_size_mb', (this.totalSize / (1024 * 1024)).toFixed(2));
        
        // 🎯 สำคัญ: อัพเดท images_data field สำหรับ Odoo wizard
        this.updateImagesDataField();
    }

    updateOdooField(fieldName, value) {
        const fieldWidget = document.querySelector(`div[name="${fieldName}"] span`);
        if (fieldWidget) {
            fieldWidget.textContent = value;
            this.log(`✅ Updated Odoo field ${fieldName}`, value);
        }
    }

    findImagesDataField() {
        // ลองหา images_data field ด้วย selector หลายแบบ
        const selectors = [
            'input[name="images_data"]',
            'field[name="images_data"] input',
            'div[name="images_data"] input',
            '.o_field_widget[name="images_data"] input',
            '[data-field-name="images_data"] input',
            'input[data-field="images_data"]'
        ];

        for (const selector of selectors) {
            const field = document.querySelector(selector);
            if (field) {
                this.log(`✅ Found images_data field with selector: ${selector}`);
                return field;
            }
        }

        // ลองหาโดยการ iterate ผ่าน input fields
        const allInputs = document.querySelectorAll('input[type="text"], input[type="hidden"], input:not([type])');
        for (const input of allInputs) {
            if (input.name === 'images_data' || 
                input.getAttribute('data-field') === 'images_data' ||
                input.getAttribute('data-field-name') === 'images_data') {
                this.log('✅ Found images_data field by iteration');
                return input;
            }
        }

        return null;
    }

    updateImagesDataField() {
        // 🔧 ปรับปรุงการหา images_data field
        const imagesDataField = this.findImagesDataField();
        
        if (imagesDataField) {
            const imagesData = this.selectedFiles
                .filter(file => file.dataUrl) // เฉพาะไฟล์ที่มี dataUrl แล้ว
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    description: file.description || '',
                    data: file.dataUrl // ใช้ dataUrl ที่มี format 'data:image/jpeg;base64,xxx'
                }));
            
            imagesDataField.value = JSON.stringify(imagesData);
            this.log('📋 Updated images_data field', { 
                fileCount: imagesData.length,
                fieldFound: true,
                dataLength: imagesDataField.value.length
            });
        } else {
            this.error('❌ images_data field not found - tried all selectors');
            
            // 🔧 Fallback: เก็บข้อมูลใน window object
            if (!window.custodyUploadData) {
                window.custodyUploadData = {};
            }
            
            const imagesData = this.selectedFiles
                .filter(file => file.dataUrl)
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    description: file.description || '',
                    data: file.dataUrl
                }));
            
            window.custodyUploadData.images_data = JSON.stringify(imagesData);
            this.log('📋 Stored images_data in window object as fallback', { 
                fileCount: imagesData.length 
            });
        }
    }

    removeFile(fileId) {
        this.log('🗑️ Removing file', fileId);
        
        const fileIndex = this.selectedFiles.findIndex(f => f.id == fileId);
        if (fileIndex !== -1) {
            this.totalSize -= this.selectedFiles[fileIndex].size;
            this.selectedFiles.splice(fileIndex, 1);
            this.renderPreviews();
            this.updateDisplay();
            this.updateOdooFields();
        }
    }

    updateFileDescription(fileId, description) {
        const file = this.selectedFiles.find(f => f.id == fileId);
        if (file) {
            file.description = description;
            this.updateImagesDataField(); // อัพเดทข้อมูลเมื่อมีการเปลี่ยน description
            this.log('📝 Updated description', { filename: file.filename });
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
        // User-facing errors ควรเก็บไว้
        this.error('❌ Validation Error:', message);
        
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

    // ฟังก์ชันสำหรับส่งข้อมูลไปยัง Odoo
    getFilesData() {
        return this.selectedFiles.map(file => ({
            filename: file.filename,
            size: file.size,
            type: file.type,
            description: file.description,
            dataUrl: file.dataUrl
        }));
    }

    // ฟังก์ชันสำหรับ Start Upload button
    startUpload() {
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
            this.showError(`${this.selectedFiles.length - readyFiles.length} images are still being processed. Please wait...`);
            return false;
        }

        this.log('🚀 Starting upload', { 
            selectedFiles: this.selectedFiles.length,
            readyFiles: readyFiles.length 
        });
        
        // อัพเดทข้อมูลครั้งสุดท้าย
        this.updateImagesDataField();
        
        // ตรวจสอบว่าข้อมูลถูกเก็บแล้ว (ใน field หรือ window object)
        const imagesDataField = this.findImagesDataField();
        const hasFieldData = imagesDataField && imagesDataField.value;
        const hasFallbackData = window.custodyUploadData && window.custodyUploadData.images_data;
        
        if (!hasFieldData && !hasFallbackData) {
            this.showError('Failed to prepare upload data. Please try again.');
            return false;
        }

        // 🔧 ถ้าใช้ fallback data ให้ copy ไปยัง field (ถ้าเจอ)
        if (!hasFieldData && hasFallbackData && imagesDataField) {
            imagesDataField.value = window.custodyUploadData.images_data;
            this.log('✅ Copied fallback data to field');
        }

        // ให้ Odoo wizard จัดการต่อ
        return true;
    }

    // 🔧 Debug Helper Methods (สำหรับ development)
    enableDebug() {
        this.debugMode = true;
        console.log('🐛 Debug mode enabled');
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
            fieldFound: !!imagesDataField,
            imagesDataLength: imagesDataField ? imagesDataField.value.length : 0,
            fallbackDataExists: !!(window.custodyUploadData && window.custodyUploadData.images_data),
            version: '1.2.0-production'
        };
    }
}

// Initialize function
function initializeUpload() {
    try {
        const uploadZone = document.querySelector('#custody_multiple_upload_zone') || 
                          document.querySelector('.custody-upload-zone');

        if (uploadZone) {
            if (!window.custodyUploadManager) {
                const manager = new CustodyUploadManager();
                window.custodyUploadManager = manager;
                manager.init();
                
                // 🔧 Debug helpers สำหรับ console
                window.enableCustodyDebug = () => manager.enableDebug();
                window.disableCustodyDebug = () => manager.disableDebug();
                window.getCustodyDebugInfo = () => manager.getDebugInfo();
            }
        } else {
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

setTimeout(initializeUpload, 2000);

// Production info
console.log('✅ Custody Upload Module Loaded - Production Version 1.2.0 (Enhanced Field Detection)');