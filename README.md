# Automatic Time Planner for Daily Task Management

Updated: February 10, 2020

This task scheduler (a.k.a. time planner) aims to automatically, scientifically schedule various activities for students. 

With an input todo-list (an example is shown [here](todolist.yaml)), the system calculates the reward function based on real-life experience, for example, fixed-time tasks like lectures and fixed-deadline tasks like assignments generally have higher value in productivity, and fun activities have higher value in enjoyment. The scheduler takes both "$productivity$" and "$enjoyment$" into consideration, with a parameter called "$strictness$" to balance the two. The final reward value of a task would be the linear combination of productivity and enjoyment: 
$$
reward=strictness*productivity+(1-strictness)*enjoyment,
$$
and the total reward value of a schedule is the sum of all the activities in the schedule:
$$
reward_{schedule}=\sum{reward_{task}}.
$$
The system applies iterative loops to search for an optimization solution to maximize the total reward value, in order to find the optimal schedule.


## Define reward functions
### Activity types
Activity of different types have different time-dependent curves multiply user-defined $reward$ value to calculate their real rewards. The type list in the system is as follows:
- Sleeping
- Meals
- Fixed-time tasks
- Fixed-deadline tasks
- As-soon-as-possible tasks
- Fun tasks
- Long-term tasks
- Daily-necessity tasks

And we will briefly introduce how the time-dependent reward curve for each type of activity is defined in the following sections.

#### Sleeping
- Parameters for a sleeping activity: "$bedtime$" and "$duration$" hours
- $bedtime$: typically range from 22:00 to 4:00
- $duration$: typically range from 5 to 12 hours
- $reward$ increases with earlier $bedtime$ and longer $duration$:
$$
rwd_{bed} = exp\{-(bed_{real}-bed_{min})\},
$$
$$
rwd_{dur} = 1-exp\{-0.8 * (dur_{real}-dur_{min})\} (\text{for } dur_{min} \leqslant dur_{real} \leqslant dur_{max}),
$$
$$
rwd = rwd_{bed} * rwd_{dur}.
$$

The diagrams of 

![3D function curve](img/3D-bedtime_duration.jpg)

and 

![2D function curve](img/func-bedtime_duration.jpg)

show the dependent relationships. It makes sense that if I sleep really late (e.g. 4am), even if sleeping for a long period of time cannot undo the harm from the stay up to the body.

Therefore, for me, the parameters are: $dur_{min} = 5, dur_{max} = 12, bed_{min} = 22, bed_{max} = 4$, and here is a diagram of reward to each pair of \{$duration$, $bedtime$\} in a discrete time step.

![discrete rwd func for sleeping](img/sleeping.jpg)

#### Meals
- Parameters: $time$
- suggested time period for three meals: [7, 10], [11, 14], [17, 20]
- It's better to eat within the suggested time period, so time-dependent reward curve: 

![rwd func for meals](img/meal.jpg)

#### Fixed-time tasks
- Parameters: $start$, $duration$
- Example: lecture, mandatory activities
- reward doesn't change as long as arrange the activity in the schedule at its arranged time, so the reward curve is a constant over time, and the value is dependent on the $strictness$ according to Equation (1):

![rwd func for fixed-time tasks](img/fixed-time.jpg)

#### Fixed-deadline tasks

![rwd func for fixed-ddl tasks](img/fixed-ddl.jpg)

#### As-soon-as-possible tasks

![rwd func for asap tasks](img/asap.jpg)

#### Fun tasks

![rwd func for fun tasks](img/fun.jpg)

#### Long-term tasks

![rwd func for long-term tasks](img/long-term.jpg)

#### Daily-necessity tasks

![rwd func for necessity tasks](img/necessity.jpg)

## Decision-making algorithms

### Random generation

![demo1](img/demo1-pure-random.png)

### Limit numbers of trivial tasks

![demo2](img/demo2-disposable.png)

### Recurrence to find better schedule

![demo3](img/demo3-recurrence.png)

### Recurrence and limit numbers of trivial tasks

![demo4](img/demo4-recurrence-disposable.png)

### Traverse over all possible sleeping time choices

![demo5](img/demo5-traversal.png)

strictness = 0.5

rwd_max = 78.55809001494876

## Traversal result with different strictness

### strictness = 0

![demo5-strict=0](img/demo5-strict=0.png)

rwd_max = 97.56982887318202

### strictness = 1

![demo5-strict=1](img/demo5-strict=1.png)

rwd_max = 70.54294748768503
