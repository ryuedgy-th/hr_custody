// Simple Upload Manager for Custody Images
// ใช้ vanilla JavaScript เท่านั้น ไม่มี @odoo-module

console.log('🚀 Custody Upload Script Loading...');

(function() {
    'use strict';
    
    // Simple upload manager
    function CustodyUploadManager() {
        this.selectedFiles = [];
        this.maxFiles = 20;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        
        console.log('📋 Upload Manager Created');
    }
    
    CustodyUploadManager.prototype.init = function() {
        console.log('🔍 Looking for upload elements...');
        
        var dropzone = document.querySelector('.upload-dropzone');
        var fileInput = document.getElementById('file_input');
        var browseBtn = document.getElementById('browse_files_btn');
        
        if (!dropzone || !fileInput || !browseBtn) {
            console.log('⏳ Elements not found, retrying in 500ms...');
            setTimeout(this.init.bind(this), 500);
            return;
        }
        
        console.log('✅ Found all elements!');
        this.setupEvents(dropzone, fileInput, browseBtn);
    };
    
    CustodyUploadManager.prototype.setupEvents = function(dropzone, fileInput, browseBtn) {
        var self = this;
        
        // Browse button click
        browseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('🖱️ Browse button clicked');
            fileInput.click();
        });
        
        // File input change
        fileInput.addEventListener('change', function(e) {
            console.log('📁 Files selected:', e.target.files.length);
            self.handleFiles(e.target.files);
        });
        
        // Basic drag and drop
        dropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
        
        dropzone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
        
        dropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            console.log('📂 Files dropped:', e.dataTransfer.files.length);
            self.handleFiles(e.dataTransfer.files);
        });
        
        console.log('✅ Events setup complete');
    };
    
    CustodyUploadManager.prototype.handleFiles = function(files) {
        console.log('📝 Processing files:', files.length);
        
        if (files.length > this.maxFiles) {
            alert('Maximum ' + this.maxFiles + ' files allowed');
            return;
        }
        
        // Simple validation and preview
        for (var i = 0; i < files.length; i++) {
            var file = files[i];
            
            if (!this.allowedTypes.includes(file.type)) {
                alert('File "' + file.name + '" has unsupported format');
                continue;
            }
            
            if (file.size > this.maxFileSize) {
                alert('File "' + file.name + '" exceeds 5MB limit');
                continue;
            }
            
            console.log('✅ File valid:', file.name);
            this.selectedFiles.push(file);
        }
        
        this.updateDisplay();
    };
    
    CustodyUploadManager.prototype.updateDisplay = function() {
        var totalFilesField = document.querySelector('input[name="total_files"]');
        if (totalFilesField) {
            totalFilesField.value = this.selectedFiles.length;
        }
        
        console.log('📊 Updated display:', this.selectedFiles.length, 'files');
    };
    
    // Initialize when DOM is ready
    function initializeUpload() {
        console.log('🔍 Checking for upload zone...');
        
        if (document.querySelector('.custody-upload-zone')) {
            console.log('✅ Upload zone found!');
            var manager = new CustodyUploadManager();
            window.custodyUploadManager = manager;  // Make globally accessible
            manager.init();
        } else {
            console.log('⏳ Upload zone not found, retrying...');
            setTimeout(initializeUpload, 1000);
        }
    }
    
    // Multiple initialization methods
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeUpload);
    } else {
        initializeUpload();
    }
    
    // Backup initialization
    window.addEventListener('load', function() {
        setTimeout(initializeUpload, 1000);
    });
    
    console.log('✅ Custody Upload Script Loaded');
})();
