# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustodyPhotoTests(models.TransientModel):
    """
    Photo Management Testing Helper
    
    This wizard helps test and validate photo upload workflows
    """
    _name = 'hr.custody.photo.tests'
    _description = 'HR Custody Photo Testing Wizard'

    custody_id = fields.Many2one(
        'hr.custody',
        string='Custody Record',
        required=True,
        help='Custody record to test photo functionality'
    )
    
    test_type = fields.Selection([
        ('upload_handover', '📸 Test Handover Photo Upload'),
        ('upload_return', '📦 Test Return Photo Upload'),
        ('quality_assessment', '📊 Test Quality Assessment'),
        ('photo_comparison', '🔍 Test Photo Comparison'),
        ('bulk_operations', '🧙‍♂️ Test Bulk Operations'),
        ('mobile_simulation', '📱 Test Mobile Workflow'),
        ('performance_test', '⚡ Test Performance'),
    ], string='Test Type', required=True, default='upload_handover')
    
    test_photos = fields.Many2many(
        'ir.attachment',
        string='Test Photos',
        help='Sample photos for testing'
    )
    
    test_results = fields.Html(
        string='Test Results',
        readonly=True,
        help='Results of the photo tests'
    )
    
    # Test configuration
    simulate_mobile = fields.Boolean(
        string='Simulate Mobile Upload',
        help='Simulate mobile device photo upload'
    )
    
    test_large_files = fields.Boolean(
        string='Test Large Files',
        help='Test with larger photo files'
    )
    
    test_quality_variants = fields.Boolean(
        string='Test Quality Variants',
        help='Test photos with different quality levels'
    )

    def action_run_tests(self):
        """Run the selected photo tests"""
        self.ensure_one()
        
        if self.test_type == 'upload_handover':
            return self._test_handover_upload()
        elif self.test_type == 'upload_return':
            return self._test_return_upload()
        elif self.test_type == 'quality_assessment':
            return self._test_quality_assessment()
        elif self.test_type == 'photo_comparison':
            return self._test_photo_comparison()
        elif self.test_type == 'bulk_operations':
            return self._test_bulk_operations()
        elif self.test_type == 'mobile_simulation':
            return self._test_mobile_workflow()
        elif self.test_type == 'performance_test':
            return self._test_performance()
    
    def _test_handover_upload(self):
        """Test handover photo upload workflow"""
        results = []
        results.append('<h3>📸 Handover Photo Upload Test</h3>')
        
        # Test 1: Basic upload functionality
        results.append('<h4>Test 1: Basic Upload</h4>')
        try:
            if self.test_photos:
                for photo in self.test_photos:
                    photo.write({
                        'res_model': 'hr.custody',
                        'res_id': self.custody_id.id,
                        'custody_photo_type': 'handover_overall'
                    })
                results.append('✅ Photo upload successful<br/>')
                results.append(f'📊 Uploaded {len(self.test_photos)} photos<br/>')
            else:
                results.append('⚠️ No test photos provided<br/>')
        except Exception as e:
            results.append(f'❌ Upload failed: {str(e)}<br/>')
        
        # Test 2: Photo categorization
        results.append('<h4>Test 2: Photo Categorization</h4>')
        try:
            handover_types = ['handover_overall', 'handover_detail', 'handover_serial']
            for i, photo in enumerate(self.test_photos[:3]):
                if i < len(handover_types):
                    photo.custody_photo_type = handover_types[i]
            results.append('✅ Photo categorization successful<br/>')
        except Exception as e:
            results.append(f'❌ Categorization failed: {str(e)}<br/>')
        
        # Test 3: Computed fields update
        results.append('<h4>Test 3: Computed Fields</h4>')
        try:
            self.custody_id._compute_photo_counts()
            self.custody_id._compute_photo_status()
            results.append(f'✅ Handover photo count: {self.custody_id.handover_photo_count}<br/>')
            results.append(f'✅ Has handover photos: {self.custody_id.has_handover_photos}<br/>')
        except Exception as e:
            results.append(f'❌ Computed fields failed: {str(e)}<br/>')
        
        self.test_results = ''.join(results)
        return self._show_results()
    
    def _test_return_upload(self):
        """Test return photo upload workflow"""
        results = []
        results.append('<h3>📦 Return Photo Upload Test</h3>')
        
        # Only test if custody is in returned state
        if self.custody_id.state != 'returned':
            results.append('⚠️ Custody must be in "Returned" state for return photo tests<br/>')
            results.append('Setting custody to returned state for testing...<br/>')
            self.custody_id.state = 'returned'
        
        # Test return photo upload
        try:
            if self.test_photos:
                for photo in self.test_photos:
                    photo.write({
                        'res_model': 'hr.custody',
                        'res_id': self.custody_id.id,
                        'custody_photo_type': 'return_overall'
                    })
                results.append('✅ Return photo upload successful<br/>')
                
                # Test photo comparison
                self.custody_id._compute_photo_status()
                results.append(f'✅ Return photo count: {self.custody_id.return_photo_count}<br/>')
                results.append(f'✅ Photos complete: {self.custody_id.photos_complete}<br/>')
            else:
                results.append('⚠️ No test photos provided<br/>')
        except Exception as e:
            results.append(f'❌ Return upload failed: {str(e)}<br/>')
        
        self.test_results = ''.join(results)
        return self._show_results()
    
    def _test_quality_assessment(self):
        """Test photo quality assessment system"""
        results = []
        results.append('<h3>📊 Photo Quality Assessment Test</h3>')
        
        # Test quality scoring
        for photo in self.test_photos:
            try:
                # Set test dimensions
                photo.write({
                    'photo_width': 1920,
                    'photo_height': 1080,
                    'mimetype': 'image/jpeg'
                })
                
                # Trigger quality computation
                photo._compute_photo_quality()
                
                results.append(f'📸 Photo: {photo.name}<br/>')
                results.append(f'🎯 Quality Score: {photo.quality_score:.1f}/100<br/>')
                results.append(f'⭐ High Quality: {photo.is_high_quality}<br/>')
                results.append(f'📏 Dimensions: {photo.photo_width}x{photo.photo_height}<br/>')
                results.append(f'💾 Size: {photo.photo_size_mb:.2f} MB<br/><br/>')
                
            except Exception as e:
                results.append(f'❌ Quality assessment failed for {photo.name}: {str(e)}<br/>')
        
        self.test_results = ''.join(results)
        return self._show_results()
    
    def _test_photo_comparison(self):
        """Test photo comparison functionality"""
        results = []
        results.append('<h3>🔍 Photo Comparison Test</h3>')
        
        try:
            # Get photo summaries
            handover_summary = self.custody_id.get_handover_photos_summary()
            return_summary = self.custody_id.get_return_photos_summary()
            
            results.append('<h4>Handover Photos Summary:</h4>')
            for photo_type, data in handover_summary.items():
                results.append(f'• {photo_type}: {data["count"]} photos<br/>')
            
            results.append('<h4>Return Photos Summary:</h4>')
            for photo_type, data in return_summary.items():
                results.append(f'• {photo_type}: {data["count"]} photos<br/>')
            
            # Test condition analysis
            if hasattr(self.custody_id, 'analyze_condition_change'):
                analysis = self.custody_id.analyze_condition_change()
                results.append('<h4>Condition Analysis:</h4>')
                results.append(f'• Assessment: {analysis.get("condition_assessment", "N/A")}<br/>')
                results.append(f'• Requires Review: {analysis.get("requires_review", False)}<br/>')
            
        except Exception as e:
            results.append(f'❌ Photo comparison failed: {str(e)}<br/>')
        
        self.test_results = ''.join(results)
        return self._show_results()
    
    def _test_bulk_operations(self):
        """Test bulk photo operations"""
        results = []
        results.append('<h3>🧙‍♂️ Bulk Operations Test</h3>')
        
        try:
            # Test bulk categorization
            if self.test_photos:
                self.test_photos.action_set_photo_type('handover_overall')
                results.append(f'✅ Bulk categorization: {len(self.test_photos)} photos set to handover_overall<br/>')
                
                # Test bulk notes addition
                test_notes = "Bulk test notes - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.test_photos.write({'custody_notes': test_notes})
                results.append('✅ Bulk notes addition successful<br/>')
                
                # Test photo analytics
                analytics = self.env['ir.attachment'].get_custody_photo_analytics()
                results.append('<h4>Photo Analytics:</h4>')
                results.append(f'• Total Photos: {analytics.get("total_photos", 0)}<br/>')
                results.append(f'• Average Quality: {analytics.get("avg_quality_score", 0):.1f}<br/>')
                results.append(f'• High Quality %: {analytics.get("high_quality_percentage", 0):.1f}%<br/>')
            else:
                results.append('⚠️ No test photos provided for bulk operations<br/>')
                
        except Exception as e:
            results.append(f'❌ Bulk operations failed: {str(e)}<br/>')
        
        self.test_results = ''.join(results)
        return self._show_results()
    
    def _test_mobile_workflow(self):
        """Test mobile-optimized workflow"""
        results = []
        results.append('<h3>📱 Mobile Workflow Test</h3>')
        
        # Simulate mobile photo characteristics
        mobile_characteristics = {
            'photo_width': 1080,  # Portrait mode
            'photo_height': 1920,
            'mimetype': 'image/jpeg',
            'custody_location': 'Mobile GPS: 13.7563, 100.5018',  # Bangkok coordinates
        }
        
        try:
            for photo in self.test_photos:
                photo.write(mobile_characteristics)
                photo._compute_photo_quality()
                
                results.append(f'📱 Mobile photo: {photo.name}<br/>')
                results.append(f'📏 Portrait: {photo.photo_width}x{photo.photo_height}<br/>')
                results.append(f'📍 Location: {photo.custody_location}<br/>')
                results.append(f'🎯 Quality: {photo.quality_score:.1f}<br/><br/>')
            
            results.append('✅ Mobile workflow simulation complete<br/>')
            
        except Exception as e:
            results.append(f'❌ Mobile workflow test failed: {str(e)}<br/>')
        
        self.test_results = ''.join(results)
        return self._show_results()
    
    def _test_performance(self):
        """Test photo system performance"""
        results = []
        results.append('<h3>⚡ Performance Test</h3>')
        
        try:
            start_time = datetime.now()
            
            # Test 1: Photo count computation performance
            test_start = datetime.now()
            self.custody_id._compute_photo_counts()
            compute_time = (datetime.now() - test_start).total_seconds()
            results.append(f'📊 Photo count computation: {compute_time:.3f}s<br/>')
            
            # Test 2: Photo status computation performance
            test_start = datetime.now()
            self.custody_id._compute_photo_status()
            status_time = (datetime.now() - test_start).total_seconds()
            results.append(f'📊 Photo status computation: {status_time:.3f}s<br/>')
            
            # Test 3: Quality assessment performance
            if self.test_photos:
                test_start = datetime.now()
                for photo in self.test_photos:
                    photo._compute_photo_quality()
                quality_time = (datetime.now() - test_start).total_seconds()
                results.append(f'📊 Quality assessment ({len(self.test_photos)} photos): {quality_time:.3f}s<br/>')
            
            # Test 4: Analytics performance
            test_start = datetime.now()
            analytics = self.env['ir.attachment'].get_custody_photo_analytics()
            analytics_time = (datetime.now() - test_start).total_seconds()
            results.append(f'📊 Analytics computation: {analytics_time:.3f}s<br/>')
            
            total_time = (datetime.now() - start_time).total_seconds()
            results.append(f'<br/>⚡ Total test time: {total_time:.3f}s<br/>')
            
            # Performance assessment
            if total_time < 1.0:
                results.append('🟢 Performance: Excellent<br/>')
            elif total_time < 3.0:
                results.append('🟡 Performance: Good<br/>')
            else:
                results.append('🔴 Performance: Needs optimization<br/>')
                
        except Exception as e:
            results.append(f'❌ Performance test failed: {str(e)}<br/>')
        
        self.test_results = ''.join(results)
        return self._show_results()
    
    def _show_results(self):
        """Show test results in a popup"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Photo Test Results'),
            'res_model': 'hr.custody.photo.tests',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'form_view_ref': 'hr_custody.hr_custody_photo_tests_results_view'}
        }
    
    def action_generate_test_photos(self):
        """Generate sample test photos for testing"""
        # This would create sample attachments for testing
        # In a real implementation, this might create placeholder images
        
        test_photo_data = [
            {
                'name': 'test_handover_overall.jpg',
                'mimetype': 'image/jpeg',
                'res_model': 'hr.custody',
                'res_id': self.custody_id.id,
                'custody_photo_type': 'handover_overall',
                'photo_width': 1920,
                'photo_height': 1080,
                'file_size': 2048000,  # 2MB
            },
            {
                'name': 'test_handover_detail.jpg', 
                'mimetype': 'image/jpeg',
                'res_model': 'hr.custody',
                'res_id': self.custody_id.id,
                'custody_photo_type': 'handover_detail',
                'photo_width': 1920,
                'photo_height': 1080,
                'file_size': 1536000,  # 1.5MB
            },
            {
                'name': 'test_return_overall.jpg',
                'mimetype': 'image/jpeg', 
                'res_model': 'hr.custody',
                'res_id': self.custody_id.id,
                'custody_photo_type': 'return_overall',
                'photo_width': 1920,
                'photo_height': 1080,
                'file_size': 2304000,  # 2.25MB
            }
        ]
        
        test_photos = self.env['ir.attachment'].create(test_photo_data)
        self.test_photos = [(6, 0, test_photos.ids)]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Generated {len(test_photos)} test photos',
                'type': 'success',
                'sticky': False,
            }
        }
