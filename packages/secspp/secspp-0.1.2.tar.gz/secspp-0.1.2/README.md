SECS++ Cube Solver
SECS++ is an intelligent, hybrid Rubik's Cube solver that combines a custom heuristic-driven A* search with a guaranteed optimal solver.

This package provides a robust and easy-to-use tool to find solutions for any valid 3x3 Rubik's Cube scramble. It first attempts to solve the cube using the innovative SECS++ algorithm. If the scramble proves too complex for the heuristic search, it seamlessly falls back to the powerful Kociemba algorithm to guarantee a correct and optimal solution.

Key Features
Hybrid Solving Strategy: Prioritizes the custom A* search and uses Kociemba's algorithm as a robust failover, offering the best of both worlds.

Unique cubeeval Heuristic: Employs a novel heuristic that evaluates cube states based on both sticker misalignment and color entropy.

Simple API: A single function call to solve any scramble.

Phase-Based Logic: Breaks the problem down into logical stages (Cross, F2L, Last Layer) for its primary search.

Guaranteed Solutions: Never fails to solve a valid scramble.

Installation
You can install the SECS++ Cube Solver directly from PyPI:

pip install secs-cube-solver

This package requires the kociemba-python library, which will be installed automatically as a dependency.

Quick Start & Usage
Using the solver is straightforward. Import the main solve function from the package, provide a scramble string, and get the solution.

Here is a complete usage example:

# Import the main solver function
from secs import solve

# Define a scramble string (standard cube notation)
scramble = "R U R' U R U2 R' U"

print(f"Solving scramble: {scramble}")

# Call the solver
# The function returns the solution moves and the solver that found it
solution_moves, solver_type = solve(scramble)

# Print the result
print(f"\nSolution found by: {solver_type}")
print(f"Solved in {len(solution_moves)} moves:")
print(' '.join(solution_moves))

Example Output:

Solving scramble: R U R' U R U2 R' U

Solution found by: SECS++ (A* with cubeeval heuristic)
Solved in 8 moves:
U' R U2 R' U' R U' R'

The SECS++ Algorithm
The primary solver uses a phased A* search algorithm. The intelligence of this search is guided by a custom heuristic function, cubeeval(n), which evaluates the "cost" of any given cube state n.

The A* formula is:
f(n)=g(n)+
textcubeeval(n)

Where:

g(n) is the number of moves already taken.

cubeeval(n) is our unique heuristic: a
cdotH_diff(n)+b
cdotE(n)

H_diff(n) measures sticker misalignment.

E(n) is a novel metric for color entropy (disorder) on each face.

If the A* search cannot find a solution within its configured limits, the package automatically calls Kociemba's algorithm to ensure a correct and optimal solution is always returned.

Author
P. Jeba Selvan Andrew

GitHub Profile

License
This project is licensed under the MIT License. See the LICENSE file for details.