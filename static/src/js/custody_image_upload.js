/** @odoo-module **/

console.log('📦 Loading Custody Upload Module...');

class CustodyUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB per file
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB total
        this.allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        console.log('📋 Upload Manager initialized');
    }

    init() {
        console.log('🚀 Initializing upload functionality...');
        this.setupEventListeners();
        this.renderPreviews();
        this.updateDisplay();
    }

    setupEventListeners() {
        const uploadZone = document.querySelector('#custody_multiple_upload_zone, .custody-upload-zone');
        const fileInput = document.querySelector('#file_input'); // แก้ไข selector

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

    showError(message) {
        console.error('❌ Error:', message);
        
        // สร้าง error display ถ้ายังไม่มี
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

    // เพิ่มฟังก์ชันสำหรับส่งข้อมูลกลับไปที่ Odoo
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

// Initialize function with better error handling
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

// Multiple initialization strategies with error handling
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

console.log('✅ Custody Upload Module Loaded - Fixed Selectors & Error Handling');