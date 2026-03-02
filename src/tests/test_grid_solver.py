"""
Tests for Grid Swap Solver in Chronicle AI
"""

import pytest
from chronicle_ai.grid_solver import min_swaps_to_valid

def test_example_1():
    grid = [[0,0,1],[1,1,0],[1,0,0]]
    assert min_swaps_to_valid(grid) == 3

def test_example_2():
    grid = [[0,1,1,0],[0,1,1,0],[0,1,1,0],[0,1,1,0]]
    assert min_swaps_to_valid(grid) == -1

def test_example_3():
    grid = [[1,0,0],[1,1,0],[1,1,1]]
    assert min_swaps_to_valid(grid) == 0

def test_empty_grid():
    assert min_swaps_to_valid([]) == 0

def test_single_cell_grid():
    assert min_swaps_to_valid([[0]]) == 0
    assert min_swaps_to_valid([[1]]) == 0

def test_already_valid():
    # 4x4 valid grid
    grid = [
        [0, 0, 0, 0],
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [1, 1, 1, 1]
    ]
    # Row 0 needs 3 zeros (has 4)
    # Row 1 needs 2 zeros (has 3)
    # Row 2 needs 1 zero (has 2)
    # Row 3 needs 0 zeros (has 0)
    assert min_swaps_to_valid(grid) == 0

def test_impossible_swap():
    grid = [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1]
    ]
    assert min_swaps_to_valid(grid) == -1
