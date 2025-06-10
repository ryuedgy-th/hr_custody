/** @odoo-module **/

import { Component, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * Multiple Image Upload Widget for Custody Images
 * แก้ไขปัญหา: useService ต้องใช้ใน OWL Component เท่านั้น
 */
export class CustodyMultipleImageUpload extends Component {
    static template = "hr_custody.CustodyMultipleImageUpload";

    setup() {
        // ⚠️ ลบการใช้ useService ออก เพราะจะเกิด error ถ้าไม่ได้อยู่ใน OWL context
        // this.orm = useService("orm");
        // this.notification = useService("notification");
        
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFiles = 20;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];

        onMounted(() => {
            this.initializeUploadZone();
        });

        onWillUnmount(() => {
            this.cleanup();
        });
    }

    initializeUploadZone() {
        const dropzone = document.querySelector('.upload-dropzone');
        const fileInput = document.getElementById('file_input');
        const browseBtn = document.getElementById('browse_files_btn');

        if (!dropzone || !fileInput || !browseBtn) {
            console.warn('Upload elements not found, retrying...');
            // Retry after a short delay
            setTimeout(() => this.initializeUploadZone(), 500);
            return;
        }

        console.log('Initializing upload zone with elements:', { dropzone, fileInput, browseBtn });

        // Setup drag and drop
        this.setupDragAndDrop(dropzone);
        
        // Setup file input
        this.setupFileInput(fileInput, browseBtn);
        
        // Setup browse button click
        this.setupBrowseButton(browseBtn, fileInput);
    }

    setupDragAndDrop(dropzone) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, this.preventDefaults.bind(this), false);
            document.body.addEventListener(eventName, this.preventDefaults.bind(this), false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add('dragover');
                console.log('Drag over detected');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove('dragover');
                console.log('Drag leave/drop detected');
            }, false);
        });

        // Handle dropped files
        dropzone.addEventListener('drop', this.handleDrop.bind(this), false);
        
        // Handle click to browse
        dropzone.addEventListener('click', (e) => {
            // Only trigger if clicked on dropzone itself, not on browse button
            if (e.target === dropzone || e.target.closest('.upload-content')) {
                const fileInput = document.getElementById('file_input');
                if (fileInput) fileInput.click();
            }
        });
    }

    setupFileInput(fileInput, browseBtn) {
        fileInput.addEventListener('change', (e) => {
            console.log('File input changed, files:', e.target.files);
            this.handleFiles(e.target.files);
        });
    }

    setupBrowseButton(browseBtn, fileInput) {
        browseBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Browse button clicked');
            fileInput.click();
        });
        
        // Add visual feedback
        browseBtn.addEventListener('mouseenter', () => {
            browseBtn.style.backgroundColor = '#0056b3';
        });
        
        browseBtn.addEventListener('mouseleave', () => {
            browseBtn.style.backgroundColor = '';
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        console.log('Files dropped:', files);
        this.handleFiles(files);
    }

    async handleFiles(files) {
        try {
            const fileArray = Array.from(files);
            console.log('Processing files:', fileArray);
            
            // Validate file count
            if (this.selectedFiles.length + fileArray.length > this.maxFiles) {
                // แทนที่ notification service ด้วย alert ธรรมดา
                alert(`Maximum ${this.maxFiles} files allowed. Currently selected: ${this.selectedFiles.length}`);
                return;
            }

            // Process each file
            for (const file of fileArray) {
                await this.processFile(file);
            }

            this.updateUI();
            this.updateFormData();

        } catch (error) {
            console.error('Error handling files:', error);
            alert('Error processing files: ' + error.message);
        }
    }

    async processFile(file) {
        return new Promise((resolve, reject) => {
            console.log('Processing file:', file.name, file.type, file.size);
            
            // Validate file type
            if (!this.allowedTypes.includes(file.type)) {
                reject(new Error(`File "${file.name}" has unsupported format. Allowed: JPEG, PNG, GIF, WebP, BMP`));
                return;
            }

            // Validate file size
            if (file.size > this.maxFileSize) {
                reject(new Error(`File "${file.name}" exceeds 5MB limit`));
                return;
            }

            // Check total size
            if (this.totalSize + file.size > this.maxTotalSize) {
                reject(new Error(`Total size would exceed 100MB limit`));
                return;
            }

            // Read file as base64
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const fileData = {
                    filename: file.name,
                    size: file.size,
                    type: file.type,
                    data: e.target.result,
                    description: '',
                    id: Date.now() + Math.random() // Unique ID for tracking
                };

                this.selectedFiles.push(fileData);
                this.totalSize += file.size;
                console.log('File processed successfully:', file.name);
                resolve(fileData);
            };

            reader.onerror = () => {
                reject(new Error(`Failed to read file "${file.name}"`));
            };

            reader.readAsDataURL(file);
        });
    }

    updateUI() {
        this.renderFilePreview();
        this.updateStats();
    }

    renderFilePreview() {
        const previewContainer = document.getElementById('selected_files_preview');
        const filesList = document.getElementById('files_list');

        if (!previewContainer || !filesList) {
            console.warn('Preview containers not found');
            return;
        }

        if (this.selectedFiles.length === 0) {
            previewContainer.style.display = 'none';
            return;
        }

        previewContainer.style.display = 'block';
        filesList.innerHTML = '';

        this.selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'col-md-3 col-sm-4 col-6';
            fileItem.innerHTML = `
                <div class="file-preview-item" data-file-id="${file.id}">
                    <button type="button" class="file-remove-btn" onclick="window.custodyUploadWidget?.removeFile('${file.id}')">
                        ×
                    </button>
                    <img src="${file.data}" alt="${file.filename}" class="file-preview-img">
                    <div class="file-preview-name">${file.filename}</div>
                    <div class="file-preview-size">${this.formatFileSize(file.size)}</div>
                    <div class="file-preview-desc">
                        <input type="text" 
                               placeholder="Description (optional)" 
                               value="${file.description}"
                               onchange="window.custodyUploadWidget?.updateFileDescription('${file.id}', this.value)">
                    </div>
                </div>
            `;
            filesList.appendChild(fileItem);
        });
    }

    updateStats() {
        // Update form fields
        const totalFilesField = document.querySelector('input[name="total_files"]');
        const totalSizeField = document.querySelector('input[name="total_size_mb"]');

        if (totalFilesField) {
            totalFilesField.value = this.selectedFiles.length;
            // Trigger change event
            totalFilesField.dispatchEvent(new Event('change'));
        }

        if (totalSizeField) {
            totalSizeField.value = (this.totalSize / (1024 * 1024)).toFixed(2);
            // Trigger change event
            totalSizeField.dispatchEvent(new Event('change'));
        }
    }

    updateFormData() {
        const imagesDataField = document.querySelector('textarea[name="images_data"]');
        if (imagesDataField) {
            imagesDataField.value = JSON.stringify(this.selectedFiles);
            // Trigger change event
            imagesDataField.dispatchEvent(new Event('change'));
        }
    }

    removeFile(fileId) {
        const fileIndex = this.selectedFiles.findIndex(f => f.id == fileId);
        if (fileIndex !== -1) {
            this.totalSize -= this.selectedFiles[fileIndex].size;
            this.selectedFiles.splice(fileIndex, 1);
            this.updateUI();
            this.updateFormData();
        }
    }

    updateFileDescription(fileId, description) {
        const file = this.selectedFiles.find(f => f.id == fileId);
        if (file) {
            file.description = description;
            this.updateFormData();
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    cleanup() {
        // Clean up global references
        if (window.custodyUploadWidget) {
            delete window.custodyUploadWidget;
        }
    }
}

// ปรับปรุงการ initialize ให้ safer
function initializeCustodyUpload() {
    const uploadZone = document.querySelector('.custody-upload-zone');
    if (uploadZone && !window.custodyUploadWidget) {
        console.log('Initializing custody upload widget...');
        try {
            const widget = new CustodyMultipleImageUpload();
            window.custodyUploadWidget = widget;
            widget.setup();
            console.log('Custody upload widget initialized successfully');
        } catch (error) {
            console.error('Error initializing custody upload widget:', error);
            // ถ้า error ให้ลองใหม่หลัง 2 วินาที
            setTimeout(initializeCustodyUpload, 2000);
        }
    }
}

// เรียกใช้เมื่อ DOM พร้อม
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCustodyUpload);
} else {
    // DOM พร้อมแล้ว ลองเลย
    initializeCustodyUpload();
}

// Backup - ลองอีกครั้งเมื่อ window load
window.addEventListener('load', () => {
    setTimeout(initializeCustodyUpload, 1000);
});

// Register เป็น component (optional สำหรับ OWL usage)
registry.category("fields").add("custody_multiple_image_upload", CustodyMultipleImageUpload);
