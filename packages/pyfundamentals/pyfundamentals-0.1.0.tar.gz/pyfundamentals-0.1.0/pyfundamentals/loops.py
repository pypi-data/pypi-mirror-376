# pyfundamentals/loops.py
def count_to_n(n: int) -> list[int]:
    """Return a list of numbers from 1 to n."""
    return [i for i in range(1, n+1)]
