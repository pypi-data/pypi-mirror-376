from typing import Union, overload


@overload
def sequential_search(lst, item, start=0, stop=None, key=None) -> Union[int, None]: ...


@overload
def sequential_search(lst, item, start=0, stop=None, key=None, insertion=True) -> int: ...


@overload
def binary_search(lst, item, low=0, high=None, key=None) -> Union[int, None]: ...


@overload
def binary_search(lst, item, low=0, high=None, key=None, insertion=True) -> int: ...


def sequential_search(lst, item, start=0, stop=None, key=None, insertion=False):
    """顺序查找"""
    found = False
    if stop is None:
        stop = len(lst)
    for index in range(start, stop):
        value = lst[index]
        if key:
            value = key(value)
        if item <= value:
            if item == value:
                found = True
            break
    else:
        index = len(lst)
    return index if found or insertion else None


def binary_search(lst, item, low=0, high=None, key=None, insertion=False):
    """二分查找"""
    found = False
    mid = low
    if high is None:
        high = len(lst) - 1
    while low <= high:
        mid = (low + high) // 2
        value = lst[mid]
        if key:
            value = key(value)
        if item > value:
            low = mid = mid + 1
        elif item < value:
            high = mid - 1
        else:
            found = True
            break
    return mid if found or insertion else None
