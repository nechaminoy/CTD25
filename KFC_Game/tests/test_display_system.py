import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from ..client.display import NullDisplay, Cv2Display


class TestNullDisplay:
    """Test the NullDisplay class - headless display for testing/servers."""
    
    def test_null_display_present_does_nothing(self):
        """NullDisplay.present should be a no-op."""
        display = NullDisplay()
        
        # Should not raise any exceptions
        display.present(None)
        display.present(np.zeros((100, 100, 3), dtype=np.uint8))
        
    def test_null_display_close_does_nothing(self):
        """NullDisplay.close should be a no-op."""
        display = NullDisplay()
        
        # Should not raise any exceptions
        display.close()


class TestCv2Display:
    """Test the Cv2Display class - OpenCV-based display."""
    
    @patch('cv2.namedWindow')
    def test_cv2_display_init_creates_window(self, mock_named_window):
        """Cv2Display should create a named window on initialization."""
        with patch('cv2.WINDOW_AUTOSIZE', 1):
            display = Cv2Display("Test Window")
            
            mock_named_window.assert_called_once_with("Test Window", 1)
            assert display.window_name == "Test Window"
    
    @patch('cv2.namedWindow')
    def test_cv2_display_default_window_name(self, mock_named_window):
        """Cv2Display should use default window name if none provided."""
        with patch('cv2.WINDOW_AUTOSIZE', 1):
            display = Cv2Display()
            
            mock_named_window.assert_called_once_with("Kung Fu Chess", 1)
            assert display.window_name == "Kung Fu Chess"
    
    @patch('cv2.namedWindow')
    @patch('cv2.imshow')
    @patch('cv2.waitKey')
    def test_present_bgr_image(self, mock_wait_key, mock_imshow, mock_named_window):
        """Should display BGR image directly."""
        with patch('cv2.WINDOW_AUTOSIZE', 1):
            display = Cv2Display("Test")
            
            # Create a BGR image (3 channels)
            bgr_image = np.zeros((100, 100, 3), dtype=np.uint8)
            
            display.present(bgr_image)
            
            mock_imshow.assert_called_once_with("Test", bgr_image)
            mock_wait_key.assert_called_once_with(1)
    
    @patch('cv2.namedWindow')
    @patch('cv2.imshow')
    @patch('cv2.waitKey')
    @patch('cv2.cvtColor')
    @patch('cv2.COLOR_BGRA2BGR', 42)  # Mock constant
    def test_present_bgra_image_converts_to_bgr(self, mock_cvt_color, mock_wait_key, mock_imshow, mock_named_window):
        """Should convert BGRA image to BGR before displaying."""
        with patch('cv2.WINDOW_AUTOSIZE', 1):
            display = Cv2Display("Test")
            
            # Create a BGRA image (4 channels)
            bgra_image = np.zeros((100, 100, 4), dtype=np.uint8)
            converted_bgr = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_cvt_color.return_value = converted_bgr
            
            display.present(bgra_image)
            
            mock_cvt_color.assert_called_once_with(bgra_image, 42)  # COLOR_BGRA2BGR
            mock_imshow.assert_called_once_with("Test", converted_bgr)
            mock_wait_key.assert_called_once_with(1)
    
    @patch('cv2.namedWindow')
    def test_present_none_image_logs_error(self, mock_named_window):
        """Should log error and return early when image is None."""
        with patch('cv2.WINDOW_AUTOSIZE', 1):
            display = Cv2Display("Test")
            
            with patch('logging.error') as mock_log_error:
                display.present(None)
                
                mock_log_error.assert_called_once_with("Display received None image")
    
    @patch('cv2.namedWindow')
    @patch('cv2.destroyWindow')
    def test_close_destroys_window(self, mock_destroy_window, mock_named_window):
        """Should destroy the OpenCV window on close."""
        with patch('cv2.WINDOW_AUTOSIZE', 1):
            display = Cv2Display("Test")
            
            display.close()
            
            mock_destroy_window.assert_called_once_with("Test")
    
    @patch('cv2.namedWindow')
    @patch('cv2.destroyWindow')
    def test_close_handles_exceptions(self, mock_destroy_window, mock_named_window):
        """Should handle exceptions during window destruction gracefully."""
        with patch('cv2.WINDOW_AUTOSIZE', 1):
            display = Cv2Display("Test")
            
            # Make destroyWindow raise an exception
            mock_destroy_window.side_effect = Exception("Test error")
            
            # Should not raise exception
            display.close()
            
            mock_destroy_window.assert_called_once_with("Test")
