# Autonomous Time Management Planner (ATMP)

Updated: January 25, 2020, by June Hu

## Abstract

Time management becomes increasingly difficult nowadays due to the overloading daily tasks and all kinds of pleasant desires. People have come up with all kinds of approaches to manage the time schedule, and the burden may be reduced with the help of machine decision-making process. Therefore, we introduce our system ATMP, "A Time Management Planner". With a few necessary inputs of the task information in a graphical interface, the planner would automatically come up with some suggested time schedules. The user can choose to follow them strictly or loosely, or run multiple times with the process of the tasks. The planner applies multiple optimization algorithms, on the basis of Markov Decision Process (MDP). The policy would keep updating until obtain a maximum gain and a minimum cost function are obtained within some range of errors. We tested the planner in a broad user-study, in various situations, and the results and feedbacks both show a positive potential application and development of our system.

**Keywords**: Decision-making; Scheduling; System Optimization


## Contributions

- Developed an algorithm for auto time planning, useful in daily life
- Applied an interactive interface for casual user to use (low learning curve)
- Developed an optimization algorithm without target goal, only to optimize the reward function
- Developed multiple reward functions with weighted ratio for balancing purpose -> an extension of current reward function in most planning algorithms 
- Developed mathematical expression and algorithm that split the entangled element in the problem (sleeping time&duration) -> show in diagram
- Developed visualizable models to simulate daily-life time-management behavior, can be used in other related researches


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

#### Define reward functions
##### Task types
- Fixed-time tasks
- Fixed-deadline tasks
- As-soon-as-possible tasks
- Fun tasks
- Long-term tasks
- Daily-necessity tasks
- Sleeping
- Meals

##### Fixed-time tasks

##### Fixed-deadline tasks

##### As-soon-as-possible tasks

##### Fun tasks

##### Long-term tasks

##### Daily-necessity tasks

##### Sleeping

##### Meals

##### Total rewards

#### Policies
##### Naïve policy

`traversal everything`

compute every possibility -> computation complexity ~ N[task]^N[time period]

##### Policy 1 (MDP?)

difference: no targeting state

Define state space S = {s}, each s is a task in todo-list, have various parameters depending on their types

Define action space A = {remain current state, change to new state}

Define reward function -> most complicated: so that to simulate the real-life situation better, have pre-defined function model with user-defined parameters:

...(detailed introduction on how to define reward function and why, also influence the parameters needed as input)

##### Policy 2


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



