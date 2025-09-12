# Mini Utility Library

A collection of Pythonic utility functions demonstrating best practices in functional programming, comprehensions, and recursion. This library provides clean, well-typed, and thoroughly tested utility functions for common programming tasks.

## 🚀 Features

- **Functional Programming**: Extensive use of `map`, `filter`, `reduce`, and lambda functions
- **List/Dict Comprehensions**: Pythonic data transformations
- **Recursion**: Natural recursive algorithms with memoization
- **Type Safety**: Comprehensive type hints using Python's `typing` module
- **Well Tested**: 47+ test cases with 100% coverage
- **Documentation**: Detailed docstrings with examples

## 📦 Installation

### From Source
```bash
git clone <repository-url>
cd "Mini Utility Library"
pip install -e .
```

### Development Installation
```bash
pip install -e .[dev]
```

## 🏗️ Project Structure

```
Mini Utility Library/
├── pyhelpers/
│   ├── __init__.py
│   ├── collections_utils.py    # List and dictionary utilities
│   ├── hof_utils.py           # Higher-order functions
│   └── recursion_utils.py     # Recursive algorithms
├── tests/
│   ├── test_collection.py     # Collection utilities tests
│   ├── test_hof.py           # HOF utilities tests
│   └── test_recursion.py     # Recursion utilities tests
├── pyproject.toml
└── README.md
```

## 📚 Modules

### Collections Utils (`collections_utils.py`)

Utility functions for working with lists and dictionaries using comprehensions.

#### Functions

- **`flatten_list(list_of_lists: List[Any]) -> List[Any]`**
  - Flatten nested lists using recursion
  - Preserves order and handles mixed data types

- **`unique_items_list(input_list: List[Any]) -> List[Any]`**
  - Remove duplicates while preserving order
  - Uses list comprehension with set for efficiency

- **`filter_dict(dictionary: Dict[str, Any], key: str) -> Optional[Any]`**
  - Get value by key with safe fallback
  - Returns `None` if key not found

#### Examples

```python
from pyhelpers.collections_utils import flatten_list, unique_items_list, filter_dict

# Flatten nested lists
nested = [[1, 2], [3, [4, 5]]]
flattened = flatten_list(nested)  # [1, 2, 3, 4, 5]

# Remove duplicates
duplicates = [1, 2, 2, 3, 1, 4]
unique = unique_items_list(duplicates)  # [1, 2, 3, 4]

# Safe dictionary access
data = {'name': 'John', 'age': 30}
age = filter_dict(data, 'age')  # 30
salary = filter_dict(data, 'salary')  # None
```

### Higher-Order Functions (`hof_utils.py`)

Functional programming utilities using `map`, `filter`, `reduce`, and lambda functions.

#### Functions

- **`map_function_to_list(input_list: List[T], function: Callable[[T], U]) -> List[U]`**
  - Apply function to each element using built-in `map`

- **`filter_list(input_list: List[T], predicate: Callable[[T], bool]) -> List[T]`**
  - Filter elements using predicate function

- **`reduce_list(input_list: List[T], function: Callable[[T, T], T], initial: Optional[T] = None) -> T`**
  - Reduce list to single value using `functools.reduce`

- **`compose_functions(functions: List[Callable[[Any], Any]]) -> Callable[[Any], Any]`**
  - Compose multiple functions using `reduce` and lambda

- **`safe_call(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Optional[Any]`**
  - Safely call function with error handling

- **`curry_function(function: Callable[..., Any], *args: Any) -> Callable[..., Any]`**
  - Curry function with partial arguments

#### Examples

```python
from pyhelpers.hof_utils import map_function_to_list, filter_list, compose_functions, safe_call

# Map function to list
numbers = [1, 2, 3, 4, 5]
squared = map_function_to_list(numbers, lambda x: x ** 2)  # [1, 4, 9, 16, 25]

# Filter list
evens = filter_list(numbers, lambda x: x % 2 == 0)  # [2, 4]

# Compose functions
add_one = lambda x: x + 1
double = lambda x: x * 2
composed = compose_functions([add_one, double])
result = composed(5)  # 12 = (5 + 1) * 2

# Safe function call
result = safe_call(lambda x, y: x / y, 10, 0)  # None (handles division by zero)
```

### Recursion Utils (`recursion_utils.py`)

Recursive algorithms with proper base cases and memoization.

#### Functions

- **`fibonacci(n: int) -> int`**
  - Calculate nth Fibonacci number (naive recursion)

- **`fibonacci_memoized(n: int, memo: Optional[Dict[int, int]] = None) -> int`**
  - Optimized Fibonacci with memoization

- **`factorial(n: int) -> int`**
  - Calculate factorial using recursion

- **`binary_search(arr: List[int], target: int, left: int = 0, right: Optional[int] = None) -> Optional[int]`**
  - Binary search using recursion

- **`search_dict(dictionary: Dict[str, Any], key: str) -> Optional[Any]`**
  - Recursively search nested dictionaries

- **`tree_traversal(tree: Dict[str, Any], traversal_type: str = "preorder") -> List[Any]`**
  - Traverse tree structures (preorder, inorder, postorder)

- **`flatten_nested_list(nested_list: List[Any]) -> List[Any]`**
  - Flatten nested lists using recursion

#### Examples

```python
from pyhelpers.recursion_utils import fibonacci, factorial, binary_search, search_dict

# Fibonacci sequence
fib_10 = fibonacci(10)  # 55
fib_50 = fibonacci_memoized(50)  # 12586269025 (optimized)

# Factorial
fact_5 = factorial(5)  # 120

# Binary search
sorted_list = [1, 3, 5, 7, 9, 11]
index = binary_search(sorted_list, 7)  # 3

# Search nested dictionary
nested_data = {
    'user': {
        'profile': {
            'name': 'Alice',
            'settings': {'theme': 'dark'}
        }
    }
}
theme = search_dict(nested_data, 'theme')  # 'dark'
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test modules
python tests/test_collection.py
python tests/test_hof.py
python tests/test_recursion.py

# Run with pytest (if installed)
python -m pytest tests/ -v
```

### Test Coverage

- **47 test cases** covering all functions
- **Edge cases** and error conditions
- **Type safety** validation
- **Performance** considerations

## 🎯 Design Principles

### Functional Programming
- **Immutable operations**: Functions don't modify input data
- **Pure functions**: No side effects, same input always produces same output
- **Higher-order functions**: Functions that take or return other functions
- **Composition**: Building complex operations from simple functions

### Python Best Practices
- **Type hints**: Comprehensive typing for better IDE support and documentation
- **List comprehensions**: More Pythonic than explicit loops
- **Docstrings**: Detailed documentation with examples
- **Error handling**: Graceful handling of edge cases

### Recursion Guidelines
- **Base cases**: Clear termination conditions
- **Memoization**: Performance optimization where appropriate
- **Tail recursion**: Structured for potential optimization
- **Infinite recursion prevention**: Proper bounds checking

## 📋 Requirements

- Python >= 3.8
- No external dependencies (uses only standard library)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

**Boopathy** - [kboopathyk7@email.com](mailto:kboopathyk7@email.com)

## 🔗 Related Projects

- [Python Functional Programming Guide](https://docs.python.org/3/howto/functional.html)
- [Python Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [Recursion in Python](https://realpython.com/python-thinking-recursively/)

---

*This library demonstrates modern Python development practices with a focus on functional programming, type safety, and clean code principles.*
