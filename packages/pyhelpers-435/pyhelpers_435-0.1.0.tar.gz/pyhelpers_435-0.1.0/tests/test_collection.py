import unittest
import sys
import os

# Add the parent directory to the path to import pyhelpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyhelpers.collections_utils import flatten_list, unique_items_list, filter_dict


class TestCollectionsUtils(unittest.TestCase):
    """Test cases for collections utility functions"""
    
    def test_flatten_list_empty(self):
        """Test flatten_list with empty list"""
        result = flatten_list([])
        self.assertEqual(result, [])
    
    def test_flatten_list_simple(self):
        """Test flatten_list with simple nested list"""
        input_list = [[1, 2], [3, 4]]
        result = flatten_list(input_list)
        self.assertEqual(result, [1, 2, 3, 4])
    
    def test_flatten_list_deeply_nested(self):
        """Test flatten_list with deeply nested lists"""
        input_list = [[1, [2, 3]], [4, [5, [6, 7]]]]
        result = flatten_list(input_list)
        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7])
    
    def test_flatten_list_mixed_types(self):
        """Test flatten_list with mixed data types"""
        input_list = [['a', 'b'], [1, 2], ['c', [3, 4]]]
        result = flatten_list(input_list)
        self.assertEqual(result, ['a', 'b', 1, 2, 'c', 3, 4])
    
    def test_flatten_list_single_level(self):
        """Test flatten_list with single level list"""
        input_list = [1, 2, 3, 4]
        result = flatten_list(input_list)
        self.assertEqual(result, [1, 2, 3, 4])
    
    def test_unique_items_list_empty(self):
        """Test unique_items_list with empty list"""
        result = unique_items_list([])
        self.assertEqual(result, [])
    
    def test_unique_items_list_no_duplicates(self):
        """Test unique_items_list with no duplicates"""
        input_list = [1, 2, 3, 4]
        result = unique_items_list(input_list)
        self.assertEqual(result, [1, 2, 3, 4])
    
    def test_unique_items_list_with_duplicates(self):
        """Test unique_items_list with duplicates"""
        input_list = [1, 2, 2, 3, 1, 4, 2]
        result = unique_items_list(input_list)
        self.assertEqual(result, [1, 2, 3, 4])
    
    def test_unique_items_list_preserves_order(self):
        """Test unique_items_list preserves order of first occurrence"""
        input_list = [3, 1, 2, 1, 3, 4, 2]
        result = unique_items_list(input_list)
        self.assertEqual(result, [3, 1, 2, 4])
    
    def test_unique_items_list_mixed_types(self):
        """Test unique_items_list with mixed data types"""
        input_list = ['a', 1, 'b', 1, 'a', 2, 'c']
        result = unique_items_list(input_list)
        self.assertEqual(result, ['a', 1, 'b', 2, 'c'])
    
    def test_filter_dict_key_exists(self):
        """Test filter_dict when key exists"""
        test_dict = {'name': 'John', 'age': 30, 'city': 'New York'}
        result = filter_dict(test_dict, 'age')
        self.assertEqual(result, 30)
    
    def test_filter_dict_key_not_exists(self):
        """Test filter_dict when key doesn't exist"""
        test_dict = {'name': 'John', 'age': 30, 'city': 'New York'}
        result = filter_dict(test_dict, 'salary')
        self.assertIsNone(result)
    
    def test_filter_dict_empty_dict(self):
        """Test filter_dict with empty dictionary"""
        result = filter_dict({}, 'any_key')
        self.assertIsNone(result)
    
    def test_filter_dict_string_values(self):
        """Test filter_dict with string values"""
        test_dict = {'first': 'Alice', 'last': 'Smith', 'middle': 'Jane'}
        result = filter_dict(test_dict, 'last')
        self.assertEqual(result, 'Smith')
    
    def test_filter_dict_numeric_values(self):
        """Test filter_dict with numeric values"""
        test_dict = {'x': 10, 'y': 20, 'z': 30}
        result = filter_dict(test_dict, 'y')
        self.assertEqual(result, 20)


if __name__ == '__main__':
    unittest.main()
