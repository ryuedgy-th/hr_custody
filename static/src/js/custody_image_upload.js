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

console.log('✅ Custody Upload Module Loaded - Enhanced with Chunked Upload Strategy');