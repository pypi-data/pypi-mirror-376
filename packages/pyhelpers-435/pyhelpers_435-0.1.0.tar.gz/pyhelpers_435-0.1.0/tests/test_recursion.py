import unittest
import sys
import os

# Add the parent directory to the path to import pyhelpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyhelpers.recursion_utils import fibonacci, search_dict


class TestRecursionUtils(unittest.TestCase):
    """Test cases for recursion utility functions"""
    
    def test_fibonacci_base_cases(self):
        """Test fibonacci with base cases"""
        self.assertEqual(fibonacci(0), 0)
        self.assertEqual(fibonacci(1), 1)
    
    def test_fibonacci_small_values(self):
        """Test fibonacci with small positive values"""
        self.assertEqual(fibonacci(2), 1)  # 0 + 1
        self.assertEqual(fibonacci(3), 2)  # 1 + 1
        self.assertEqual(fibonacci(4), 3)  # 1 + 2
        self.assertEqual(fibonacci(5), 5)  # 2 + 3
        self.assertEqual(fibonacci(6), 8)  # 3 + 5
        self.assertEqual(fibonacci(7), 13) # 5 + 8
    
    def test_fibonacci_negative_values(self):
        """Test fibonacci with negative values"""
        # Note: The current implementation doesn't handle negative values properly
        # This test documents the current behavior
        self.assertEqual(fibonacci(-1), -1)
        self.assertEqual(fibonacci(-5), -5)
    
    def test_fibonacci_larger_values(self):
        """Test fibonacci with larger values"""
        self.assertEqual(fibonacci(10), 55)
        self.assertEqual(fibonacci(15), 610)
        self.assertEqual(fibonacci(20), 6765)
    
    def test_fibonacci_sequence_verification(self):
        """Test that fibonacci follows the correct sequence"""
        expected_sequence = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        for i, expected in enumerate(expected_sequence):
            with self.subTest(i=i):
                self.assertEqual(fibonacci(i), expected)
    
    def test_search_dict_key_exists_top_level(self):
        """Test search_dict when key exists at top level"""
        test_dict = {'name': 'John', 'age': 30, 'city': 'New York'}
        result = search_dict(test_dict, 'age')
        self.assertEqual(result, 30)
    
    def test_search_dict_key_exists_nested(self):
        """Test search_dict when key exists in nested dictionary"""
        test_dict = {
            'user': {
                'name': 'Alice',
                'profile': {
                    'age': 25,
                    'email': 'alice@example.com'
                }
            },
            'status': 'active'
        }
        result = search_dict(test_dict, 'email')
        self.assertEqual(result, 'alice@example.com')
    
    def test_search_dict_key_not_exists(self):
        """Test search_dict when key doesn't exist"""
        test_dict = {'name': 'John', 'age': 30}
        result = search_dict(test_dict, 'salary')
        self.assertIsNone(result)
    
    def test_search_dict_empty_dict(self):
        """Test search_dict with empty dictionary"""
        result = search_dict({}, 'any_key')
        self.assertIsNone(result)
    
    def test_search_dict_deeply_nested(self):
        """Test search_dict with deeply nested dictionaries"""
        test_dict = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'target': 'found'
                        }
                    }
                }
            }
        }
        result = search_dict(test_dict, 'target')
        self.assertEqual(result, 'found')
    
    def test_search_dict_multiple_nested_levels(self):
        """Test search_dict with multiple nested levels"""
        test_dict = {
            'users': [
                {'name': 'Alice', 'details': {'age': 25}},
                {'name': 'Bob', 'details': {'age': 30}}
            ],
            'admin': {
                'name': 'Admin',
                'permissions': {
                    'level': 'super',
                    'access': 'full'
                }
            }
        }
        result = search_dict(test_dict, 'access')
        self.assertEqual(result, 'full')
    
    def test_search_dict_key_in_multiple_places(self):
        """Test search_dict when key exists in multiple places (returns first found)"""
        test_dict = {
            'name': 'John',
            'user': {
                'name': 'Alice',
                'profile': {
                    'name': 'Bob'
                }
            }
        }
        result = search_dict(test_dict, 'name')
        self.assertEqual(result, 'John')  # Should return the first occurrence
    
    def test_search_dict_with_different_value_types(self):
        """Test search_dict with different value types"""
        test_dict = {
            'string_value': 'hello',
            'number_value': 42,
            'boolean_value': True,
            'list_value': [1, 2, 3],
            'nested': {
                'float_value': 3.14,
                'none_value': None
            }
        }
        
        self.assertEqual(search_dict(test_dict, 'string_value'), 'hello')
        self.assertEqual(search_dict(test_dict, 'number_value'), 42)
        self.assertEqual(search_dict(test_dict, 'boolean_value'), True)
        self.assertEqual(search_dict(test_dict, 'list_value'), [1, 2, 3])
        self.assertEqual(search_dict(test_dict, 'float_value'), 3.14)
        self.assertIsNone(search_dict(test_dict, 'none_value'))
    
    def test_search_dict_nested_with_lists(self):
        """Test search_dict with nested dictionaries containing lists"""
        test_dict = {
            'data': {
                'items': [
                    {'id': 1, 'name': 'item1'},
                    {'id': 2, 'name': 'item2'}
                ],
                'config': {
                    'max_items': 100
                }
            }
        }
        result = search_dict(test_dict, 'max_items')
        self.assertEqual(result, 100)
    
    def test_search_dict_case_sensitive(self):
        """Test search_dict is case sensitive"""
        test_dict = {'Name': 'John', 'AGE': 30}
        result = search_dict(test_dict, 'name')  # lowercase
        self.assertIsNone(result)
        
        result = search_dict(test_dict, 'Name')  # uppercase
        self.assertEqual(result, 'John')


if __name__ == '__main__':
    unittest.main()
