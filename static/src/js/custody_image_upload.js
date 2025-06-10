/** @odoo-module **/

/**
 * Simple Multiple Image Upload Manager for Custody
 * สำหรับ Odoo 18.0 - ใช้ vanilla JS เพื่อหลีกเลี่ยงปัญหา service dependencies
 */

// Global manager instance
let custodyUploadManager = null;

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
            console.log('⏳ Elements not ready, retrying...');
            setTimeout(() => this.init(), 500);
            return;
        }

        console.log('✅ Found all elements, setting up...');
        this.setupEventListeners(dropzone, fileInput, browseBtn);
        this.initialized = true;
        console.log('✅ Manager initialized successfully!');
    }

    setupEventListeners(dropzone, fileInput, browseBtn) {
        try {
            // File input change event
            fileInput.addEventListener('change', (e) => {
                console.log('📁 Files selected:', e.target.files.length);
                this.handleFiles(e.target.files);
            });

            // Browse button click event
            browseBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🖱️ Browse button clicked');
                
                const currentFileInput = document.getElementById('file_input');
                if (currentFileInput) {
                    currentFileInput.click();
                    console.log('✅ File dialog opened');
                } else {
                    console.error('❌ File input element not found');
                }
            });

            // Drag and drop events
            this.setupDragAndDrop(dropzone);
            
            // Dropzone click (alternative trigger)
            dropzone.addEventListener('click', (e) => {
                if (e.target !== browseBtn && !browseBtn.contains(e.target)) {
                    console.log('🖱️ Dropzone area clicked');
                    const currentFileInput = document.getElementById('file_input');
                    if (currentFileInput) {
                        currentFileInput.click();
                    }
                }
            });

            console.log('✅ All event listeners setup complete');
        } catch (error) {
            console.error('❌ Error setting up event listeners:', error);
        }
    }

    setupDragAndDrop(dropzone) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });

        // Visual feedback for drag over
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove('dragover');
            }, false);
        });

        // Handle file drop
        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            console.log('📂 Files dropped:', files.length);
            this.handleFiles(files);
        }, false);
    }

    async handleFiles(files) {
        try {
            const fileArray = Array.from(files);
            console.log('📝 Processing', fileArray.length, 'files');
            
            if (this.selectedFiles.length + fileArray.length > this.maxFiles) {
                this.showMessage(`Maximum ${this.maxFiles} files allowed. Currently selected: ${this.selectedFiles.length}`, 'warning');
                return;
            }

            for (const file of fileArray) {
                await this.processFile(file);
            }

            this.updateUI();
            this.updateFormData();

        } catch (error) {
            console.error('❌ Error handling files:', error);
            this.showMessage('Error processing files: ' + error.message, 'error');
        }
    }

    async processFile(file) {
        return new Promise((resolve, reject) => {
            console.log('⚙️ Processing:', file.name);
            
            // Validate file type
            if (!this.allowedTypes.includes(file.type)) {
                reject(new Error(`File "${file.name}" has unsupported format`));
                return;
            }

            // Validate file size
            if (file.size > this.maxFileSize) {
                reject(new Error(`File "${file.name}" exceeds 5MB limit`));
                return;
            }

            if (this.totalSize + file.size > this.maxTotalSize) {
                reject(new Error('Total size would exceed 100MB limit'));
                return;
            }

            // Read file
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const fileData = {
                    filename: file.name,
                    size: file.size,
                    type: file.type,
                    data: e.target.result,
                    description: '',
                    id: Date.now() + Math.random()
                };

                this.selectedFiles.push(fileData);
                this.totalSize += file.size;
                console.log('✅ File processed:', file.name);
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
                    <button type="button" class="file-remove-btn" onclick="custodyUploadManager?.removeFile('${file.id}')">
                        ×
                    </button>
                    <img src="${file.data}" alt="${file.filename}" class="file-preview-img">
                    <div class="file-preview-name">${file.filename}</div>
                    <div class="file-preview-size">${this.formatFileSize(file.size)}</div>
                    <div class="file-preview-desc">
                        <input type="text" 
                               placeholder="Description (optional)" 
                               value="${file.description}"
                               onchange="custodyUploadManager?.updateFileDescription('${file.id}', this.value)">
                    </div>
                </div>
            `;
            filesList.appendChild(fileItem);
        });
    }

    updateStats() {
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

    showMessage(message, type = 'info') {
        // ใช้ native alert หรือ Odoo notification ถ้ามี
        if (type === 'error') {
            alert('Error: ' + message);
        } else if (type === 'warning') {
            alert('Warning: ' + message);
        } else {
            console.log('Info:', message);
        }
    }
}

// Safe initialization function
function initializeCustodyUpload() {
    console.log('🔍 Looking for custody upload zone...');
    
    const uploadZone = document.querySelector('.custody-upload-zone');
    
    if (uploadZone && !custodyUploadManager) {
        console.log('✅ Upload zone found! Creating manager...');
        
        try {
            custodyUploadManager = new CustodyUploadManager();
            // Make it globally accessible for onclick handlers
            window.custodyUploadManager = custodyUploadManager;
            custodyUploadManager.init();
        } catch (error) {
            console.error('❌ Error creating upload manager:', error);
            setTimeout(initializeCustodyUpload, 2000);
        }
    } else if (!uploadZone) {
        console.log('⏳ No upload zone found, retrying...');
        setTimeout(initializeCustodyUpload, 500);
    }
}

// Initialize when DOM is ready
console.log('📋 Setting up custody upload initialization...');

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCustodyUpload);
} else {
    initializeCustodyUpload();
}

// Backup initialization
window.addEventListener('load', () => {
    setTimeout(initializeCustodyUpload, 1000);
});

// Watch for dynamic content
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1 && 
                    node.querySelector && 
                    node.querySelector('.custody-upload-zone')) {
                    console.log('🔄 Upload zone detected via MutationObserver');
                    setTimeout(initializeCustodyUpload, 100);
                }
            });
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

console.log('✅ Custody upload module loaded successfully');
