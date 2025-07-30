"""Test the main entry points and their functionality."""
import unittest


class TestMainCore(unittest.TestCase):
    """Test the essential main function behaviors."""

    def test_main_imports_correctly(self):
        """Test that main module can be imported and run functions exist."""
        # Act & Assert - just test the import doesn't crash
        from KFC_Game.main import run_local, run_server
        self.assertTrue(callable(run_local))
        self.assertTrue(callable(run_server))
        print("✓ Main module imports successfully")
        print("✓ run_local and run_server functions are callable")


if __name__ == '__main__':
    unittest.main()
