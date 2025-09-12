from typing import Dict, Any, List, Optional, Union


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number using recursion.
    
    Args:
        n: The position in the Fibonacci sequence (0-indexed)
    
    Returns:
        The nth Fibonacci number
        
    Examples:
        >>> fibonacci(0)
        0
        >>> fibonacci(1)
        1
        >>> fibonacci(10)
        55
        
    Note:
        This implementation uses naive recursion and is not optimized for large n.
        For better performance with large numbers, consider using memoization.
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fibonacci_memoized(n: int, memo: Optional[Dict[int, int]] = None) -> int:
    """
    Calculate the nth Fibonacci number using memoized recursion for better performance.
    
    Args:
        n: The position in the Fibonacci sequence (0-indexed)
        memo: Optional memoization dictionary (used internally)
    
    Returns:
        The nth Fibonacci number
        
    Examples:
        >>> fibonacci_memoized(50)
        12586269025
        >>> fibonacci_memoized(100)
        354224848179261915075
    """
    if memo is None:
        memo = {}
    
    if n in memo:
        return memo[n]
    
    if n <= 1:
        return n
    
    memo[n] = fibonacci_memoized(n - 1, memo) + fibonacci_memoized(n - 2, memo)
    return memo[n]


def search_dict(dictionary: Dict[str, Any], key: str) -> Optional[Any]:
    """
    Recursively search a dictionary for a key in nested dictionaries.
    
    Args:
        dictionary: The dictionary to search in
        key: The key to search for
    
    Returns:
        The value associated with the key, or None if not found
        
    Examples:
        >>> search_dict({'name': 'John', 'age': 30}, 'age')
        30
        >>> search_dict({'user': {'profile': {'name': 'Alice'}}}, 'name')
        'Alice'
    """
    for item in dictionary:
        if item == key:
            return dictionary[item]
        elif isinstance(dictionary[item], dict):
            result = search_dict(dictionary[item], key)
            if result is not None:
                return result
    return None


def factorial(n: int) -> int:
    """
    Calculate factorial using recursion.
    
    Args:
        n: Non-negative integer
    
    Returns:
        Factorial of n
        
    Examples:
        >>> factorial(0)
        1
        >>> factorial(5)
        120
        >>> factorial(10)
        3628800
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def binary_search(arr: List[int], target: int, left: int = 0, right: Optional[int] = None) -> Optional[int]:
    """
    Binary search using recursion.
    
    Args:
        arr: Sorted list of integers
        target: Value to search for
        left: Left boundary (used internally)
        right: Right boundary (used internally)
    
    Returns:
        Index of target if found, None otherwise
        
    Examples:
        >>> binary_search([1, 3, 5, 7, 9], 5)
        2
        >>> binary_search([1, 3, 5, 7, 9], 4)
        None
    """
    if right is None:
        right = len(arr) - 1
    
    if left > right:
        return None
    
    mid = (left + right) // 2
    
    if arr[mid] == target:
        return mid
    elif arr[mid] > target:
        return binary_search(arr, target, left, mid - 1)
    else:
        return binary_search(arr, target, mid + 1, right)


def tree_traversal(tree: Dict[str, Any], traversal_type: str = "preorder") -> List[Any]:
    """
    Traverse a tree structure recursively.
    
    Args:
        tree: Tree represented as nested dictionary
        traversal_type: Type of traversal ("preorder", "inorder", "postorder")
    
    Returns:
        List of values in traversal order
        
    Examples:
        >>> tree = {'value': 1, 'left': {'value': 2}, 'right': {'value': 3}}
        >>> tree_traversal(tree, "preorder")
        [1, 2, 3]
    """
    if not tree:
        return []
    
    result = []
    
    if traversal_type == "preorder":
        result.append(tree.get('value'))
        if 'left' in tree:
            result.extend(tree_traversal(tree['left'], traversal_type))
        if 'right' in tree:
            result.extend(tree_traversal(tree['right'], traversal_type))
    
    elif traversal_type == "inorder":
        if 'left' in tree:
            result.extend(tree_traversal(tree['left'], traversal_type))
        result.append(tree.get('value'))
        if 'right' in tree:
            result.extend(tree_traversal(tree['right'], traversal_type))
    
    elif traversal_type == "postorder":
        if 'left' in tree:
            result.extend(tree_traversal(tree['left'], traversal_type))
        if 'right' in tree:
            result.extend(tree_traversal(tree['right'], traversal_type))
        result.append(tree.get('value'))
    
    return result


def flatten_nested_list(nested_list: List[Any]) -> List[Any]:
    """
    Flatten a nested list using recursion.
    
    Args:
        nested_list: List that may contain nested lists
    
    Returns:
        Flattened list
        
    Examples:
        >>> flatten_nested_list([1, [2, 3], [4, [5, 6]]])
        [1, 2, 3, 4, 5, 6]
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_nested_list(item))
        else:
            result.append(item)
    return result