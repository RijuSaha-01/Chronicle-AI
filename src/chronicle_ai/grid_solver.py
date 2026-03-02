"""
Chronicle AI - Grid Swap Solver Algorithm
LeetCode Problem: Minimum Swaps to Make a Binary Grid Valid
"""

from typing import List

def min_swaps_to_valid(grid: List[List[int]]) -> int:
    """
    Calculate the minimum number of adjacent row swaps to make the binary grid valid.
    A grid is valid if all cells above the main diagonal are zeros.
    
    Args:
        grid: n x n binary grid
        
    Returns:
        Minimum number of steps or -1 if impossible.
    """
    n = len(grid)
    if n == 0:
        return 0
        
    # Pre-calculate trailing zeros for each row
    trailing_zeros = []
    for row in grid:
        zeros = 0
        for i in range(n - 1, -1, -1):
            if row[i] == 0:
                zeros += 1
            else:
                break
        trailing_zeros.append(zeros)

    total_swaps = 0
    # Process each row position i from top to bottom
    for i in range(n):
        # Row i needs at least (n - 1 - i) trailing zeros
        needed = n - 1 - i
        
        # Find the first row in the remaining grid that satisfies the requirement
        found_idx = -1
        for j in range(i, n):
            if trailing_zeros[j] >= needed:
                found_idx = j
                break
        
        if found_idx == -1:
            return -1
        
        # Swap the found row up to position i one step at a time
        while found_idx > i:
            trailing_zeros[found_idx], trailing_zeros[found_idx - 1] = (
                trailing_zeros[found_idx - 1],
                trailing_zeros[found_idx]
            )
            total_swaps += 1
            found_idx -= 1
            
    return total_swaps

if __name__ == "__main__":
    # Example 1
    example1 = [[0,0,1],[1,1,0],[1,0,0]]
    print(f"Example 1 Swaps: {min_swaps_to_valid(example1)}") # Expected: 3

    # Example 2
    example2 = [[0,1,1,0],[0,1,1,0],[0,1,1,0],[0,1,1,0]]
    print(f"Example 2 Swaps: {min_swaps_to_valid(example2)}") # Expected: -1

    # Example 3
    example3 = [[1,0,0],[1,1,0],[1,1,1]]
    print(f"Example 3 Swaps: {min_swaps_to_valid(example3)}") # Expected: 0
