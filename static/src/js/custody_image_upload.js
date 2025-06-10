/** @odoo-module **/

// Updated 2025-06-11 - Fix field selectors for invisible fields

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
        this.browseButtonClicked = false; // Track browse button clicks
        
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
            filesList: document.getElementById('files_list'),
            // ปรับ selector สำหรับ invisible fields ใน Odoo
            imagesDataField: document.querySelector('textarea[name="images_data"]') || 
                           document.querySelector('input[name="images_data"]') ||
                           document.querySelector('field[name="images_data"] textarea') ||
                           document.querySelector('field[name="images_data"] input'),
            totalFilesField: document.querySelector('input[name="total_files"]') ||
                           document.querySelector('field[name="total_files"] input'),
            totalSizeField: document.querySelector('input[name="total_size_mb"]') ||
                          document.querySelector('field[name="total_size_mb"] input')
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
        this.initialized = true;
        console.log('✅ Manager initialized successfully');
    }

    triggerFileDialog() {
        const now = Date.now();
        
        // ป้องกัน rapid clicks (ภายใน 300ms)
        if (now - this.lastClickTime < 300) {
            console.log('⚠️ Rapid click detected, ignoring');
            return;
        }
        
        // ป้องกัน multiple calls ในเวลาใกล้กัน
        if (this.clickTimeout) {
            console.log('⚠️ File dialog already triggered, ignoring');
            return;
        }

        console.log('🎯 Triggering file dialog...');
        this.lastClickTime = now;
        this.browseButtonClicked = true; // Set flag เมื่อกด browse button
        
        const fileInput = document.getElementById('file_input');
        if (fileInput) {
            fileInput.click();
            console.log('✅ File dialog opened');
            
            // Set timeout เพื่อป้องกัน multiple triggers
            this.clickTimeout = setTimeout(() => {
                this.clickTimeout = null;
                this.browseButtonClicked = false; // Reset flag หลังจาก 500ms
            }, 500);
        } else {
            console.error('❌ File input not found');
            this.browseButtonClicked = false;
        }
    }

    setupEvents(elements) {
        const { dropzone, fileInput, browseBtn } = elements;
        
        console.log('🔧 Setting up event listeners...');

        // Browse button events - ใช้หลาย events เพื่อ block อย่างสมบูรณ์
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

        // Dropzone click - เช็คทั้ง flag และ position
        dropzone.addEventListener('click', (e) => {
            // ถ้า browse button เพิ่งถูกกด ให้ skip
            if (this.browseButtonClicked) {
                console.log('🚫 Browse button just clicked, ignoring dropzone');
                return;
            }

            // เช็คอย่างละเอียดว่าคลิกบริเวณ browse button หรือไม่
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
            this.updateFormData();
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
        // ลองหา fields ด้วยหลายวิธี
        const totalFilesField = this.findFormField('total_files');
        const totalSizeField = this.findFormField('total_size_mb');

        if (totalFilesField) {
            totalFilesField.value = this.selectedFiles.length;
            this.triggerOdooFieldUpdate(totalFilesField);
            console.log('✅ Updated total_files field:', this.selectedFiles.length);
        } else {
            console.warn('⚠️ total_files field not found');
        }

        if (totalSizeField) {
            const sizeInMB = (this.totalSize / (1024 * 1024)).toFixed(2);
            totalSizeField.value = sizeInMB;
            this.triggerOdooFieldUpdate(totalSizeField);
            console.log('✅ Updated total_size_mb field:', sizeInMB);
        } else {
            console.warn('⚠️ total_size_mb field not found');
        }

        this.updateFormData();

        console.log('📊 Display updated:', {
            files: this.selectedFiles.length,
            totalSizeMB: (this.totalSize / (1024 * 1024)).toFixed(2)
        });
    }

    findFormField(fieldName) {
        // ลองหา field ด้วยหลาย selector
        const selectors = [
            `input[name="${fieldName}"]`,
            `textarea[name="${fieldName}"]`,
            `field[name="${fieldName}"] input`,
            `field[name="${fieldName}"] textarea`,
            `.o_field_widget[name="${fieldName}"] input`,
            `.o_field_widget[name="${fieldName}"] textarea`,
            `[data-field-name="${fieldName}"] input`,
            `[data-field-name="${fieldName}"] textarea`
        ];

        for (const selector of selectors) {
            const field = document.querySelector(selector);
            if (field) {
                console.log(`🎯 Found ${fieldName} using selector: ${selector}`);
                return field;
            }
        }
        
        console.warn(`⚠️ Field ${fieldName} not found with any selector`);
        return null;
    }

    triggerOdooFieldUpdate(field) {
        // Trigger Odoo field update events
        const events = ['change', 'input', 'blur'];
        events.forEach(eventType => {
            const event = new Event(eventType, { bubbles: true, cancelable: true });
            field.dispatchEvent(event);
        });
    }

    updateFormData() {
        const imagesDataField = this.findFormField('images_data');
        
        if (imagesDataField) {
            const formData = this.selectedFiles
                .filter(file => file.dataUrl)
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    data: file.dataUrl,
                    description: file.description || '',
                    id: file.id
                }));

            imagesDataField.value = JSON.stringify(formData);
            this.triggerOdooFieldUpdate(imagesDataField);

            console.log('💾 Form data updated with', formData.length, 'files');
            if (formData.length > 0) {
                console.log('📄 Sample data length:', formData[0].data.length);
                console.log('📄 Sample filename:', formData[0].filename);
            }
        } else {
            console.error('❌ images_data field not found');
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
            this.updateFormData();
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

console.log('✅ Custody Upload Module Loaded - Fixed Field Selectors');
