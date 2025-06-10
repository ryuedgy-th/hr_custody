/** @odoo-module **/

// Updated 2025-06-11 - Add DOM inspection for debugging

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

    // Debug function to inspect DOM
    debugDOMStructure() {
        console.log('🔍 DEBUG: Inspecting DOM structure...');
        
        // ดู form elements ทั้งหมด
        const allInputs = document.querySelectorAll('input');
        const allTextareas = document.querySelectorAll('textarea');
        const allFields = document.querySelectorAll('[name*="total_files"], [name*="total_size"], [name*="images_data"]');
        
        console.log('📋 All inputs:', allInputs.length);
        allInputs.forEach((input, i) => {
            if (input.name) {
                console.log(`  Input ${i}: name="${input.name}", type="${input.type}", class="${input.className}"`);
            }
        });
        
        console.log('📋 All textareas:', allTextareas.length);
        allTextareas.forEach((textarea, i) => {
            if (textarea.name) {
                console.log(`  Textarea ${i}: name="${textarea.name}", class="${textarea.className}"`);
            }
        });
        
        console.log('📋 Fields with target names:', allFields.length);
        allFields.forEach((field, i) => {
            console.log(`  Field ${i}:`, field.outerHTML.substring(0, 100) + '...');
        });
        
        // ดู Odoo field widgets
        const odooFields = document.querySelectorAll('.o_field_widget, [data-field-name], .o_field');
        console.log('📋 Odoo field widgets:', odooFields.length);
        odooFields.forEach((field, i) => {
            const name = field.getAttribute('name') || field.getAttribute('data-field-name') || field.dataset.fieldName;
            if (name && (name.includes('total_files') || name.includes('total_size') || name.includes('images_data'))) {
                console.log(`  Odoo Field ${i}: name="${name}", class="${field.className}"`);
                console.log(`    HTML:`, field.outerHTML.substring(0, 150) + '...');
            }
        });
    }

    init() {
        if (this.initialized) {
            console.log('⚠️ Manager already initialized');
            return;
        }

        console.log('🔍 Looking for upload elements...');
        
        // เรียก debug function
        setTimeout(() => this.debugDOMStructure(), 1000);
        
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
        // ใช้ alternative approach: ตั้งค่าใน global variables แทน
        console.log('💾 Storing data in global variables for form submission...');
        
        // เก็บข้อมูลใน window object เพื่อให้ Odoo access ได้
        window.custodyUploadData = {
            totalFiles: this.selectedFiles.length,
            totalSizeMB: (this.totalSize / (1024 * 1024)).toFixed(2),
            filesData: this.selectedFiles
                .filter(file => file.dataUrl)
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    data: file.dataUrl,
                    description: file.description || '',
                    id: file.id
                }))
        };
        
        console.log('📊 Global data updated:', {
            files: window.custodyUploadData.totalFiles,
            totalSizeMB: window.custodyUploadData.totalSizeMB,
            dataLength: window.custodyUploadData.filesData.length
        });
        
        // พยายาม inject ข้อมูลลงใน form field ถ้าเจอ
        this.injectFormData();
    }

    injectFormData() {
        // ลองหา form และ inject ข้อมูลโดยตรง
        const form = document.querySelector('form');
        if (form) {
            console.log('📝 Found form, attempting to inject data...');
            
            // ลองสร้าง hidden fields
            const fieldsToCreate = [
                { name: 'total_files', value: this.selectedFiles.length },
                { name: 'total_size_mb', value: (this.totalSize / (1024 * 1024)).toFixed(2) },
                { name: 'images_data', value: JSON.stringify(window.custodyUploadData.filesData) }
            ];
            
            fieldsToCreate.forEach(fieldInfo => {
                // ลบ field เก่าถ้ามี
                const existingField = form.querySelector(`input[name="${fieldInfo.name}"], textarea[name="${fieldInfo.name}"]`);
                if (existingField) {
                    existingField.value = fieldInfo.value;
                    this.triggerOdooFieldUpdate(existingField);
                    console.log(`✅ Updated existing field: ${fieldInfo.name} = ${fieldInfo.value}`);
                } else {
                    // สร้าง hidden field ใหม่
                    const hiddenField = document.createElement('input');
                    hiddenField.type = 'hidden';
                    hiddenField.name = fieldInfo.name;
                    hiddenField.value = fieldInfo.value;
                    form.appendChild(hiddenField);
                    console.log(`✅ Created hidden field: ${fieldInfo.name} = ${fieldInfo.value}`);
                }
            });
        }
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
        // อัพเดท global data
        this.updateDisplay();
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

console.log('✅ Custody Upload Module Loaded - With DOM Debug & Form Injection');
