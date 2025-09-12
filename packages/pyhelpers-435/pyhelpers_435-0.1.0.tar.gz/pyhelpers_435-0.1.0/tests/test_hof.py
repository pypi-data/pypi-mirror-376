import unittest
import sys
import os

# Add the parent directory to the path to import pyhelpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyhelpers.hof_utils import map_function_to_list, compose_functions, safe_call


class TestHofUtils(unittest.TestCase):
    """Test cases for higher-order function utilities"""
    
    def test_map_function_to_list_empty(self):
        """Test map_function_to_list with empty list"""
        def square(x):
            return x * x
        
        result = map_function_to_list([], square)
        self.assertEqual(result, [])
    
    def test_map_function_to_list_square(self):
        """Test map_function_to_list with square function"""
        def square(x):
            return x * x
        
        input_list = [1, 2, 3, 4, 5]
        result = map_function_to_list(input_list, square)
        self.assertEqual(result, [1, 4, 9, 16, 25])
    
    def test_map_function_to_list_string_length(self):
        """Test map_function_to_list with string length function"""
        def get_length(s):
            return len(s)
        
        input_list = ['hello', 'world', 'test']
        result = map_function_to_list(input_list, get_length)
        self.assertEqual(result, [5, 5, 4])
    
    def test_map_function_to_list_type_conversion(self):
        """Test map_function_to_list with type conversion"""
        def to_string(x):
            return str(x)
        
        input_list = [1, 2.5, True, None]
        result = map_function_to_list(input_list, to_string)
        self.assertEqual(result, ['1', '2.5', 'True', 'None'])
    
    def test_map_function_to_list_negative_numbers(self):
        """Test map_function_to_list with negative numbers"""
        def absolute(x):
            return abs(x)
        
        input_list = [-1, -2, -3, 4, -5]
        result = map_function_to_list(input_list, absolute)
        self.assertEqual(result, [1, 2, 3, 4, 5])
    
    def test_compose_functions_empty_list(self):
        """Test compose_functions with empty list"""
        composed = compose_functions([])
        # Should return identity function
        result = composed(5)
        self.assertEqual(result, 5)
    
    def test_compose_functions_single_function(self):
        """Test compose_functions with single function"""
        def add_one(x):
            return x + 1
        
        composed = compose_functions([add_one])
        result = composed(5)
        self.assertEqual(result, 6)
    
    def test_compose_functions_multiple_functions(self):
        """Test compose_functions with multiple functions"""
        def add_one(x):
            return x + 1
        
        def multiply_two(x):
            return x * 2
        
        def square(x):
            return x * x
        
        composed = compose_functions([add_one, multiply_two, square])
        # This will call: square(multiply_two(add_one(5)))
        # add_one(5) = 6, multiply_two(6) = 12, square(12) = 144
        result = composed(5)
        self.assertEqual(result, 144)
    
    def test_compose_functions_with_initial_value(self):
        """Test compose_functions with different initial values"""
        def identity(x):
            return x
        
        def double(x):
            return x * 2
        
        composed = compose_functions([identity, double])
        result = composed(10)
        self.assertEqual(result, 20)
    
    def test_safe_call_successful_execution(self):
        """Test safe_call with successful function execution"""
        def add(a, b):
            return a + b
        
        result = safe_call(add, 5, 3)
        self.assertEqual(result, 8)
    
    def test_safe_call_with_keyword_arguments(self):
        """Test safe_call with keyword arguments"""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"
        
        result = safe_call(greet, "Alice", greeting="Hi")
        self.assertEqual(result, "Hi, Alice!")
    
    def test_safe_call_with_exception(self):
        """Test safe_call with function that raises exception"""
        def divide(a, b):
            return a / b
        
        result = safe_call(divide, 10, 0)
        self.assertIsNone(result)
    
    def test_safe_call_with_type_error(self):
        """Test safe_call with TypeError"""
        def add_numbers(a, b):
            return a + b
        
        result = safe_call(add_numbers, "hello", 5)
        self.assertIsNone(result)
    
    def test_safe_call_with_value_error(self):
        """Test safe_call with ValueError"""
        def convert_to_int(s):
            return int(s)
        
        result = safe_call(convert_to_int, "not_a_number")
        self.assertIsNone(result)
    
    def test_safe_call_with_no_arguments(self):
        """Test safe_call with function that takes no arguments"""
        def get_constant():
            return 42
        
        result = safe_call(get_constant)
        self.assertEqual(result, 42)
    
    def test_safe_call_with_lambda(self):
        """Test safe_call with lambda function"""
        result = safe_call(lambda x, y: x * y, 4, 5)
        self.assertEqual(result, 20)
    
    def test_safe_call_with_exception_lambda(self):
        """Test safe_call with lambda that raises exception"""
        result = safe_call(lambda x: x[10], [1, 2, 3])
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
