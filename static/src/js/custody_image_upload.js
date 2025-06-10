/** @odoo-module **/

import { Component, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Multiple Image Upload Widget for Custody Images
 */
export class CustodyMultipleImageUpload extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
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
            console.warn('Upload elements not found');
            return;
        }

        // Setup drag and drop
        this.setupDragAndDrop(dropzone);
        
        // Setup file input
        this.setupFileInput(fileInput, browseBtn);
    }

    setupDragAndDrop(dropzone) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, this.preventDefaults.bind(this), false);
            document.body.addEventListener(eventName, this.preventDefaults.bind(this), false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
        });

        // Handle dropped files
        dropzone.addEventListener('drop', this.handleDrop.bind(this), false);
        
        // Handle click to browse
        dropzone.addEventListener('click', () => {
            document.getElementById('file_input').click();
        });
    }

    setupFileInput(fileInput, browseBtn) {
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });

        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }

    async handleFiles(files) {
        try {
            const fileArray = Array.from(files);
            
            // Validate file count
            if (this.selectedFiles.length + fileArray.length > this.maxFiles) {
                this.notification.add(
                    `Maximum ${this.maxFiles} files allowed. Currently selected: ${this.selectedFiles.length}`,
                    { type: 'warning' }
                );
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
            this.notification.add('Error processing files: ' + error.message, { type: 'danger' });
        }
    }

    async processFile(file) {
        return new Promise((resolve, reject) => {
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
                    <button type="button" class="file-remove-btn" onclick="removeFile('${file.id}')">
                        ×
                    </button>
                    <img src="${file.data}" alt="${file.filename}" class="file-preview-img">
                    <div class="file-preview-name">${file.filename}</div>
                    <div class="file-preview-size">${this.formatFileSize(file.size)}</div>
                    <div class="file-preview-desc">
                        <input type="text" 
                               placeholder="Description (optional)" 
                               value="${file.description}"
                               onchange="updateFileDescription('${file.id}', this.value)">
                    </div>
                </div>
            `;
            filesList.appendChild(fileItem);
        });

        // Make functions globally available
        window.removeFile = this.removeFile.bind(this);
        window.updateFileDescription = this.updateFileDescription.bind(this);
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
        // Clean up global functions
        if (window.removeFile) {
            delete window.removeFile;
        }
        if (window.updateFileDescription) {
            delete window.updateFileDescription;
        }
    }
}

// Auto-initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.custody-upload-zone')) {
        new CustodyMultipleImageUpload();
    }
});

// Register component for potential future use
CustodyMultipleImageUpload.template = "hr_custody.CustodyMultipleImageUpload";
registry.category("fields").add("custody_multiple_image_upload", CustodyMultipleImageUpload);
