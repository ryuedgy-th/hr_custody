# HR Custody - Multiple Image Upload Feature

## 🆕 New Feature: Multiple Image Upload

### Overview
The HR Custody module now supports **multiple image upload** with drag & drop functionality for before/after documentation of custody equipment.

### Key Features

#### 📁 **Batch Upload**
- Upload up to **20 images** at once
- **Drag & drop** interface
- **Browse files** option
- Real-time **progress tracking**

#### 🖼️ **Image Management**
- **Preview** selected images before upload
- **Individual descriptions** for each image
- **Auto-sequencing** of uploaded images
- **File validation** (format, size, etc.)

#### 📊 **Smart Limitations**
- Maximum **5MB per image**
- Maximum **100MB total** per upload
- Supported formats: **JPEG, PNG, GIF, WebP, BMP**
- Maximum **20 files** per batch

#### ⚙️ **Advanced Options**
- **Bulk description** for all images
- **Location notes** shared across images
- **Auto sequence numbering**
- **Error handling** with detailed messages

### How to Use

#### 1. **Access Multiple Upload**
From any custody record, click one of these buttons:
- `📁 Upload Multiple Before Images`
- `📁 Upload Multiple After Images` 
- `📁 Upload Damage Images`

#### 2. **Upload Images**
- **Drag & drop** files into the upload zone
- Or click **"Browse Files"** to select multiple files
- Preview and edit descriptions if needed
- Configure upload options
- Click **"Start Upload"**

#### 3. **Track Progress**
- Watch the **progress bar** during upload
- View **success/error messages**
- Access uploaded images immediately

### Technical Details

#### **File Validation**
```python
# Automatic validation for:
- File format (image types only)
- File size (max 5MB per file)
- Total size (max 100MB per batch)
- File count (max 20 files)
```

#### **Workflow Integration**
- **Before images**: Can upload when custody is `to_approve`, `approved`, or `returned`
- **After images**: Can upload when custody is `approved` or `returned`
- **Damage images**: Can upload when custody is `approved` or `returned`

#### **Permission Control**
- Only **HR users** or **property approvers** can upload images
- State-based restrictions ensure proper workflow
- Automatic user tracking for audit trail

### Browser Compatibility
- **Chrome** ✅
- **Firefox** ✅ 
- **Safari** ✅
- **Edge** ✅

### Performance Notes
- Uses **client-side image processing** for speed
- **Asynchronous upload** prevents browser freezing
- **Memory efficient** - processes one file at a time
- **Network optimized** - validates before sending

### Migration from Single Upload
- **Existing single upload** buttons still work
- **No data migration needed**
- **Backward compatible** with existing workflows
- **New buttons added** alongside existing ones

### Troubleshooting

#### Common Issues:
1. **"Upload zone not responding"**
   - Check browser JavaScript is enabled
   - Refresh the page and try again

2. **"File size too large"**
   - Compress images before upload
   - Maximum 5MB per image

3. **"Upload failed"**
   - Check network connection
   - Ensure proper permissions
   - Try uploading fewer files

4. **"Invalid file format"**
   - Only image files allowed
   - Supported: JPEG, PNG, GIF, WebP, BMP

### Developer Notes

#### **New Models Added:**
- `custody.image.upload.wizard` - Handles multiple upload process

#### **New Methods in hr.custody:**
- `action_upload_before_images()` - Opens before images wizard
- `action_upload_after_images()` - Opens after images wizard  
- `action_upload_damage_images()` - Opens damage images wizard

#### **Assets Added:**
- `static/src/css/custody_image_upload.css` - Upload UI styles
- `static/src/js/custody_image_upload.js` - Upload functionality

#### **Security Considerations:**
- File type validation on both client and server
- Size limits enforced at multiple levels
- User permission checks before upload
- Audit trail for all uploaded images

### Future Enhancements
- [ ] **Bulk resize** option for large images
- [ ] **Cloud storage** integration (AWS S3, Google Drive)
- [ ] **Image annotation** tools
- [ ] **AI-powered** damage detection
- [ ] **Mobile app** support for direct camera upload

### Support
For technical support or feature requests:
- Create an issue in the repository
- Contact the development team
- Check the documentation for updates

---

## Installation Notes

### Requirements
- **Odoo 18.0 CE**
- **Python 3.8+**
- **Modern web browser** with JavaScript enabled

### Upgrade from Previous Version
1. **Backup** your database
2. **Update** the module
3. **Restart** Odoo server
4. **Test** upload functionality

### Configuration
No additional configuration required - the feature is ready to use immediately after installation.

---

*Last updated: June 10, 2025*
*Version: 18.0.1.2.0*
