#coding: UTF-8
'''
=================== License Information ===================
Author:     June Hu
Email:      junesirius@ucla.edu
Version:    Ver 2.0.0
Date:       January 30, 2020
'''

import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.optimize import curve_fit
import time
import random
import yaml
import os

T = 1               # Discrete time sampling window length
                    # For now, sampling length: 1 hour (min time on each task is 1h)
                    # Suggested sampling time duration: 0.5 hour (30 mins) => similar to tomato time, time of human concentration
                    # T <= 1 and 60*T must be integer (for now), so a good choice list for T: [1, 0.5, 1/3, 0.25, 0.2, 1/6, 0.1, 1/12]
                    # corresponding min: [60, 30, 20, 15, 12, 10, 6, 5]
procrastination = 1.5    # Approxinate procrastination time percentage based on approx_time

# Read input parameters from YAML file, default filename: 'todo.yaml'
def inputYAML(filename = "todolist.yaml"):
    # Return a dictionary of potential tasks with input parameters
    if os.path.isfile(filename):
        file = open(filename)
        tasks = yaml.load(file)
        file.close()
        return tasks
    else:
        raise Exception("Can't find the file '" + filename + "'")

# Combined rewards of enjoyment and productivity after weighted ratio "strictness"
def rwd_after_strict(strictness, enjoyment, productivity):
    # strictness ∈ [0, 1]
    return strictness * productivity + (1 - strictness) * enjoyment

# Reward function of fixed-time tasks
def rwd_fixed_time(x, task, strictness):
    # x: exact hour of a day, ∈ [0, 24]
    # task.keys(): type, day, start, duration, enjoyment, productivity
    if task["type"] == "fixed_time":
        start = task["start"]
        duration = task["duration"]
        reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])

        if start <= x <= start + duration:
            y = reward
        else:
            y = 0
        return y
    else:
        raise Exception("Wrong reward function for non-fixed-time task")

# Mathematical expression of reward function of fixed-ddl tasks
def func_fixed_ddl(x, a, k, c):
    # a: max reward, a > 0
    # k: decreasing speed, ≈ half-life (?), k > 0
    # c: start point
    y = a + 1 - np.exp(k * (x - c))
    return y

# Find function in the expression form of func_fixed_ddl, by two points
def findfunc_fixed_ddl(x, p1, p2):
    # p1, p2 are start and end point on partial rwd-time function plot
    # p1 = (x1, y1), p2 = (x2, y2)
    # Must satisfy: x1 < x2
    a = p1[1]
    k = np.log(p1[1] + 1 - p2[1]) / (p2[0] - p1[0])
    c = p1[0]
    return func_fixed_ddl(x, a, k, c)

# Reward function of fixed-ddl tasks
def rwd_fixed_ddl(x, task, strictness):
    # x: time duration since now
    # task.keys(): type, approx_time, deadline, enjoyment, productivity
    if task["type"] == "fixed_ddl":
        approx_time = task["approx_time"]
        deadline = task["deadline"]
        reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])

        xdata = [0, deadline]
        ydata = [reward, reward / 5]
        if 0 <= x <= deadline:
            y = findfunc_fixed_ddl(x, (xdata[0], ydata[0]), (xdata[1], ydata[1]))
        else:
            y = 0
        return y
    else:
        raise Exception("Wrong reward function for non-fixed-ddl task")

# Mathematical expression of reward function of as-soon-as-possible tasks
def func_asap(x, a, k, c):
    y = a * np.exp(-k * (x - c))
    return y

# Find function in the expression form of func_asap, by two points
def findfunc_asap(x, p1, p2):
    # p1, p2 are start and end points on rwd-time function plot
    # p1 = (x1, y1), p2 = (x2, y2)
    # Must satisfy: x1 < x2
    a = p1[1]
    k = np.log(p1[1] / p2[1]) / (p2[0] - p1[0])
    c = p1[0]
    return func_asap(x, a, k, c)

# Reward function of asap tasks
def rwd_asap(x, task, strictness):
    # x: time duration since now
    # task.keys(): type, approx_time, enjoyment, productivity
    if task["type"] == "as_soon_as_possible":
        approx_time = task["approx_time"]
        reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])

        xdata = [0, approx_time * procrastination]
        ydata = [reward, reward / 2]
        if x >= xdata[0]:
            y = findfunc_asap(x, (xdata[0], ydata[0]), (xdata[1], ydata[1]))
        else:
            y = 0
        return y
    else:
        raise Exception("Wrong reward function for non-asap task")

# Reward function of fun tasks
def rwd_fun(x, task, strictness):
    # x: whichever def (duration or exact current hour)
    # task.keys(): type, enjoyment, productivity
    if task["type"] == "fun":
        reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])

        if x >= 0:
            y = reward
        else:
            y = 0
        return y
    else:
        raise Exception("Wrong reward function for non-fun task")

# Mathematical expression of long-term tasks, dependent on the duration
def func_long_term_duration(x, duration_max):
    if 0 <= x <= duration_max:
        y = 1 - np.exp(-x * 5 / duration_max)
    else:
        y = 0
    return y

# Mathematical expression of long-term tasks, dependent on insisted days
def func_long_term_insist_days(insist_day, lamda):
    # insist_day: number of days that has been insisting on working on the long-term task; must be >0
    # lamda: dacay coefficient to reduce (a little bit) past influence, compared to the present commitment; ∈ [0, 1]
    if insist_day >= 0 and 0 <= lamda <= 1:
        y = np.sqrt(insist_day * lamda + 1)
        return y
    else:
        raise Exception("Wrong inputs for long-term task")

# Reward function of long-term-beneficial tasks
def rwd_long_term(x, task, strictness, lamda = 0.7):
    # x: time duration of the task, accumulated after each day
    # lamba: decay coefficient for past insisted days
    # task.keys(): type, insist_day, duration_max, enjoyment, productivity
    if task["type"] == "long_term":
        insist_day = task["insist_day"]
        duration_max = task["duration_max"]
        reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])

        if x >= 0:
            y = reward * func_long_term_insist_days(insist_day, lamda) * func_long_term_duration(x, duration_max)
        else:
            y = 0
        return y
    else:
        raise Exception("Wrong reward function for non-long-term task")

# Find params for the logistic signoid function for necessity task
def findfunc_necessity(r, l, epsilon = 0.01):
    # r: the right-boundary of x value when y = 0.99 is max (when epsilon = 0.01)
    # l: the left-boundary of x value when y = 0.01 is min (when epsilon = 0.01)
    # epsilon: the threshold to measure if y is close enough to 0 and 1

    # Find the alpha and gamma for function logisticSigmoid((x-alpha)/gamma)
    # <=> Solve the functions {logisticSigmoid((r-alpha)/gamma)=0.99, logisticSigmoid((l-alpha)/gamma)}
    # <=> {(r-alpha)/gamma=ln(99)=C, (l-alpha)/gamma=-ln(99)=-C}
    # => y(r) = y(l) = 0.5
    C = np.log(1 - epsilon) - np.log(epsilon)
    alpha = (r + l) / 2
    gamma = (r - l) / (2*C)
    return alpha, gamma

# Mathematical expression for necessity task
def func_necessity(x, time, relaxation = 1):
    # x: exact time of the day [0, 24)
    # time: type: list; may have param number of 0, 1, 2
    if len(time) == 0:      # No time limit, rwd = constant, regardless of x
        y = 1
    elif len(time) == 1:    # Have an optimal time point, relaxation time = 2h
        alpha1, gamma1 = findfunc_necessity(time[0], time[0] - relaxation)
        alpha2, gamma2 = findfunc_necessity(time[0], time[0] + relaxation)
        y = logisticSigmoid((x - alpha1) / gamma1) + logisticSigmoid((x - alpha2) / gamma2) - 1
        # Normalization (make sure when x = time[0], y = 1)
        y_max = logisticSigmoid((time[0] - alpha1) / gamma1) + logisticSigmoid((time[0] - alpha2) / gamma2) - 1
        y = y / y_max
    elif len(time) == 2:    # Have an optimal time period, relaxation time = 2h
        alpha1, gamma1 = findfunc_necessity(time[0], time[0] - relaxation)
        alpha2, gamma2 = findfunc_necessity(time[1], time[1] + relaxation)
        y = logisticSigmoid((x - alpha1) / gamma1) + logisticSigmoid((x - alpha2) / gamma2) - 1
        # Normally don't need normalization because exponential function almost always naturally makes sure during [time], y = 1
    else:
        raise Exception("Wrong input of 'time' for necessity task")
    return y

# Reward function of daily-necessary tasks
def rwd_necessity(x, task, strictness):
    # x: exact time of the day
    # task.keys(): type, time, duration, enjoyment, productivity
    if task["type"] == "necessity":
        time = task["time"]
        reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])

        if 0 <= x < 24:
            y = reward * func_necessity(x, time)
        else:
            raise Exception("Wrong input time for necessity task")
        return y
    else:
        raise Exception("Wrong reward function for non-necessity task")

# Logistic Sigmoid Curve, for func_meal
def logisticSigmoid(x):
    return 1 / (1 + np.exp(-x))

# Mathematical expression for reward fucntion of meals
def func_meal(x, l, r):
    # l, r: short for "left" and "right", lower and upper bounds for the curve
    # 3 parts of y represents: lower bound to middle, middle to upper bound, for normalization (so y=0 when x is far away)
    # Normalized (y_max = 1 for any x)
    y = pow(logisticSigmoid((x - l + 1) * 3), 3) + pow(logisticSigmoid((r - x) * 3), 3) - 1
    if y < 0:
        y = 0
    return y

# Reward function of meals
def rwd_meal(x, task, strictness):
    # x: exact current time
    # time: list type, = [start_time, end_time], end_time - start_time = 3 hours
    # task.keys(): type, time, duration, enjoyment, productivity
    if task["type"] == "meal":
        time = task["time"]
        reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])
        y = reward * func_meal(x, time[0], time[1])
        return y
    else:
        raise Exception("Wrong reward function for non-meal task")

# Mathematical expression for sleeping duration
def func_sleeping_duration(x, duration_min, duration_max):
    # Assume: duration_min <= duration_max
    # e.g.: min = 5, max = 12
    # the parameter 5/(max-min) makes sure when x>=max, 0.99 <= y <= 1 (saturation)
    if x >= duration_min:
        y = 1 - np.exp(-5 / (duration_max - duration_min) * (x - duration_min))
    else:
        y = 0
    return y

# Mathematical expression for bedtime of sleeping
# TODO: Extend the bedtime to later than 0:00
def func_sleeping_bedtime(x, bedtime_min, bedtime_max):
    # bedtime_min ∈ [21, 24] -> earliest time to go to bed: 21:00-24:00
    # bedtime_max ∈ [0, 4] -> latest time to go to bed: 0:00-4:00
    # e.g.: min = 22, max = 4
    if bedtime_min <= x <= 24:
        y = np.exp(-(x - bedtime_min))
    elif 0 <= x <= bedtime_max:
        y = np.exp(-(x + 24 - bedtime_min))
    else:
        y = 0
    return y

# Mathematical expression for deep sleeping cycle
def func_sleeping_cycle(x):
    # x: time of sleeping since bedtime, unit: hour
    # TODO
    pass

# Reward function of sleeping
def rwd_sleeping(x, bedtime, duration, sleeping, strictness, T = T):
    # Given: dict "sleeping" from yaml file
    # x: current real time
    # sleeping.keys(): duration_min, duration_max, bedtime_min, bedtime_max, enjoyment, productivity
    # Return: reward value, based on (bedtime, duration) pair, "reward" is 3D function of both bedtime and duration

    # Steps:
    # 1. check if the type is 'sleeping'
    # 2. duration dependent function: rwd1(t_d) = reward * (1-exp(-0.8(t_d-duration_min))) (duration_min <= t_d <= duration_max)
    # 3. bedtime dependent function: rwd2(t_b) = reward * exp(-(t_b-bedtime_min)) (bedtime_min <= t_b <= bedtime_max + 24)
    # 4. final reward: rwd(t_d, t_b) = sqrt(rwd1(t_d)*rwd(t_b))
    if sleeping["type"] == "sleeping":
        duration_min = sleeping["duration_min"]
        duration_max = sleeping["duration_max"]
        bedtime_min = sleeping["bedtime_min"]
        bedtime_max = sleeping["bedtime_max"]
        reward = rwd_after_strict(strictness, sleeping["enjoyment"], sleeping["productivity"])
        
        rwd = reward * np.sqrt(func_sleeping_duration(duration, duration_min, duration_max) * func_sleeping_bedtime(bedtime, bedtime_min, bedtime_max))   # TODO (future work): * func_sleeping_cycle(x)
        return rwd
    else:
        raise Exception("Wrong reward function for non-sleeping task")

# Contineous reward value in the contineous time space, for all tasks
def reward_contineous(x, task, strictness):
    # x: time slot (different def for different task)
    try:
        task_type = task["type"]
    except:
        raise Exception("Task '" + task["name"] + "' does not have input 'type'")

    if task_type == "fixed_time":
        y = rwd_fixed_time(x, task, strictness)     # x: current time
    elif task_type == "fixed_ddl":
        y = rwd_fixed_ddl(x, task, strictness)      # x: time passed since beginning
    elif task_type == "as_soon_as_possible":
        y = rwd_asap(x, task, strictness)           # x: time passed since beginning
    elif task_type == "fun":
        y = rwd_fun(x, task, strictness)            # x: current time
    elif task_type == "long_term":
        y = rwd_long_term(x, task, strictness)      # x: duration of the task
    elif task_type == "necessity":
        y = rwd_necessity(x, task, strictness)      # x: current time
    elif task_type == "meal":
        y = rwd_meal(x, task, strictness)           # x: current time
    else:
        raise Exception("Task '" + task["name"] + "' has undefined 'type' for continuous reward")
    return y

# Discrete reward (enjoyment & productivity) value over time period T, based on reward functinos in continuous time for all tasks
def reward_discrete(n, task, strictness, detailed = True, T = T):
    # Given: 
        # n: discrete number of T; have different meaning for different type of task
        # task: a dict, different "type" has different (contineous) reward function, all have been defined in the same function "reward_contineous"
    # Return: average reward during time period / time sampling window [n * T, (n + 1) * T] over certain detailed time length (e.g. each minute, or simple average of two ends)
    rwd = 0
    
    # Decide how "detailed" the average is
    if detailed:
        # Average over minutes
        count = int(np.floor(T * 60 + 1))
    else:
        # Average of two ends of the [nT, (n+1)T]
        count = 2

    for delta in np.linspace(n * T, (n + 1) * T, count):
        rwd += reward_contineous(np.mod(delta, 24), task, strictness)
    rwd = rwd / count
    return rwd

# Return task list from input 'tasks' dict, and check task validity
def input_analysis(tasks):
    # Given: dict of {task_name: task_content}
    # Return: task_name list
    task_names = list(tasks.keys())

    # Check validity of task params
    param = {'today': {'name', 'type', 'curr_time', 'day', 'strictness'}, \
             'sleeping': {'name', 'type', 'duration_min', 'duration_max', 'bedtime_min', 'bedtime_max', 'enjoyment', 'productivity'}, \
             'fixed_time': {'name', 'type', 'day', 'start', 'duration', 'switch', 'enjoyment', 'productivity'}, \
             'fixed_ddl': {'name', 'type', 'approx_time', 'deadline', 'switch', 'enjoyment', 'productivity'}, \
             'as_soon_as_possible': {'name', 'type', 'approx_time', 'switch', 'enjoyment', 'productivity'}, \
             'fun': {'name', 'type', 'enjoyment', 'productivity'}, \
             'long_term': {'name', 'type', 'insist_day', 'duration_max', 'enjoyment', 'productivity'}, \
             'necessity': {'name', 'type', 'time', 'duration', 'enjoyment', 'productivity'}, \
             'meal': {'name', 'type', 'time', 'duration', 'enjoyment', 'productivity'}}
    wrong_param = []

    # Check all necessary parameters for given tasks are provided in the input file
    for task_name in task_names:
        try:
            diff = param[tasks[task_name]["type"]].difference(set(tasks[task_name].keys()))
        except Exception as e:
            print("Task '" + task_name + "' has missing or undefined {'type'}!")
            wrong_param.append(task_name)
            continue
        
        if diff != set():
            print("Task '" + task_name + "' has missing parameter " + str(diff) + "!")
            wrong_param.append(task_name)

    # Check Task 'today' and 'sleeping' are provided
    diff = set(['today', 'sleeping']).difference(set(task_names))
    if diff != set():
        print("Inputs has missing Task " + str(diff) + "!")
    else:
        task_names.remove('today')
        task_names.remove('sleeping')        

    if len(wrong_param) != 0:
        raise Exception("Check inputs of " + str(set(wrong_param)) + " and try again!")

    return task_names

# Only consider plan for tomorrow (for now => TODO: future extension for plan for the same day)
# Policy random: naive, initial, randomly distribute any task for any T
def policy_random(tasks):
    # Init plan
    plan = {}

    # Extract 'strictness' info from input
    strictness = tasks['today']['strictness']

    # Plan about 'sleeping'
    sleeping = tasks['sleeping']
    getup_min = np.mod(sleeping['bedtime_min'] + sleeping['duration_min'], 24) # Assume getup_min > 0 (for now)
    getup_max = np.mod(sleeping['bedtime_max'] + sleeping['duration_max'], 24)

    # Assume bedtime_min ∈ [21, 24], bedtime_max ∈ [0, 4] for now => TODO: future extension for bedtime_min ∈ [0, 4]
    # 'bedtime_list', 'duration_list': discrete choice list for 'bedtime' and 'duration'
    bedtime_list = np.arange(sleeping['bedtime_min'] - 24, sleeping['bedtime_max'] + T, T)
    duration_list = np.arange(sleeping['duration_min'], sleeping['duration_max'] + T, T)
    bedtime = random.choice(bedtime_list)
    duration = random.choice(duration_list)
    print('bedtime: ' + str(np.mod(bedtime, 24)) + ':00\tduration: ' + str(duration) + 'h\tgetup time: ' + str(bedtime + duration) + ':00')

    # Sleep before 24:00
    plan['sleeping'] = {'name': 'sleeping'}
    if bedtime <= 0:
        plan['sleeping']['time'] = [0, bedtime + duration]
        plan['sleeping']['rwd'] = []
        for x in np.arange(0, bedtime + duration, T):
            plan['sleeping']['rwd'].append(rwd_sleeping(x, np.mod(bedtime, 24), duration, sleeping, strictness))
    else:
        plan['N/A'] = {'name': 'N/A', 'time': [0, bedtime], 'rwd': list(np.arange(0, bedtime, T) * 0)}
        plan['sleeping']['time'] = [bedtime, bedtime + duration]
        plan['sleeping']['rwd'] = []
        for x in np.arange(bedtime, bedtime + duration, T):
            plan['sleeping']['rwd'].append(rwd_sleeping(x, bedtime, duration, sleeping, strictness))

    if bedtime < 0:
        # Because circulant or symmetric
        plan['sleeping_'] = {'name': 'sleeping', 'time': [bedtime + 24, 24], 'rwd': []}
        for x in np.arange(bedtime + 24, 24, T):
            plan['sleeping_']['rwd'].append(rwd_sleeping(x, bedtime + 24, duration, sleeping, strictness))

    # Assume the daily plan is circulant (a.k.a. bedtime for the next day = bedtime of the planned day)
    if bedtime <= 0:
        # Active until before 24:00, then go to sleep (add another segment of sleeping)
        activetime = bedtime + 24
    else:
        # Active until 24:00
        activetime = 24

    # If bedtime after 0:00, extra time for other tasks
    time_list = list(np.arange(np.ceil((bedtime + duration) / T), np.floor(activetime / T), T))
    if 'N/A' in plan.keys():
        time_NA = plan['N/A']['time']
        time_list.extend(np.arange(np.ceil(time_NA[0] / T), np.floor(time_NA[1] / T), T))
        plan.pop('N/A')

    # Add random tasks into 'plan'
    task_names_copy = task_names[:]
    for n in time_list:
        task_curr = random.choice(task_names_copy)
        if tasks[task_curr]['type'] not in plan.keys():
            plan_ref = tasks[task_curr]['type']
            plan[plan_ref] = {'name': task_curr, 'time': [n * T, (n + 1) * T], 'rwd': []}

            # Modify 'n' for different meaning of time
            if plan_ref in ['fixed_time']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
            elif plan_ref in ['fun', 'necessity', 'meal']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)
            elif plan_ref in ['as_soon_as_possible', 'fixed_ddl']:
                rwd = reward_discrete(n - np.ceil((24 - tasks['today']['curr_time']) / T), tasks[task_curr], strictness)
            elif plan_ref in ['long_term']:
                rwd = reward_discrete(T, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)   # TODO: may not remove if T≠1: count the number of the long_term tasks => modify the rwd value

            plan[plan_ref]['rwd'].append(rwd)
        else:
            count = 0
            for task_prev in plan.keys():
                if task_prev.strip('_') == tasks[task_curr]['type']:
                    count += 1
            plan_ref = tasks[task_curr]['type'] + count*'_'
            plan[plan_ref] = {'name': task_curr, 'time': [n * T, (n + 1) * T], 'rwd': []}

            # Modify 'n' for different meaning of time
            if plan_ref.strip('_') in ['fixed_time']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
            elif plan_ref.strip('_') in ['fun', 'necessity', 'meal']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)
            elif plan_ref.strip('_') in ['as_soon_as_possible', 'fixed_ddl']:
                rwd = reward_discrete(n - np.ceil((24 - tasks['today']['curr_time']) / T), tasks[task_curr], strictness)
            elif plan_ref.strip('_') in ['long_term']:
                rwd = reward_discrete(T, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)

            plan[plan_ref]['rwd'].append(rwd)

    # print('Initial random plan: ' + str(plan))
    return plan

# Modify policy_random to consider about approx_time of fixed_ddl and asap tasks
def policy_random_modify(tasks):
    # Init plan
    plan = {}

    # Extract 'strictness' info from input
    strictness = tasks['today']['strictness']

    # Plan about 'sleeping'
    sleeping = tasks['sleeping']
    getup_min = np.mod(sleeping['bedtime_min'] + sleeping['duration_min'], 24) # Assume getup_min > 0 (for now)
    getup_max = np.mod(sleeping['bedtime_max'] + sleeping['duration_max'], 24)

    # Assume bedtime_min ∈ [21, 24], bedtime_max ∈ [0, 4] for now => TODO: future extension for bedtime_min ∈ [0, 4]
    # 'bedtime_list', 'duration_list': discrete choice list for 'bedtime' and 'duration'
    bedtime_list = np.arange(sleeping['bedtime_min'] - 24, sleeping['bedtime_max'] + T, T)
    duration_list = np.arange(sleeping['duration_min'], sleeping['duration_max'] + T, T)
    bedtime = random.choice(bedtime_list)
    duration = random.choice(duration_list)
    print('bedtime: ' + str(np.mod(bedtime, 24)) + ':00\tduration: ' + str(duration) + 'h\tgetup time: ' + str(bedtime + duration) + ':00')

    # Sleep before 24:00
    plan['sleeping'] = {'name': 'sleeping'}
    if bedtime <= 0:
        plan['sleeping']['time'] = [0, bedtime + duration]
        plan['sleeping']['rwd'] = []
        for x in np.arange(0, bedtime + duration, T):
            plan['sleeping']['rwd'].append(rwd_sleeping(x, np.mod(bedtime, 24), duration, sleeping, strictness))
    else:
        plan['N/A'] = {'name': 'N/A', 'time': [0, bedtime], 'rwd': list(np.arange(0, bedtime, T) * 0)}
        plan['sleeping']['time'] = [bedtime, bedtime + duration]
        plan['sleeping']['rwd'] = []
        for x in np.arange(bedtime, bedtime + duration, T):
            plan['sleeping']['rwd'].append(rwd_sleeping(x, bedtime, duration, sleeping, strictness))

    if bedtime < 0:
        # Because circulant or symmetric
        plan['sleeping_'] = {'name': 'sleeping', 'time': [bedtime + 24, 24], 'rwd': []}
        for x in np.arange(bedtime + 24, 24, T):
            plan['sleeping_']['rwd'].append(rwd_sleeping(x, bedtime + 24, duration, sleeping, strictness))

    # Assume the daily plan is circulant (a.k.a. bedtime for the next day = bedtime of the planned day)
    if bedtime <= 0:
        # Active until before 24:00, then go to sleep (add another segment of sleeping)
        activetime = bedtime + 24
    else:
        # Active until 24:00
        activetime = 24

    # If bedtime after 0:00, extra time for other tasks
    time_list = list(np.arange(np.ceil((bedtime + duration) / T), np.floor(activetime / T), T))
    if 'N/A' in plan.keys():
        time_NA = plan['N/A']['time']
        time_list.extend(np.arange(np.ceil(time_NA[0] / T), np.floor(time_NA[1] / T), T))
        plan.pop('N/A')

    # Add random tasks into 'plan'
    task_names_copy = task_names[:]
    task_count = {}
    for n in time_list:
        task_curr = random.choice(task_names_copy)
        while_start = time.time()       # In case of time-out
        while reward_discrete(n, tasks[task_curr], strictness) == 0:
            task_curr = random.choice(task_names_copy)
            while_end = time.time()
            if while_end - while_start > 3:
                break
        if tasks[task_curr]['type'] not in plan.keys():
            plan_ref = tasks[task_curr]['type']
            plan[plan_ref] = {'name': task_curr, 'time': [n * T, (n + 1) * T], 'rwd': []}

            # Modify 'n' for different meaning of time
            if plan_ref in ['fixed_time']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
            elif plan_ref in ['fun', 'necessity', 'meal']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)
            elif plan_ref in ['as_soon_as_possible', 'fixed_ddl']:
                rwd = reward_discrete(n - np.ceil((24 - tasks['today']['curr_time']) / T), tasks[task_curr], strictness)
                task_count[task_curr] = 1
                if task_count[task_curr] * T >= tasks[task_curr]['approx_time'] * procrastination:
                    task_names_copy.remove(task_curr)
            elif plan_ref in ['long_term']:
                rwd = reward_discrete(T, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)

            plan[plan_ref]['rwd'].append(rwd)
        else:
            count = 0
            for task_prev in plan.keys():
                if task_prev.strip('_') == tasks[task_curr]['type']:
                    count += 1
            plan_ref = tasks[task_curr]['type'] + count*'_'
            plan[plan_ref] = {'name': task_curr, 'time': [n * T, (n + 1) * T], 'rwd': []}

            # Modify 'n' for different meaning of time
            if plan_ref.strip('_') in ['fixed_time']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
            elif plan_ref.strip('_') in ['fun', 'necessity', 'meal']:
                rwd = reward_discrete(n, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)
            elif plan_ref.strip('_') in ['as_soon_as_possible', 'fixed_ddl']:
                rwd = reward_discrete(n - np.ceil((24 - tasks['today']['curr_time']) / T), tasks[task_curr], strictness)
                task_count[task_curr] += 1
                if task_count[task_curr] * T >= tasks[task_curr]['approx_time'] * procrastination:
                    task_names_copy.remove(task_curr)
            elif plan_ref.strip('_') in ['long_term']:
                rwd = reward_discrete(T, tasks[task_curr], strictness)
                task_names_copy.remove(task_curr)

            plan[plan_ref]['rwd'].append(rwd)

    # print('Initial random plan: ' + str(plan))
    return plan

# Based on the plan generated from policy_random(_modify) and replace randomly with tasks of higher rwd => local optimal result
def policy_random_optimal(tasks):
    # TODO
    pass

# Policy traversal: list all possible plans, calculate the plan with the max rwd
def policy_traversal(tasks):
    # Init plan, plan_list (all possible plans)
    plan = {}
    plan_list = []

    # Extract 'strictness' info from input
    strictness = tasks['today']['strictness']

    # Plan about 'sleeping'
    sleeping = tasks['sleeping']
    getup_min = np.mod(sleeping['bedtime_min'] + sleeping['duration_min'], 24) # Assume getup_min > 0 (for now)
    getup_max = np.mod(sleeping['bedtime_max'] + sleeping['duration_max'], 24)

    # Assume bedtime_min ∈ [21, 24], bedtime_max ∈ [0, 4] for now => TODO: future extension for bedtime_min ∈ [0, 4]
    # 'bedtime_list', 'duration_list': discrete choice list for 'bedtime' and 'duration'
    bedtime_list = np.arange(sleeping['bedtime_min'] - 24, sleeping['bedtime_max'] + T, T)
    duration_list = np.arange(sleeping['duration_min'], sleeping['duration_max'] + T, T)

    # TODO

    return plan

# Make the 'Initial plan' more neat: same continuous task in the same dict.key, all the tasks in the time order
def plan_sort(plan):
    newplan = {}
    task_names = list(plan.keys())

    # All the tasks in the same order
    time_list = []
    for task in task_names:
        time_list.append(plan[task]['time'][0])
    time_index = np.argsort(time_list)
    task_names = list(np.array(task_names)[time_index])

    # Same continuous task in the same key
    newplan[task_names[0]] = plan[task_names[0]]
    for i in range(1, len(plan)):
        last_task = list(newplan.keys())[-1]
        if task_names[i].strip('_') == last_task.strip('_') and plan[task_names[i]]['name'] == plan[last_task]['name']:
            time_ori = newplan[last_task]['time']
            time_new = plan[task_names[i]]['time']      # '_new': relative to 'newplan' reconstruction

            if time_ori[1] == time_new[0]:
                newplan[last_task]['time'] = [time_ori[0], time_new[1]]
                newplan[last_task]['rwd'].extend(plan[task_names[i]]['rwd'])
            else:
                newplan[task_names[i]] = plan[task_names[i]]
        else:
            newplan[task_names[i]] = plan[task_names[i]]

    # print('Sorted plan: ' + str(newplan))
    return newplan

# Visualize resulting plan for output
# E.g.: plan={'sleeping': {'time': [0, 6], 'rwd':[1, 2, 3, 4, 5, 4]}, 'breakfast': {'time': [6, 8], 'rwd': [2, 3]}}
def visualize_plan(plan, ax):
    # plan: type: dict, keys: task name, same as input file; each task: also dict, keys: 'time', 'rwd'; 'time': list, the beginning and ending hour of the day, 'rwd': discrete current reward corresponding discrete time period

    title_font = {'fontname': 'Arial', 'fontsize': 14, 'color': 'black', 'weight': 'bold', 'va': 'bottom'}
    axis_font = {'fontname': 'Arial', 'fontsize': 12, 'color': 'black', 'weight': 'normal'}
    text_font = {'fontname': 'Arial', 'fontsize': 12, 'weight': 'normal', 'ha': 'center', 'va': 'center'}

    if len(plan) == 0:
        raise Exception("Empty plan for visualization")

    # x, y: horizontal, vertical axes for the rwd-time output plot
    # For init
    x = [0]
    y = [0]
    x_max = 0
    y_max = 0

    # Iterate all the tasks in the plan
    for task in plan:
        # Assume all the 'task's in 'plan' follows the time order for now => TODO
        time = plan[task]['time']
        rwd = plan[task]['rwd']

        # To plot lines that are all connected
        x = [x[-1]]
        y = [y[-1]]

        # The first segment of plot
        if task == list(plan.keys())[0]:
            x.extend(np.linspace(time[0], time[1], int(np.floor((time[1] - time[0]) / T)) + 1)[:-1])
            y.extend(rwd)
            p = ax.plot(x[1:], y[1:], '.-')
            color = p[0].get_color()
        else:
            x.extend(np.linspace(time[0], time[1], int(np.floor((time[1] - time[0]) / T)) + 1)[:-1])
            y.extend(rwd)
            ax.plot(x[:2], y[:2], '.-', color = color)
            p = ax.plot(x[1:], y[1:], '.-')
            color = p[0].get_color()

        # Plot the last segment
        if task == list(plan.keys())[-1]:
            x = [x[-1], x[-1] + T]
            y = [y[-1], y[-1]]
            ax.plot(x, y, '.-', color = color)

        ax.text((time[0] + time[1]) / 2, np.max(y[1:]) + 0.5, plan[task]['name'], color = color, **text_font)

        x_max = max(x_max, np.max(x))
        y_max = max(y_max, np.max(y))

    # Add axes
    ax.set_xlim(-0.5, 24.5)
    ax.set_ylim(0, int(y_max + 0.5) + 1)
    ax.set_xticks(np.linspace(0, x_max, int(x_max / T + 1)))
    ax.set_yticks(np.linspace(0, int(y_max + 0.5) + 1, int(y_max + 0.5) + 2))
    xlabels = [str(int(i) % 24) + ":00" for i in range(25)]
    ax.set_xticklabels(xlabels, rotation = -45)

    ax.grid(alpha = 0.5, linestyle = 'dashed', linewidth = 0.5)

    # Add plot labels
    ax.set_title('Time Schedule Planner', **title_font)
    ax.set_xlabel('Time', **axis_font)
    ax.set_ylabel('Reward Value', **axis_font)




# # Tests
# # For input test and debug
tasks = inputYAML()
# reward_contineous(10,tasks['dinner'],0.5)
# print(tasks)
# print(tasks['dinner'])
# print(len(tasks))


# # For policy test
task_names = input_analysis(tasks)
plan = policy_random_modify(tasks)
plan = plan_sort(plan)
for each in plan.keys():
    print("'"+str(each)+"': "+str(plan[each])+', \\')


# # For rwd func test and debug
# lab={"type":"as_soon_as_possible", "approx_time": 2, "enjoyment": 6, "productivity": 6}
# sleeping={"type":"sleeping","duration_min":5,"duration_max":12,"bedtime_min":22,"bedtime_max":4,"enjoyment":6,"productivity":2}
# house={"type":"necessity","time":[17],"duration":0.75,"enjoyment":0,"productivity":10}
# x=np.linspace(15,20,100)
# y=[]
# for eachx in x:
#     y.append(reward_contineous(eachx,house,0.5))
# y=np.array(y)
# plt.plot(x,y,"r")
# plt.show()

# # For output
# plan={'sleeping':{'time':[0,6],'rwd':[1,2,3,4,5,5]},'breakfast':{'time':[6,8],'rwd':[2,3]},'film':{'time':[8,14],'rwd':[5,2,7,9,1,5]}}
fig, ax = plt.subplots(dpi = 100)
visualize_plan(plan, ax)
plt.tight_layout()
plt.show()
# fig.savefig("planner.png", dpi = 200, bbox_inches = 'tight')