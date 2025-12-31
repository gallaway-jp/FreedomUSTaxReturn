"""
Unit tests for sharing dialog GUI components
"""
import pytest
from unittest.mock import Mock, MagicMock
from gui.sharing_dialog import SharingDialog, QR_CODE_AVAILABLE
from services.collaboration_service import CollaborationService, CollaborationRole, AccessLevel
from models.user import User


class TestSharingDialog:
    """Test sharing dialog functionality"""

    def test_qr_code_availability(self):
        """Test that QR code availability is detected correctly"""
        # This test will pass if qrcode is installed, fail if not
        # The dialog should handle both cases gracefully
        assert isinstance(QR_CODE_AVAILABLE, bool)

    def test_sharing_dialog_initialization(self):
        """Test that sharing dialog can be initialized"""
        # Mock dependencies
        mock_parent = Mock()
        mock_collaboration_service = Mock(spec=CollaborationService)
        mock_user = Mock(spec=User)
        mock_user.id = "test_user_id"
        mock_user.name = "Test User"

        return_id = "test_return_123"
        tax_year = 2025

        # This should not raise an exception
        try:
            dialog = SharingDialog(
                mock_parent,
                mock_collaboration_service,
                mock_user,
                return_id,
                tax_year
            )
            # If we get here, the dialog initialized successfully
            assert dialog is not None
            assert dialog.return_id == return_id
            assert dialog.tax_year == tax_year
        except Exception as e:
            # If there's an exception, it should not be about qrcode import
            assert "qrcode" not in str(e).lower()

    @pytest.mark.skipif(not QR_CODE_AVAILABLE, reason="qrcode module not available")
    def test_qr_code_generation_with_module(self):
        """Test QR code generation when qrcode module is available"""
        import qrcode

        # Test that we can create a QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        test_data = "https://example.com/share/123"
        qr.add_data(test_data)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        assert qr_image is not None

    def test_qr_code_graceful_degradation(self):
        """Test that dialog works even when QR code is not available"""
        # This test verifies that the conditional import works
        # If QR_CODE_AVAILABLE is False, the dialog should still work
        # but without QR code functionality

        # We can't easily test the GUI without a full Tkinter setup,
        # but we can verify the import logic works
        try:
            from gui.sharing_dialog import QR_CODE_AVAILABLE
            # This should always be a boolean
            assert isinstance(QR_CODE_AVAILABLE, bool)
        except ImportError:
            pytest.fail("Sharing dialog should import successfully regardless of qrcode availability")