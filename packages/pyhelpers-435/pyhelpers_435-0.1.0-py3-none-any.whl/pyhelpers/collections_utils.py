from typing import List, Dict, Any, Union, Optional


def flatten_list(list_of_lists: List[Any], result: Optional[List[Any]] = None) -> List[Any]:
    """
    Flatten a list of lists into a single list using recursion.
    
    Args:
        list_of_lists: A list that may contain nested lists
        result: Optional accumulator list (used internally for recursion)
    
    Returns:
        A flattened list containing all elements from nested lists
        
    Examples:
        >>> flatten_list([[1, 2], [3, [4, 5]]])
        [1, 2, 3, 4, 5]
        >>> flatten_list([1, 2, 3])
        [1, 2, 3]
    """
    if result is None:
        result = []
    
    for item in list_of_lists:
        if isinstance(item, list):
            result = flatten_list(item, result)
        else:
            result.append(item)
    return result


def unique_items_list(input_list: List[Any]) -> List[Any]:
    """
    Remove duplicate items from a list while preserving order using list comprehension.
    
    Args:
        input_list: A list that may contain duplicate elements
    
    Returns:
        A new list with duplicates removed, preserving the order of first occurrence
        
    Examples:
        >>> unique_items_list([1, 2, 2, 3, 1, 4])
        [1, 2, 3, 4]
        >>> unique_items_list(['a', 'b', 'a', 'c'])
        ['a', 'b', 'c']
    """
    seen = set()
    return [item for item in input_list if not (item in seen or seen.add(item))]


def filter_dict(dictionary: Dict[str, Any], key: str) -> Optional[Any]:
    """
    Filter a dictionary by a key using dictionary comprehension.
    
    Args:
        dictionary: The dictionary to search in
        key: The key to search for
    
    Returns:
        The value associated with the key, or None if key not found
        
    Examples:
        >>> filter_dict({'name': 'John', 'age': 30}, 'age')
        30
        >>> filter_dict({'name': 'John', 'age': 30}, 'salary')
        None
    """
    return dictionary.get(key)