# Hr_custody - Comparison with Odoo 18 hr_expense Best Practices

## 🔍 การศึกษา hr_expense module เพื่อปรับปรุง hr_custody

จากการศึกษา hr_expense module ของ Odoo 18 ผมพบแนวทางปฏิบัติที่ดีหลายประการที่สามารถนำมาปรับปรุง hr_custody ได้:

### 💡 ข้อค้นพบสำคัญจาก hr_expense:

#### 1. **การใช้ ORM Service แทน RPC แบบเก่า**
Odoo 18 แนะนำให้ใช้ `orm` service แทน `rpc` สำหรับการเรียก model methods:

```javascript
// ❌ วิธีเก่า (ที่ hr_custody ใช้อยู่)
const rpcData = {
    model: 'custody.image.upload.wizard',
    method: 'write',
    args: [[wizardId], data],
    kwargs: {}
};
const result = await this.callOdooRPC('/web/dataset/call_kw', rpcData);

// ✅ วิธีใหม่ที่ดีกว่า (ตาม hr_expense pattern)
this.orm = useService("orm");
const result = await this.orm.write('custody.image.upload.wizard', [wizardId], data);
const uploadResult = await this.orm.call('custody.image.upload.wizard', 'action_upload_images', [wizardId]);
```

#### 2. **การจัดการ Error ที่ดีกว่า**
hr_expense ใช้ standard error handling pattern:

```javascript
try {
    const result = await this.orm.call(model, method, args);
    // Handle success
} catch (error) {
    this.notification.add({
        title: _t("Error"),
        message: error.message,
        type: "danger",
    });
}
```

#### 3. **การใช้ Notification Service**
```javascript
this.notification = useService("notification");

// แสดง notification
this.notification.add({
    title: _t("Upload Successful"),
    message: _t("Successfully uploaded %s images", count),
    type: "success",
});
```

#### 4. **การใช้ useService Pattern อย่างถูกต้อง**
```javascript
setup() {
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.action = useService("action");
}
```

### 🔧 การปรับปรุง hr_custody ตาม Best Practices

#### 1. **ปรับปรุง JavaScript เป็น Odoo 18 Standard**

```javascript
/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class CustodyUploadManager {
    constructor() {
        this.selectedFiles = [];
        this.totalSize = 0;
        this.maxFiles = 20;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.maxTotalSize = 100 * 1024 * 1024; // 100MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
        
        // Initialize Odoo services
        this.setupServices();
    }

    setupServices() {
        // Use Odoo 18 service pattern
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
    }

    async handleCustomUpload() {
        if (this.selectedFiles.length === 0) {
            this.notification.add({
                title: _t("No Files Selected"),
                message: _t("Please select at least one image to upload."),
                type: "warning",
            });
            return;
        }

        try {
            console.log('📡 Starting Odoo 18 ORM upload...');
            
            const imagesData = this.selectedFiles
                .filter(file => file.dataUrl)
                .map(file => ({
                    filename: file.filename,
                    size: file.size,
                    type: file.type,
                    data: this.compressBase64IfNeeded(file.dataUrl, file.size),
                    description: file.description || '',
                    id: file.id
                }));

            const wizardId = this.getWizardId();
            if (!wizardId) {
                throw new Error(_t('Could not find wizard ID'));
            }

            console.log(`📡 Uploading ${imagesData.length} files via ORM to wizard ${wizardId}...`);

            // STEP 1: Update wizard using ORM service
            await this.orm.write('custody.image.upload.wizard', [wizardId], {
                'images_data': JSON.stringify(imagesData),
                'total_files': this.selectedFiles.length,
                'total_size_mb': parseFloat((this.totalSize / (1024 * 1024)).toFixed(2))
            });

            console.log('✅ Step 1 completed: Wizard updated via ORM');

            // STEP 2: Trigger upload action
            const uploadResult = await this.orm.call(
                'custody.image.upload.wizard', 
                'action_upload_images', 
                [wizardId]
            );

            console.log('✅ Step 2 completed: Upload action result:', uploadResult);

            // Handle the result
            if (uploadResult && uploadResult.type === 'ir.actions.client') {
                this.notification.add({
                    title: uploadResult.params.title || _t("Upload Completed"),
                    message: uploadResult.params.message,
                    type: "success",
                });
                
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.notification.add({
                    title: _t("Upload Completed"),
                    message: _t("Images uploaded successfully!"),
                    type: "success",
                });
                setTimeout(() => window.location.reload(), 1000);
            }

        } catch (error) {
            console.error('❌ Upload failed:', error);
            
            this.notification.add({
                title: _t("Upload Failed"),
                message: this.getDetailedErrorMessage(error),
                type: "danger",
            });
        }
    }

    compressBase64IfNeeded(dataUrl, originalSize) {
        // Same as before...
        if (originalSize > 2 * 1024 * 1024) {
            try {
                const base64Data = dataUrl.split(',')[1] || dataUrl;
                console.log(`📦 Compressing large file (${originalSize} bytes) base64 data...`);
                return base64Data;
            } catch (e) {
                console.warn('⚠️ Failed to compress base64, using original');
                return dataUrl;
            }
        }
        return dataUrl;
    }

    getDetailedErrorMessage(error) {
        const message = error.message || _t('Unknown error');
        
        if (message.includes('Odoo Server Error')) {
            return _t('Server processing error. This might be due to file size, format, or permission issues. Please try with smaller images.');
        }
        
        if (message.includes('403') || message.includes('Forbidden')) {
            return _t('Permission denied. You may not have rights to upload images.');
        }
        
        if (message.includes('413') || message.includes('Payload Too Large')) {
            return _t('Files are too large. Please use smaller images.');
        }
        
        return message;
    }

    // ... rest of the methods remain the same
}
```

#### 2. **ปรับปรุง Python ให้ใช้ Standard Patterns**

```python
def action_upload_images(self):
    """Process and upload multiple images with enhanced error handling"""
    self.ensure_one()
    
    try:
        # ใช้ standard logging pattern เหมือน hr_expense
        _logger.info("Starting image upload for custody %s", self.custody_id.id)
        
        # ... validation code ...
        
        # ใช้ message_post pattern เหมือน hr_expense
        self.custody_id.message_post(
            body=_("Multiple images uploaded successfully: %d files") % len(created_images),
            attachment_ids=[(6, 0, [img.id for img in created_images])],
            message_type='notification'
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upload Successful!'),
                'message': _('Successfully uploaded %d images') % len(created_images),
                'type': 'success',
                'sticky': False
            }
        }
        
    except Exception as e:
        _logger.error("Image upload failed: %s", str(e))
        
        # ใช้ standard error return pattern
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upload Failed'),
                'message': str(e),
                'type': 'danger',
                'sticky': True
            }
        }
```

### 🎯 ประโยชน์ของการปรับปรุง:

1. **Performance**: ORM service มีประสิทธิภาพดีกว่า RPC แบบเก่า
2. **Error Handling**: การจัดการ error ที่มาตรฐานและชัดเจน
3. **User Experience**: Notification ที่สวยงามและเข้าใจง่าย
4. **Maintainability**: โค้ดที่ทำตาม Odoo 18 standard
5. **Consistency**: Pattern เดียวกับ module อื่นใน Odoo 18

### 📋 แผนการอัพเกรด:

1. **Phase 1**: ปรับปรุง JavaScript ให้ใช้ ORM service
2. **Phase 2**: ปรับปรุง Python error handling
3. **Phase 3**: เพิ่ม message_post integration
4. **Phase 4**: ทดสอบและ optimize performance

การปรับปรุงนี้จะทำให้ hr_custody มีคุณภาพและประสิทธิภาพเทียบเท่ากับ hr_expense ของ Odoo 18! 🚀
