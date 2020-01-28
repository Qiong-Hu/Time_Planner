#coding: UTF-8
'''
=================== License Information ===================
Author: 	June Hu
Email: 		junesirius@ucla.edu
Version: 	Ver 2.0.0
Date: 		January 25, 2020
'''

import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.optimize import curve_fit
import time
import random
import yaml

T = 1				# For now, sampling: 1 hour (min time on each task is 1h)
					# Suggested sampling time duration: 0.25 hour (15 mins)
					# T must = 60/interger
approx_err = 1.4	# Procrastination time percentage based on approx_time

# Read input parameters from YAML file, default filename: 'todo.yaml'
def input(filename = 'todolist.yaml'):
	# Return a dictionary of potential tasks with input parameters
	file = open(filename)
	tasks = yaml.load(file)
	file.close()
	return tasks

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
	# x: time duration of the task
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

# Reward function of daily-necessary tasks
def rwd_necessity(x, task, strictness):
	# x: tbd
	# task.keys(): type, time, duration, enjoyment, productivity
	if task["type"] == "necessity":
		duration = task["duration"]
		reward = rwd_after_strict(strictness, task["enjoyment"], task["productivity"])

		if 0 <= x <= duration:
			y = reward
		else:
			y = 0
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
	y = pow(logisticSigmoid((x - l + 1) * 3), 3) + pow(logisticSigmoid((r - x) * 3), 3) - 1
	return y

# Reward function of meals
def rwd_meal(x, task, strictness):
	# time = [start_time, end_time], end_time - start_time = 3 hours
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
	# x: time slot (different definition for different task)
	try:
		task_type = task["type"]
	except:
		raise Exception("Current task does not have input 'type'")

	if task_type == "fixed_time":
		y = rwd_fixed_time(x, task, strictness)
	elif task_type == "fixed_ddl":
		y = rwd_fixed_ddl(x, task, strictness)
	elif task_type == "as_soon_as_possible":
		y = rwd_asap(x, task, strictness)
	elif task_type == "fun":
		y = rwd_fun(x, task, strictness)
	elif task_type == "long_term":
		y = rwd_long_term(x, task, strictness)
	elif task_type == "necessity":
		y = rwd_necessity(x, task, strictness)
	elif task_type == "meal":
		y = rwd_meal(x, task, strictness)
	else:
		raise Exception("Current task has undefined 'type'")
	return y

# Discrete reward (enjoyment & productivity) value over time period T, based on reward functinos in continuous time for all tasks
def reward_discrete(t, task, strictness, T = T):
	# Given: task is a dict, different "type" has different (contineous) reward function 
	# Return: average reward over time (t, t + T)
	# t: have different meaning for different type of task, unit: h
	rwd = 0

	start = int(t * 60 / (T * 60)) * T
	end = start + T - 1 / 60
	for delta in np.linspace(start, end, round(T * 60)):
		rwd += reward_contineous(delta, task, strictness)

	rwd = rwd / (T * 60)
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
sleeping={"type":"sleeping","duration_min":5,"duration_max":12,"bedtime_min":22,"bedtime_max":4,"enjoyment":6,"productivity":2}
# x=np.linspace(0,15,100)
# y=[]
# for eachx in x:
# 	y.append(func_sleeping_duration(eachx,5,12))
# y=np.array(y)
# plt.show()



# # For input test and debug
# todolist = input()
# tasks = {}
# i = 0
# for each in todolist.keys():
# 	i=i+1
# 	tasks[each] = todolist[each]
# 	if i>4:
# 		break
# print(tasks)
# print(len(todolist))

