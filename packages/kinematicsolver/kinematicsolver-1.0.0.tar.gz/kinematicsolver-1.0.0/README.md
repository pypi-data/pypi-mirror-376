# KinematicSolver
An algebra-based kinematic variables solver for UAM
To successfully calculate the variables, you must provide the method with a list of 5 elements (3 "givens" in float format), and the unsolved variables should be "None". Each element in the list should align with the SUVAT acronym. Meaning, for example, displacement (S) should be in the index 0, because it is the first letter of SUVAT.
Example: [None, 0, 20, 2, None]
Precondition: Time must be a non-zero number