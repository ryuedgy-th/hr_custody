# Open HRMS Custody - User Guide

## Overview

The Open HRMS Custody module helps organizations manage and track company property in employee custody. It provides a complete workflow for requesting, approving, documenting, and returning company assets.

## Configuration

### Property Categories

Categories help organize properties by type or department.

1. Go to **Custody > Configuration > Categories**
2. Click **Create** to add a new category
3. Fill in the following fields:
   - **Category Name**: Name of the category (e.g., "IT Equipment")
   - **Category Code**: Optional short code (e.g., "IT")
   - **Parent Category**: Optional parent for hierarchical organization
   - **Default Return Type**: Set default return policy for this category
   - **Color**: Select color for kanban view

### Property Tags

Tags provide flexible labeling for properties.

1. Go to **Custody > Configuration > Tags**
2. Click **Create** to add a new tag
3. Fill in the **Tag Name** and select a **Color**

### Properties

1. Go to **Custody > Properties**
2. Click **Create** to add a new property
3. Fill in the following fields:
   - **Property Name**: Name of the property
   - **Image**: Upload an image of the property
   - **Category**: Select a category
   - **Tags**: Add relevant tags
   - **Property Code**: Unique identifier or asset tag
   - **Storage Location**: Where the property is normally stored
   - **Responsible Department**: Department responsible for this property
   - **Approvers**: Users who can approve custody requests for this property

## Daily Operations

### Creating a Custody Request

1. Go to **Custody > Custody Requests**
2. Click **Create** to create a new request
3. Fill in the following fields:
   - **Employee**: Select the employee requesting custody
   - **Property**: Select the property to be borrowed
   - **Reason**: Explain why the property is needed
   - **Return Type**: Choose between fixed date, flexible, or term-end return
   - **Return Date**: If fixed date, specify when the property will be returned
   - **Expected Return Period**: For flexible returns, provide general timeframe
4. Add **Notes** if needed
5. Upload **Images** to document the property condition
6. Click **Save** and then **Send for Approval**

### Approving a Custody Request

1. Users set as approvers for the property will see pending requests
2. Go to **Custody > Custody Requests** and filter by **Waiting for Approval**
3. Open the request and review the details
4. Click **Approve** to approve or **Refuse** to reject the request
5. If rejecting, provide a reason when prompted

### Recording Property Return

1. Go to **Custody > Custody Requests** and filter by **Approved**
2. Open the custody record to be returned
3. Upload return images to document the property condition
4. Add notes about the return condition if needed
5. Click **Return** to complete the process

## Reporting and Analysis

### Employee Custody Report

1. Go to **Custody > Reports > Employee Custody Report**
2. View statistics on property custody by employee, department, or property type
3. Use filters to narrow down the data

### Property Status Overview

1. Go to **Custody > Properties**
2. Use the **Kanban** view to see property status at a glance
3. Filter by **Available**, **In Use**, or other statuses

## Advanced Features

### Multiple Image Upload

1. When creating or editing a custody record, click **Upload Multiple Images**
2. Select multiple images from your device
3. Add descriptions for each image if needed
4. Click **Upload** to attach all images at once

### Image Comparison

For returned items, compare checkout and return images:

1. Open a returned custody record
2. Click **Compare Images** to view side-by-side comparison
3. Use this to identify any changes in condition

### Email Notifications

The system automatically sends email notifications:

1. When a custody request is created
2. When a request is approved or rejected
3. When a return date is approaching
4. When a property is overdue for return

## Troubleshooting

### Common Issues

1. **Property Not Available**: Ensure the property status is set to "Available"
2. **Cannot Approve Request**: Verify you are set as an approver for the property
3. **Images Not Uploading**: Check file size and format (JPG, PNG recommended)

For additional support, contact your system administrator. 