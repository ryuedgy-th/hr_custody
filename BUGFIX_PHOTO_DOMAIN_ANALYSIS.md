# 🚨 CRITICAL BUGFIX: Photo Category Domain Separation 

## Root Cause Analysis

After thorough investigation, the issue was found in the **view layer**, not the model:

### ❌ **Problem Identified:**
- Model correctly defines `handover_photo_ids` and `return_photo_ids` as separate fields
- BUT XML view incorrectly uses `attachment_ids` for both upload widgets
- This causes photos uploaded in Return tab to show in Handover tab

### ✅ **Solution:**
- Use the correct field names in XML view:
  - **Handover tab**: Use `handover_photo_ids` 
  - **Return tab**: Use `return_photo_ids`
- Remove the shared `attachment_ids` field usage
- Ensure proper domain separation at view level

### 🔧 **Technical Fix:**

**Before (Incorrect):**
```xml
<!-- Both tabs incorrectly using same field -->
<field name="attachment_ids" widget="many2many_binary" domain="[('custody_photo_type', 'in', ['handover_...'])]"/>
<field name="attachment_ids" widget="many2many_binary" domain="[('custody_photo_type', 'in', ['return_...'])]"/>
```

**After (Correct):**
```xml
<!-- Handover tab uses dedicated field -->
<field name="handover_photo_ids" widget="many2many_binary"/>
<!-- Return tab uses dedicated field -->  
<field name="return_photo_ids" widget="many2many_binary"/>
```

### 🎯 **Result:**
- Photos uploaded in Handover tab will only appear in Handover gallery
- Photos uploaded in Return tab will only appear in Return gallery  
- Clean separation of photo workflows
- No more cross-contamination between photo categories

### 📋 **Files to Update:**
- `views/hr_custody_views.xml` - Update field references in upload widgets and gallery displays
- Test thoroughly to ensure proper separation

This fix addresses the fundamental issue while maintaining all existing functionality.