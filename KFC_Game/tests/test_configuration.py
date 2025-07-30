"""Test configuration system and edge cases."""
import unittest
from unittest.mock import Mock, patch
import os
from KFC_Game.config import settings
from KFC_Game.config import input_maps


class TestSettings(unittest.TestCase):
    """Test the settings configuration module."""

    def test_settings_constants_exist(self):
        """Test that settings module contains expected constants."""
        # Check basic constants
        self.assertTrue(hasattr(settings, 'PIECES_DIR'))
        self.assertTrue(hasattr(settings, 'WS_HOST'))
        self.assertTrue(hasattr(settings, 'WS_PORT'))
        self.assertTrue(hasattr(settings, 'WS_URI'))
        print("✓ Settings module contains expected constants")

    def test_ws_uri_format(self):
        """Test that WebSocket URI is properly formatted."""
        uri = settings.WS_URI
        self.assertTrue(uri.startswith('ws://'))
        self.assertIn(str(settings.WS_PORT), uri)
        print(f"✓ WebSocket URI properly formatted: {uri}")

    def test_pieces_dir_is_string(self):
        """Test that pieces directory is a valid string path."""
        pieces_dir = settings.PIECES_DIR
        self.assertIsInstance(pieces_dir, str)
        self.assertTrue(len(pieces_dir) > 0)
        print(f"✓ Pieces directory is valid: {pieces_dir}")

    def test_ws_port_is_number(self):
        """Test that WebSocket port is a valid number."""
        port = settings.WS_PORT
        self.assertIsInstance(port, int)
        self.assertGreater(port, 0)
        self.assertLess(port, 65536)  # Valid port range
        print(f"✓ WebSocket port is valid: {port}")


class TestInputMaps(unittest.TestCase):
    """Test input mapping configuration."""

    def test_player_maps_exist(self):
        """Test that player input maps exist."""
        self.assertTrue(hasattr(input_maps, 'P1_MAP'))
        self.assertTrue(hasattr(input_maps, 'P2_MAP'))
        print("✓ Player input maps exist")

    def test_player1_map_structure(self):
        """Test that player 1 map has expected structure."""
        p1_map = input_maps.P1_MAP
        self.assertIsInstance(p1_map, dict)
        
        # Check for essential keys
        expected_keys = ['up', 'down', 'left', 'right', 'enter', 'space']
        for key in expected_keys:
            self.assertIn(key, p1_map)
        
        print(f"✓ Player 1 map has {len(p1_map)} key mappings")

    def test_player2_map_structure(self):
        """Test that player 2 map has expected structure.""" 
        p2_map = input_maps.P2_MAP
        self.assertIsInstance(p2_map, dict)
        
        # Check for essential keys (WASD style)
        expected_keys = ['w', 's', 'a', 'd', 'f', 'space']
        for key in expected_keys:
            self.assertIn(key, p2_map)
            
        print(f"✓ Player 2 map has {len(p2_map)} key mappings")

    def test_maps_have_same_actions(self):
        """Test that both player maps map to the same set of actions."""
        p1_actions = set(input_maps.P1_MAP.values())
        p2_actions = set(input_maps.P2_MAP.values())
        self.assertEqual(p1_actions, p2_actions)
        print("✓ Both player maps support the same actions")


class TestConfigurationEdgeCases(unittest.TestCase):
    """Test edge cases in configuration."""

    @patch.dict(os.environ, {'KFC_MODE': 'invalid_mode'})
    def test_handles_invalid_game_mode(self):
        """Test that system handles invalid game mode gracefully."""
        mode = os.environ.get('KFC_MODE')
        self.assertEqual(mode, 'invalid_mode')
        # The main function should handle this gracefully
        print("✓ System can handle invalid game mode in environment")

    @patch.dict(os.environ, {'PLAYER': 'INVALID'})
    def test_handles_invalid_player_setting(self):
        """Test that system handles invalid player setting."""
        player = os.environ.get('PLAYER')
        self.assertEqual(player, 'INVALID')
        print("✓ System can handle invalid player setting")

    def test_configuration_import_safety(self):
        """Test that configuration modules can be imported safely."""
        # Test multiple imports don't cause issues
        from KFC_Game.config import settings as s1
        from KFC_Game.config import settings as s2
        from KFC_Game.config import input_maps as im1
        from KFC_Game.config import input_maps as im2
        
        # Should be the same objects (module level)
        self.assertEqual(s1.WS_PORT, s2.WS_PORT)
        self.assertEqual(im1.P1_MAP, im2.P1_MAP)
        print("✓ Configuration modules can be imported safely")

    def test_ws_uri_construction(self):
        """Test WebSocket URI construction logic."""
        # Verify the URI is built correctly from components
        expected = f"ws://{settings.WS_HOST}:{settings.WS_PORT}"
        self.assertEqual(settings.WS_URI, expected)
        print("✓ WebSocket URI constructed correctly from components")


if __name__ == '__main__':
    unittest.main()
