"""
Tests for the soandso package
"""

import unittest
from soandso import do_a_thing, do_another_thing, do_something_else
from soandso import make_it_fancy, count_stuff, generate_nonsense


class TestSoandso(unittest.TestCase):
    
    def test_do_a_thing(self):
        """Test do_a_thing function"""
        result = do_a_thing("test")
        self.assertIn("test", result)
        self.assertIn("Successfully did", result)
    
    def test_do_another_thing(self):
        """Test do_another_thing function"""
        result = do_another_thing(5)
        self.assertIsInstance(result, dict)
        self.assertTrue(result["thing_done"])
        self.assertEqual(result["intensity_level"], 5)
    
    def test_do_something_else(self):
        """Test do_something_else function"""
        items = ["apple", "banana"]
        result = do_something_else(items)
        self.assertEqual(len(result), 2)
        self.assertTrue(all("processed" in item for item in result))
    
    def test_make_it_fancy(self):
        """Test make_it_fancy function"""
        result = make_it_fancy("test")
        self.assertIn("TEST", result)
        self.assertIn("✨", result)
    
    def test_count_stuff(self):
        """Test count_stuff function"""
        result = count_stuff("hello world")
        self.assertEqual(result["total"], 11)
        self.assertEqual(result["without_spaces"], 10)
    
    def test_generate_nonsense(self):
        """Test generate_nonsense function"""
        result = generate_nonsense(5)
        words = result.split()
        self.assertEqual(len(words), 5)


if __name__ == "__main__":
    unittest.main()