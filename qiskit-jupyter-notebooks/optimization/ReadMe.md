# Optimization Problems with Qiskit

## Types of Optimization Problems 

Following is a list of the type of optimization problems supported in Qiskit.

* Type A: Quadratic Unconstrained Binary Optimization (QUBO) - Binary Variables and No Constraints
* Type B: QUBO along with continuous variables

Examples of such types of problems are included in this repository.

## Metrics
1. Data related to the above types of problems are in the excel file <i>stats.csv</i>.

## Method
1. A problem is solved in a notebook using CPLEX.
2. The problem in the **LP-Format** can be created as a file.
3. The file is read in the Quantum Solver notebook

    3a. A problem of type A is solved using QAOA, VQE or Grover's Optimization technique
	An MIP is converted to QUBO as well.
    
    3b. A problem of type B is solved using ADMM technique.
    


<img src="images/optimization-landscape.jpg" />
In the entire optimisation landscaped displayed above, certain problems in the blue colored types can be solved using Qiskit so far. 


## Limits for the problem (with ibmq-manhattan, 65 qubits, QV32)

1. MILP with binary and continuous variables -  9 variables
2. MIQP with binary variables -                 3 variables
3. QUBO -                                      12 variables (sydney)
4. Assignment Problem with binary variables -   9 variables
5. Bin Packing Problem with binary variables
6. Objects in boxes with binary variables -     9 variables
