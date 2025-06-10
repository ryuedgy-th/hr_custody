/** @odoo-module **/

import { Component, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * Multiple Image Upload Widget for Custody Images
 * แก้ไขปัญหา: Simple approach ที่ทำงานได้จริง
 */
class CustodyUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFiles = 20;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;
        
        console.log('🚀 Initializing CustodyUploadManager...');
        
        const dropzone = document.querySelector('.upload-dropzone');
        const fileInput = document.getElementById('file_input');
        const browseBtn = document.getElementById('browse_files_btn');

        if (!dropzone || !fileInput || !browseBtn) {
            console.warn('⚠️ Upload elements not found, retrying in 500ms...');
            setTimeout(() => this.init(), 500);
            return;
        }

        console.log('✅ Found all elements:', { dropzone, fileInput, browseBtn });

        // Setup event listeners
        this.setupEventListeners(dropzone, fileInput, browseBtn);
        this.initialized = true;
        
        console.log('✅ CustodyUploadManager initialized successfully!');
    }

    setupEventListeners(dropzone, fileInput, browseBtn) {
        // File input change
        fileInput.addEventListener('change', (e) => {
            console.log('📁 File input changed, files:', e.target.files);
            this.handleFiles(e.target.files);
        });

        // Browse button click - สำคัญมาก!
        browseBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('🖱️ Browse button clicked - triggering file input');
            
            // ตรวจสอบว่า file input ยังอยู่หรือไม่
            const currentFileInput = document.getElementById('file_input');
            if (currentFileInput) {
                currentFileInput.click();
                console.log('✅ File input triggered');
            } else {
                console.error('❌ File input not found!');
            }
        });

        // Drag and drop
        this.setupDragAndDrop(dropzone);
        
        // Dropzone click (เผื่อคลิกที่อื่น)
        dropzone.addEventListener('click', (e) => {
            // ถ้าคลิกที่ dropzone แต่ไม่ใช่ browse button
            if (e.target !== browseBtn && !browseBtn.contains(e.target)) {
                console.log('🖱️ Dropzone clicked - triggering file input');
                const currentFileInput = document.getElementById('file_input');
                if (currentFileInput) {
                    currentFileInput.click();
                }
            }
        });

        console.log('✅ All event listeners setup complete');
    }

    setupDragAndDrop(dropzone) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add('dragover');
                console.log('🎯 Drag over detected');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove('dragover');
                console.log('🎯 Drag leave/drop detected');
            }, false);
        });

        // Handle dropped files
        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            console.log('📂 Files dropped:', files);
            this.handleFiles(files);
        }, false);
    }

    async handleFiles(files) {
        try {
            const fileArray = Array.from(files);
            console.log('📝 Processing files:', fileArray.length, 'files');
            
            // Validate file count
            if (this.selectedFiles.length + fileArray.length > this.maxFiles) {
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
            console.error('❌ Error handling files:', error);
            alert('Error processing files: ' + error.message);
        }
    }

    async processFile(file) {
        return new Promise((resolve, reject) => {
            console.log('⚙️ Processing file:', file.name, file.type, file.size);
            
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
                console.log('✅ File processed successfully:', file.name);
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
            console.warn('⚠️ Preview containers not found');
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
                    <button type="button" class="file-remove-btn" onclick="window.custodyUploadManager?.removeFile('${file.id}')">
                        ×
                    </button>
                    <img src="${file.data}" alt="${file.filename}" class="file-preview-img">
                    <div class="file-preview-name">${file.filename}</div>
                    <div class="file-preview-size">${this.formatFileSize(file.size)}</div>
                    <div class="file-preview-desc">
                        <input type="text" 
                               placeholder="Description (optional)" 
                               value="${file.description}"
                               onchange="window.custodyUploadManager?.updateFileDescription('${file.id}', this.value)">
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
            totalFilesField.dispatchEvent(new Event('change'));
        }

        if (totalSizeField) {
            totalSizeField.value = (this.totalSize / (1024 * 1024)).toFixed(2);
            totalSizeField.dispatchEvent(new Event('change'));
        }
    }

    updateFormData() {
        const imagesDataField = document.querySelector('textarea[name="images_data"]');
        if (imagesDataField) {
            imagesDataField.value = JSON.stringify(this.selectedFiles);
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
}

// Initialize function
function initializeCustodyUpload() {
    console.log('🔍 Checking for custody upload zone...');
    const uploadZone = document.querySelector('.custody-upload-zone');
    
    if (uploadZone && !window.custodyUploadManager) {
        console.log('✅ Upload zone found! Creating manager...');
        
        try {
            const manager = new CustodyUploadManager();
            window.custodyUploadManager = manager;
            manager.init();
            console.log('🎉 Custody upload manager ready!');
        } catch (error) {
            console.error('❌ Error creating custody upload manager:', error);
            // Retry after 2 seconds
            setTimeout(initializeCustodyUpload, 2000);
        }
    } else if (!uploadZone) {
        console.log('⏳ Upload zone not found, retrying in 500ms...');
        setTimeout(initializeCustodyUpload, 500);
    } else {
        console.log('ℹ️ Manager already exists');
    }
}

// Multiple initialization strategies
console.log('📋 Setting up custody upload initialization...');

// Strategy 1: DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCustodyUpload);
} else {
    initializeCustodyUpload();
}

// Strategy 2: Window load backup
window.addEventListener('load', () => {
    setTimeout(initializeCustodyUpload, 1000);
});

// Strategy 3: MutationObserver for dynamic content
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && node.querySelector && node.querySelector('.custody-upload-zone')) {
                    console.log('🔄 Upload zone detected via MutationObserver');
                    setTimeout(initializeCustodyUpload, 100);
                }
            });
        }
    });
});

// Start observing
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// OWL Component (optional - สำหรับ future use)
export class CustodyMultipleImageUpload extends Component {
    static template = "hr_custody.CustodyMultipleImageUpload";

    setup() {
        onMounted(() => {
            console.log('🦉 OWL Component mounted, triggering initialization...');
            setTimeout(initializeCustodyUpload, 100);
        });

        onWillUnmount(() => {
            if (window.custodyUploadManager) {
                delete window.custodyUploadManager;
            }
        });
    }
}

// Register component
registry.category("fields").add("custody_multiple_image_upload", CustodyMultipleImageUpload);

console.log('✅ Custody upload module loaded');
