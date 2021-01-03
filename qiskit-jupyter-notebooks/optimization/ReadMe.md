# Optimization Problems with Qiskit

## Types of Optimization Problems 

Following is a list of the type of optimization problems supported in Qiskit.

* Type A: Quadratic Unconstrained Binary Optimization (QUBO) - Binary Variables and No Constraints
* Type B: QUBO along with continuous variables

Examples of such types of problems are included in this repository.

## Metrics
1. Data related to the above types of problems are in the excel file <>.

## Method
1. A problem is solved in a notebook using CPLEX.
2. The problem in the **LP-Format** can be created as a file.
3. The file is read in the Quantum Solver notebook

    3a. A problem of type A is solved using QAOA, VQE or Grover's Optimization technique
    
    3b. A problem of type B is solved using ADMM technique.
    


<img src="images/optimization-landscape.jpg" />
In the entire optimisation landscaped displayed above, certain problems in the blue colored types can be solved using Qiskit so far. 

## Insights
* Until x variables (qubits) the results from IBMQ machines (sydney and manhattan) are erroneous