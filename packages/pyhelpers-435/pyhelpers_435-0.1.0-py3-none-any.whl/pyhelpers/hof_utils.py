from typing import List, Callable, Any, Optional, TypeVar, Union
from functools import reduce

T = TypeVar('T')
U = TypeVar('U')


def map_function_to_list(input_list: List[T], function: Callable[[T], U]) -> List[U]:
    """
    Map a function to a list using built-in map function.
    
    Args:
        input_list: List of items to transform
        function: Function to apply to each item
    
    Returns:
        New list with function applied to each element
        
    Examples:
        >>> map_function_to_list([1, 2, 3], lambda x: x * 2)
        [2, 4, 6]
        >>> map_function_to_list(['hello', 'world'], len)
        [5, 5]
    """
    return list(map(function, input_list))


def filter_list(input_list: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    Filter a list using a predicate function.
    
    Args:
        input_list: List of items to filter
        predicate: Function that returns True for items to keep
    
    Returns:
        New list containing only items where predicate returns True
        
    Examples:
        >>> filter_list([1, 2, 3, 4, 5], lambda x: x % 2 == 0)
        [2, 4]
        >>> filter_list(['hello', '', 'world', ''], lambda x: len(x) > 0)
        ['hello', 'world']
    """
    return list(filter(predicate, input_list))


def reduce_list(input_list: List[T], function: Callable[[T, T], T], initial: Optional[T] = None) -> T:
    """
    Reduce a list to a single value using a function.
    
    Args:
        input_list: List of items to reduce
        function: Binary function to apply cumulatively
        initial: Optional initial value
    
    Returns:
        Single reduced value
        
    Examples:
        >>> reduce_list([1, 2, 3, 4], lambda x, y: x + y)
        10
        >>> reduce_list([1, 2, 3, 4], lambda x, y: x * y)
        24
    """
    if initial is not None:
        return reduce(function, input_list, initial)
    return reduce(function, input_list)


def compose_functions(functions: List[Callable[[Any], Any]]) -> Callable[[Any], Any]:
    """
    Compose a list of functions using reduce and lambda.
    
    Args:
        functions: List of functions to compose
    
    Returns:
        Composed function that applies all functions in sequence
        
    Examples:
        >>> add_one = lambda x: x + 1
        >>> double = lambda x: x * 2
        >>> composed = compose_functions([add_one, double])
        >>> composed(5)
        12  # (5 + 1) * 2
    """
    if not functions:
        return lambda x: x
    
    return lambda x: reduce(lambda acc, func: func(acc), functions, x)


def safe_call(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Optional[Any]:
    """
    Safely call a function with error handling.
    
    Args:
        function: Function to call
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Function result or None if an exception occurs
        
    Examples:
        >>> safe_call(lambda x, y: x + y, 5, 3)
        8
        >>> safe_call(lambda x: x / 0, 5)
        None
    """
    try:
        return function(*args, **kwargs)
    except Exception:
        return None


def curry_function(function: Callable[..., Any], *args: Any) -> Callable[..., Any]:
    """
    Curry a function with partial arguments.
    
    Args:
        function: Function to curry
        *args: Arguments to partially apply
    
    Returns:
        Curried function that takes remaining arguments
        
    Examples:
        >>> add = lambda x, y: x + y
        >>> add_five = curry_function(add, 5)
        >>> add_five(3)
        8
    """
    return lambda *remaining_args: function(*args, *remaining_args)
