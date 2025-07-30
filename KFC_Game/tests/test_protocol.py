"""Test protocol and network communication edge cases."""
import unittest
from unittest.mock import Mock, patch, AsyncMock
import json
from KFC_Game.network.protocol import command_to_json, command_from_json, event_to_json, event_from_json
from KFC_Game.shared.event import Event, EventType
from KFC_Game.shared.command import Command


class TestProtocolCommands(unittest.TestCase):
    """Test protocol command serialization/deserialization."""

    def test_command_serialization(self):
        """Test that commands can be serialized to JSON."""
        cmd = Command(timestamp=1000, piece_id="PW_1", type="move", params=[(0, 0), (1, 1)])
        
        json_str = command_to_json(cmd)
        self.assertIsInstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        self.assertEqual(parsed["piece_id"], "PW_1")
        self.assertEqual(parsed["type"], "move")
        print("✓ Commands can be serialized to JSON")

    def test_command_deserialization(self):
        """Test that commands can be deserialized from JSON."""
        cmd = Command(timestamp=1500, piece_id="QB_2", type="jump", params=[(2, 2)])
        
        # Serialize and deserialize
        json_str = command_to_json(cmd)
        restored_cmd = command_from_json(json_str)
        
        self.assertEqual(restored_cmd.piece_id, "QB_2")
        self.assertEqual(restored_cmd.type, "jump")
        self.assertEqual(restored_cmd.params, [(2, 2)])
        print("✓ Commands can be deserialized from JSON")

    def test_command_with_tuple_params(self):
        """Test command serialization with tuple parameters."""
        cmd = Command(timestamp=2000, piece_id="NW_3", type="move", params=[(3, 4), (5, 6)])
        
        json_str = command_to_json(cmd)
        restored_cmd = command_from_json(json_str)
        
        # Tuples should be preserved
        self.assertEqual(restored_cmd.params[0], (3, 4))
        self.assertEqual(restored_cmd.params[1], (5, 6))
        print("✓ Command tuple parameters are preserved")

    def test_command_with_empty_params(self):
        """Test command with no parameters."""
        cmd = Command(timestamp=2500, piece_id="KW_1", type="idle", params=[])
        
        json_str = command_to_json(cmd)
        restored_cmd = command_from_json(json_str)
        
        self.assertEqual(restored_cmd.params, [])
        print("✓ Commands with empty parameters work correctly")


class TestProtocolEvents(unittest.TestCase):
    """Test protocol event serialization/deserialization."""

    def test_event_serialization(self):
        """Test that events can be serialized to JSON."""
        event = Event(type=EventType.PIECE_MOVED, payload={"from": [0, 0], "to": [1, 1]}, timestamp=3000)
        
        json_str = event_to_json(event)
        self.assertIsInstance(json_str, str)
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        self.assertEqual(parsed["type"], EventType.PIECE_MOVED.value)
        print("✓ Events can be serialized to JSON")

    def test_event_deserialization(self):
        """Test that events can be deserialized from JSON."""
        event = Event(type=EventType.CAPTURE, payload={"piece": "P", "player": "white"}, timestamp=3500)
        
        # Serialize and deserialize
        json_str = event_to_json(event)
        restored_event = event_from_json(json_str)
        
        self.assertEqual(restored_event.type, EventType.CAPTURE)
        self.assertEqual(restored_event.payload["piece"], "P")
        self.assertEqual(restored_event.timestamp, 3500)
        print("✓ Events can be deserialized from JSON")

    def test_event_with_empty_payload(self):
        """Test event with empty payload."""
        event = Event(type=EventType.GAME_STARTED, payload={}, timestamp=4000)
        
        json_str = event_to_json(event)
        restored_event = event_from_json(json_str)
        
        self.assertEqual(restored_event.payload, {})
        print("✓ Events with empty payload work correctly")

    def test_event_types_exist(self):
        """Test that EventType enumeration has expected values."""
        # Check for essential event types
        essential_types = ['GAME_STARTED', 'PIECE_MOVED', 'CAPTURE', 'GAME_ENDED']
        
        for event_type in essential_types:
            self.assertTrue(hasattr(EventType, event_type))
        
        print(f"✓ EventType has essential event types")


class TestProtocolEdgeCases(unittest.TestCase):
    """Test edge cases in protocol handling."""

    def test_malformed_command_json(self):
        """Test handling of malformed command JSON."""
        malformed_json = '{"timestamp": 1000, "piece_id": "incomplete'
        
        # Should raise an exception when parsing
        with self.assertRaises(json.JSONDecodeError):
            command_from_json(malformed_json)
        
        print("✓ Malformed command JSON properly raises exceptions")

    def test_malformed_event_json(self):
        """Test handling of malformed event JSON."""
        malformed_json = '{"type": "GAME_STARTED", "payload": incomplete'
        
        # Should raise an exception when parsing
        with self.assertRaises(json.JSONDecodeError):
            event_from_json(malformed_json)
        
        print("✓ Malformed event JSON properly raises exceptions")

    def test_command_missing_fields(self):
        """Test command deserialization with missing fields."""
        # Missing required field should raise KeyError
        incomplete_json = '{"timestamp": 1000, "type": "move"}'  # missing piece_id
        
        with self.assertRaises(KeyError):
            command_from_json(incomplete_json)
        
        print("✓ Commands with missing fields raise appropriate errors")

    def test_large_payload_handling(self):
        """Test handling of large payloads."""
        # Create a large payload
        large_payload = {"data": ["item"] * 1000}
        event = Event(type=EventType.STATE_SNAPSHOT, payload=large_payload, timestamp=5000)
        
        json_str = event_to_json(event)
        restored_event = event_from_json(json_str)
        
        self.assertEqual(len(restored_event.payload["data"]), 1000)
        print("✓ Large payloads are handled correctly")

    def test_unicode_in_protocol(self):
        """Test handling of unicode characters in protocol."""
        cmd = Command(timestamp=5500, piece_id="测试_1", type="move", params=[(0, 0)])
        
        json_str = command_to_json(cmd)
        restored_cmd = command_from_json(json_str)
        
        self.assertEqual(restored_cmd.piece_id, "测试_1")
        print("✓ Unicode characters in protocol are handled correctly")


class TestProtocolIntegration(unittest.TestCase):
    """Test integration aspects of the protocol."""

    def test_round_trip_command_consistency(self):
        """Test that command round-trip preserves all data."""
        original_cmd = Command(
            timestamp=6000,
            piece_id="RB_8", 
            type="castle",
            params=[(0, 0), (0, 3), (0, 7), (0, 5)],
            cmd_id="test_123"
        )
        
        # Full round trip
        json_str = command_to_json(original_cmd)
        restored_cmd = command_from_json(json_str)
        
        # All fields should match
        self.assertEqual(restored_cmd.timestamp, original_cmd.timestamp)
        self.assertEqual(restored_cmd.piece_id, original_cmd.piece_id)
        self.assertEqual(restored_cmd.type, original_cmd.type)
        self.assertEqual(restored_cmd.params, original_cmd.params)
        self.assertEqual(restored_cmd.cmd_id, original_cmd.cmd_id)
        print("✓ Command round-trip preserves all data")

    def test_round_trip_event_consistency(self):
        """Test that event round-trip preserves all data."""
        original_event = Event(
            type=EventType.GAME_ENDED,
            payload={"winner": "black", "reason": "checkmate"},
            timestamp=6500
        )
        
        # Full round trip
        json_str = event_to_json(original_event)
        restored_event = event_from_json(json_str)
        
        # All fields should match
        self.assertEqual(restored_event.type, original_event.type)
        self.assertEqual(restored_event.payload, original_event.payload)
        self.assertEqual(restored_event.timestamp, original_event.timestamp)
        print("✓ Event round-trip preserves all data")

    def test_protocol_type_safety(self):
        """Test that protocol maintains type safety."""
        # Timestamps should be integers
        cmd = Command(timestamp=7000, piece_id="PW_1", type="select", params=[])
        json_str = command_to_json(cmd)
        restored = command_from_json(json_str)
        
        self.assertIsInstance(restored.timestamp, int)
        print("✓ Protocol maintains type safety")


if __name__ == '__main__':
    unittest.main()
