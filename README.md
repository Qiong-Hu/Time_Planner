# Autonomous Time Management Planner (ATMP)

Updated: January 25, 2020, by June

**Keywords**: **TODO**

## Abstract

**TODO**



## Contributions

- developed an algorithm for auto time planning, useful in daily life
- applied an interactive interface for casual user to use (low learning curve)
- developed an optimization algorithm without target goal, only to optimize the reward function
- developed multiple reward functions with weighted ratio for balancing purpose -> an extension of current reward function in most planning algorithms 
- developed mathematical expression and algorithm that split the entangled element in the problem (sleeping time&duration) -> show in diagram
- developed visualizable models to simulate daily-life time-management behavior, can be used in other related researches


## Introduction (Big Picture)

*`What is the overall problem that is trying to solve?`* 
*`Why should people care about it?`* 
*`What is the general approach to solving this problem?`* 
*`How will this approach result in a solution?`* 
*`What is the value of this approach beyond this specific solution?`*

*`Create and include one or two graphics that capture and communicate the problem and proposed solution to technical but non-expert audiences. Can you create a one or two sentence summary of the problem and the proposed solution approach?`*

**TODO**



## Related Works
*`What foundation and fundamentals need to be known in order to understand your problem, approach, and solution?`*
*`What work has been done before on this specific problem?`*
*`What are related problems that have been addressed?`*
*`What work has been done on those related problems?`*
*`How does this past work contribute to your proposed solution?`*

*`Be sure to cite all potential sources, and summarize each one in terms of its content and relation to your project.`*

**TODO**



## Specific Project Scope
### Methods
#### Naive method

`traversal everything`

compute every possibility -> computation complexity ~ N[task]^N[time period]

#### Method 1 (MDP?)

difference: no targeting state

Define state space S = {s}, each s is a task in todo-list, have various parameters depending on their types

Define action space A = {remain current state, change to new state}

Define reward function -> most complicated: so that to simulate the real-life situation better, have pre-defined function model with user-defined parameters:

...(detailed introduction on how to define reward function and why, also influence the parameters needed as input)

#### Method 2


### Demo
`demo example`


### Results
`compare with other methods, such as naive methods`


### User-study
#### User-study design
*`use self-guide example and documentation, allow free input, count time / observe how they behave, record quantitative and descriptive feedbacks (pre and post survey/interview)`*

#### User Composition

#### User feedbacks


### Extended application
*`What is the value of your solution beyond solely solving this subproblem?`*


## Future works
*`limitations -> expressed as future works`*


## References
1. **TODO**



