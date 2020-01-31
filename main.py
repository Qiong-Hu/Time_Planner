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
approx_err = 1.4    # Procrastination time percentage based on approx_time

# Read input parameters from YAML file, default filename: 'todo.yaml'
def inputYAML(filename = 'todolist2.yaml'):
    # Return a dictionary of potential tasks with input parameters
    if os.path.isfile(filename):
        file = open(filename)
        tasks = yaml.load(file)
        file.close()
        return tasks
    else:
        raise Exception("Can't find file '" + filename + "'")

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

        xdata = [0, approx_time * approx_err, deadline]
        ydata = [reward, reward / 2, reward / 5]
        if xdata[1] <= xdata[2]:
            if xdata[0] <= x <= xdata[1]:
                y = findfunc_fixed_ddl(x, (xdata[0], ydata[0]), (xdata[1], ydata[1]))
            elif xdata[1] < x <= xdata[2]:
                y = findfunc_fixed_ddl(x, (xdata[1], ydata[1]), (xdata[2], ydata[2]))
            else:
                y = 0
        else:
            if 0 <= x <= deadline:
                y = findfunc_fixed_ddl(x, (xdata[0], ydata[0]), (xdata[2], ydata[2]))
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

        xdata = [0, approx_time * approx_err]
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
        y = 1 - np.exp(- 5 / (duration_max - duration_min) * (x - duration_min))
    else:
        y = 0
    return y

# Mathematical expression for bedtime of sleeping
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

# Reward function of sleeping
def rwd_sleeping(bedtime, duration, sleeping, strictness, T = T):
    # Given: dict "sleeping" from yaml file
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
        
        rwd = reward * np.sqrt(func_sleeping_duration(duration, duration_min, duration_max) * func_sleeping_bedtime(bedtime, bedtime_min, bedtime_max))

        return rwd
    else:
        raise Exception("Current task is not 'sleeping'")

# Contineous reward value in the contineous time space, for all tasks
def reward_contineous(x, task, strictness):
    # x: time slot (different def for different task)
    try:
        task_type = task["type"]
    except:
        raise Exception("Current task does not have input 'type'")

    if task_type == "fixed_time":
        y = rwd_fixed_time(x, task, strictness)     # x: current time
    elif task_type == "fixed_ddl":
        y = rwd_fixed_ddl(x, task, strictness)      # x: time passed since beginning
    elif task_type == "as_soon_as_possible":
        y = rwd_asap(x, task, strictness)           # x: time passed since beginning
    elif task_type == "fun":
        y = rwd_fun(x, task, strictness)            # x: whichever def
    elif task_type == "long_term":
        y = rwd_long_term(x, task, strictness)      # x: duration of the task
    elif task_type == "necessity":
        y = rwd_necessity(x, task, strictness)      # x: current time
    elif task_type == "meal":
        y = rwd_meal(x, task, strictness)           # x: current time
    else:
        raise Exception("Current task has undefined 'type' for continuous reward")
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
        count = round(T * 60 + 1)
    else:
        # Average of two ends of the [nT, (n+1)T]
        count = 2

    for delta in np.linspace(n * T, (n + 1) * T, count):
        rwd += reward_contineous(np.mod(delta, 24), task, strictness)
    rwd = rwd / count
    return rwd

# Policy 1: naive, calculate every possibilities for every T 
def policy_naive(tasks):
    pass

# Visualize output result
def output(plan):
    pass




# # Tests
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



# # For input test and debug
todolist = inputYAML()
# print(todolist)
# print(len(todolist))

