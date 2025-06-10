// Fixed Upload Manager for Custody Images
// แก้ไข: event ซ้อน และ form data integration

console.log('🚀 Custody Upload Script Loading...');

(function() {
    'use strict';
    
    // Prevent multiple initializations
    if (window.custodyUploadManager) {
        console.log('⚠️ Upload manager already exists, skipping...');
        return;
    }
    
    // Upload manager class
    function CustodyUploadManager() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFiles = 20;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        this.initialized = false;
        
        console.log('📋 Upload Manager Created');
    }
    
    CustodyUploadManager.prototype.init = function() {
        if (this.initialized) {
            console.log('⚠️ Manager already initialized');
            return;
        }
        
        console.log('🔍 Looking for upload elements...');
        
        var dropzone = document.querySelector('.upload-dropzone');
        var fileInput = document.getElementById('file_input');
        var browseBtn = document.getElementById('browse_files_btn');
        
        if (!dropzone || !fileInput || !browseBtn) {
            console.log('⏳ Elements not found, retrying in 500ms...');
            setTimeout(this.init.bind(this), 500);
            return;
        }
        
        console.log('✅ Found all elements');
        this.setupEvents(dropzone, fileInput, browseBtn);
        this.initialized = true;
        console.log('✅ Manager initialized successfully');
    };
    
    CustodyUploadManager.prototype.setupEvents = function(dropzone, fileInput, browseBtn) {
        var self = this;
        
        // Remove any existing event listeners to prevent duplicates
        var newFileInput = fileInput.cloneNode(true);
        fileInput.parentNode.replaceChild(newFileInput, fileInput);
        fileInput = newFileInput;
        
        var newBrowseBtn = browseBtn.cloneNode(true);
        browseBtn.parentNode.replaceChild(newBrowseBtn, browseBtn);
        browseBtn = newBrowseBtn;
        
        console.log('🔧 Setting up clean events...');
        
        // Browse button click - ป้องกันการเปิด dialog ซ้ำ
        browseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            console.log('🖱️ Browse button clicked');
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', function(e) {
            console.log('📁 File input changed! Files:', e.target.files.length);
            
            if (e.target.files.length > 0) {
                console.log('📝 Processing selected files...');
                self.handleFiles(e.target.files);
                // Clear the input for next selection
                e.target.value = '';
            }
        });
        
        // Dropzone click - ป้องกันการเปิด dialog ซ้ำ
        dropzone.addEventListener('click', function(e) {
            if (e.target === browseBtn || browseBtn.contains(e.target)) {
                return; // Let browse button handle it
            }
            e.preventDefault();
            e.stopPropagation();
            console.log('🖱️ Dropzone clicked - opening file dialog');
            fileInput.click();
        });
        
        // Drag and drop events
        this.setupDragAndDrop(dropzone, self);
        
        console.log('✅ Events setup complete');
    };
    
    CustodyUploadManager.prototype.setupDragAndDrop = function(dropzone, self) {
        // Prevent default behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(function(eventName) {
            dropzone.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });
        
        // Visual feedback
        ['dragenter', 'dragover'].forEach(function(eventName) {
            dropzone.addEventListener(eventName, function() {
                dropzone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(function(eventName) {
            dropzone.addEventListener(eventName, function() {
                dropzone.classList.remove('dragover');
            }, false);
        });
        
        // Handle file drop
        dropzone.addEventListener('drop', function(e) {
            var files = e.dataTransfer.files;
            console.log('📂 Files dropped:', files.length);
            self.handleFiles(files);
        }, false);
    };
    
    CustodyUploadManager.prototype.handleFiles = function(files) {
        console.log('📝 Processing files:', files.length);
        
        if (!files || files.length === 0) {
            console.log('⚠️ No files to process');
            return;
        }
        
        if (this.selectedFiles.length + files.length > this.maxFiles) {
            alert('Maximum ' + this.maxFiles + ' files allowed. Currently selected: ' + this.selectedFiles.length);
            return;
        }
        
        // Process each file
        var validFiles = 0;
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            console.log('🔍 Checking file:', file.name, file.type, file.size);
            
            // Validate file type
            if (!this.allowedTypes.includes(file.type)) {
                alert('File "' + file.name + '" has unsupported format. Allowed: JPEG, PNG, GIF, WebP, BMP');
                continue;
            }
            
            // Validate file size
            if (file.size > this.maxFileSize) {
                alert('File "' + file.name + '" exceeds 5MB limit');
                continue;
            }
            
            // Check total size
            if (this.totalSize + file.size > this.maxTotalSize) {
                alert('Total size would exceed 100MB limit');
                break;
            }
            
            console.log('✅ File valid:', file.name);
            this.addFile(file);
            validFiles++;
        }
        
        console.log('📊 Added', validFiles, 'valid files. Total:', this.selectedFiles.length);
        this.updateDisplay();
    };
    
    CustodyUploadManager.prototype.addFile = function(file) {
        var fileData = {
            id: Date.now() + Math.random(),
            filename: file.name,
            size: file.size,
            type: file.type,
            file: file,
            description: ''
        };
        
        this.selectedFiles.push(fileData);
        this.totalSize += file.size;
        
        // Create preview immediately
        this.createFilePreview(fileData);
    };
    
    CustodyUploadManager.prototype.createFilePreview = function(fileData) {
        var self = this;
        var reader = new FileReader();
        
        reader.onload = function(e) {
            fileData.dataUrl = e.target.result;
            self.renderPreviews();
            self.updateFormData(); // อัพเดท form data ทุกครั้งที่มีรูปใหม่
        };
        
        reader.onerror = function() {
            console.error('Error reading file:', fileData.filename);
        };
        
        reader.readAsDataURL(fileData.file);
    };
    
    CustodyUploadManager.prototype.renderPreviews = function() {
        console.log('🖼️ Rendering previews for', this.selectedFiles.length, 'files');
        
        var previewContainer = document.getElementById('selected_files_preview');
        var filesList = document.getElementById('files_list');
        
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
        
        var self = this;
        this.selectedFiles.forEach(function(file) {
            if (file.dataUrl) {
                var fileItem = document.createElement('div');
                fileItem.className = 'col-md-3 col-sm-4 col-6';
                fileItem.innerHTML = 
                    '<div class="file-preview-item" data-file-id="' + file.id + '">' +
                        '<button type="button" class="file-remove-btn" onclick="window.custodyUploadManager.removeFile(\'' + file.id + '\')">' +
                            '×' +
                        '</button>' +
                        '<img src="' + file.dataUrl + '" alt="' + file.filename + '" class="file-preview-img">' +
                        '<div class="file-preview-name">' + file.filename + '</div>' +
                        '<div class="file-preview-size">' + self.formatFileSize(file.size) + '</div>' +
                        '<div class="file-preview-desc">' +
                            '<input type="text" placeholder="Description (optional)" value="' + file.description + '" ' +
                                   'onchange="window.custodyUploadManager.updateFileDescription(\'' + file.id + '\', this.value)">' +
                        '</div>' +
                    '</div>';
                
                filesList.appendChild(fileItem);
            }
        });
        
        console.log('✅ Previews rendered');
    };
    
    CustodyUploadManager.prototype.removeFile = function(fileId) {
        console.log('🗑️ Removing file:', fileId);
        
        var fileIndex = this.selectedFiles.findIndex(function(f) { return f.id == fileId; });
        if (fileIndex !== -1) {
            this.totalSize -= this.selectedFiles[fileIndex].size;
            this.selectedFiles.splice(fileIndex, 1);
            this.renderPreviews();
            this.updateDisplay();
            console.log('✅ File removed. Remaining:', this.selectedFiles.length);
        }
    };
    
    CustodyUploadManager.prototype.updateFileDescription = function(fileId, description) {
        var file = this.selectedFiles.find(function(f) { return f.id == fileId; });
        if (file) {
            file.description = description;
            this.updateFormData();
            console.log('📝 Updated description for:', file.filename);
        }
    };
    
    CustodyUploadManager.prototype.updateDisplay = function() {
        // Update form fields
        var totalFilesField = document.querySelector('input[name="total_files"]');
        var totalSizeField = document.querySelector('input[name="total_size_mb"]');
        
        if (totalFilesField) {
            totalFilesField.value = this.selectedFiles.length;
            totalFilesField.dispatchEvent(new Event('change'));
        }
        
        if (totalSizeField) {
            totalSizeField.value = (this.totalSize / (1024 * 1024)).toFixed(2);
            totalSizeField.dispatchEvent(new Event('change'));
        }
        
        this.updateFormData();
        
        console.log('📊 Display updated:', {
            files: this.selectedFiles.length,
            totalSizeMB: (this.totalSize / (1024 * 1024)).toFixed(2)
        });
    };
    
    CustodyUploadManager.prototype.updateFormData = function() {
        var imagesDataField = document.querySelector('textarea[name="images_data"]');
        if (imagesDataField) {
            // สร้าง data ที่จะส่งไป Python wizard
            var formData = this.selectedFiles.map(function(file) {
                return {
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    data: file.dataUrl,
                    description: file.description || '',
                    id: file.id
                };
            });
            
            imagesDataField.value = JSON.stringify(formData);
            
            // Force trigger change event for Odoo form
            var event = new Event('input', { bubbles: true });
            imagesDataField.dispatchEvent(event);
            
            console.log('💾 Form data updated with', formData.length, 'files');
            console.log('📄 Data preview:', JSON.stringify(formData).substring(0, 200) + '...');
        } else {
            console.warn('⚠️ images_data field not found');
        }
    };
    
    CustodyUploadManager.prototype.formatFileSize = function(bytes) {
        if (bytes === 0) return '0 Bytes';
        var k = 1024;
        var sizes = ['Bytes', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    
    // Initialize function
    function initializeUpload() {
        console.log('🔍 Checking for upload zone...');
        
        if (document.querySelector('.custody-upload-zone')) {
            console.log('✅ Upload zone found!');
            
            if (!window.custodyUploadManager) {
                var manager = new CustodyUploadManager();
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
    
    // Backup initialization
    window.addEventListener('load', function() {
        setTimeout(initializeUpload, 1000);
    });
    
    console.log('✅ Custody Upload Script Loaded Successfully');
})();
