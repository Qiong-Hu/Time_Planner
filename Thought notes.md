# Notes of casual thoughts 

## Title & Abstract (draft at 20200123)

### Title options
- A Time Management Planner via approximate Markov decision process

### Keywords for related-work search
- decision making, time scheduling
- time scheduling strategy
- production scheduling strategy
- hybrid optimization strategy
- optimization, scheduling, decision-making

### Abstract
- Background: Time management becomes increasingly difficult nowadays due to the overloading daily tasks and all kinds of pleasant desires.
- Motivation: People have come up with all kinds of approaches to manage the time schedule, and the burden may be reduced with the help of machine decision-making process.
- System intro: Therefore, we introduce our system ATMP, "A Time Management Planner".
- Method: With a few necessary inputs of the task information in a graphical interface, the planner would automatically come up with some suggested time schedules. The user can choose to follow them strictly or loosely, or run multiple times with the process of the tasks.
- Method detail: The planner applies multiple optimization algorithms, on the basis of Markov Decision Process (MDP). The policy would keep updating until obtain a maximum gain and a minimum cost function are obtained within some range of errors.
- Results: We tested the planner in a broad user-study, in various situations, and the results and feedbacks both show a positive potential application and development of our system.

- Put together: Time management becomes increasingly difficult nowadays due to the overloading daily tasks and all kinds of pleasant desires. People have come up with all kinds of approaches to manage the time schedule, and the burden may be reduced with the help of machine decision-making process. Therefore, we introduce our system ATMP, "A Time Management Planner". With a few necessary inputs of the task information in a graphical interface, the planner would automatically come up with some suggested time schedules. The user can choose to follow them strictly or loosely, or run multiple times with the process of the tasks. The planner applies multiple optimization algorithms, on the basis of Markov Decision Process (MDP). The policy would keep updating until obtain a maximum gain and a minimum cost function are obtained within some range of errors. We tested the planner in a broad user-study, in various situations, and the results and feedbacks both show a positive potential application and development of our system.


## Related works
## JANE上根据title和abstract自动找来的（20200123）
- Alagoz O, Hsu H, Schaefer AJ, Roberts MS. Markov decision processes: a tool for sequential decision making under uncertainty. Med Decis Making. 2010
- Da Silva FL, Glatt R, Costa AHR. MOO-MDP: An Object-Oriented Representation for Cooperative Multiagent Reinforcement Learning. IEEE transactions on cybernetics. 2019
- Ma Y, Zhao T, Hatano K, Sugiyama M. An Online Policy Gradient Algorithm for Markov Decision Processes with Continuous States and Actions. Neural computation. 2016
- Mirian MS, Ahmadabadi MN, Araabi BN, Siegwart RR. Learning active fusion of multiple experts' decisions: an attention-based approach. Neural computation. 2011
- Patrick J. A Markov decision model for determining optimal outpatient scheduling. Health care management science. 2012
- Dickerson PS. The Evolving Role of A Nurse Planner. Journal of continuing education in nursing. 2016
- Choi SE, Brandeau ML, Basu S. Dynamic treatment selection and modification for personalised blood pressure therapy using a Markov decision process model: a cost-effectiveness analysis. BMJ open. 2017
- Haeri S, Trajkovic L. Virtual Network Embedding via Monte Carlo Tree Search. IEEE transactions on cybernetics. 2018
- 


### Google Scholar找来的
- Real-time tracking of activity scheduling/schedule execution within a unified data collection framework. JJ Zhou, R Golledge - Transportation Research Part A: Policy and Practice, 2007 - Elsevier
- A high performance video transform engine by using space-time scheduling strategy. YH Chen, TY Chang - IEEE transactions on very large scale …, 2011 - ieeexplore.ieee.org
- A scheduling strategy on load balancing of virtual machine resources in cloud computing environment. J Hu, J Gu, G Sun, T Zhao - 2010 3rd International symposium …, 2010 - ieeexplore.ieee.org
- A new variable production scheduling strategy for deteriorating items with time-varying demand and partial lost sale. YW Zhou, HS Lau, SL Yang - Computers & Operations Research, 2003 - Elsevier
- A prediction-based real-time scheduling advisor. PA Dinda - Proceedings 16th International Parallel and …, 2001 - ieeexplore.ieee.org
- A weighted mean time min-min max-min selective scheduling strategy for independent tasks on grid. SS Chauhan, RC Joshi - 2010 IEEE 2nd International Advance …, 2010 - ieeexplore.ieee.org
- Game Theory Based Real‐Time Shop Floor Scheduling Strategy and Method for Cloud Manufacturing. Y Zhang, J Wang, S Liu, C Qian - International Journal of …, 2017 - Wiley Online Library
- A mathematical programming model for scheduling steelmaking-continuous casting production. L Tang, J Liu, A Rong, Z Yang - European Journal of Operational Research, 2000 - Elsevier
- Precise scheduling method for daily generation plan of large-scale hydropower station based on comprehensive state evaluation strategy for generating units. YQ Wang, JZ Zhou, L Mo, R Zhang… - Power System …, 2012 - en.cnki.com.cn
- [HTML] A comparison of three heuristics on a practical case of sub-daily staff scheduling. M Günther, V Nissen - Annals of Operations Research, 2014 - Springer
- Dynamic multi-objective optimization and decision-making using modified NSGA-II: a case study on hydro-thermal power scheduling. K Deb, S Karthik - … conference on evolutionary multi-criterion optimization, 2007 - Springer
- 


## Some thoughts
- 这个project的标题取缩写ATMP（A Time Management Planner）
- 原数据/输入值的储存：maybe use yaml to store raw datas and pyyaml to load
- rewards的计算方法（按比例）：define "rewards" in both "enjoyment" and "productivity", define final goal reward as "strictness" ∈ [0, 1], rig=0 means max enjoyment (max fun tasks), rig=1 means max productivity (max working tasks), rig∈(0, 1) means somewhere in between, the user can decide by themselves, default settings can have lower rig in weekends
- 生产力函数：
	- 不同type的生产力函数的定义互相独立
	- 每个任务的真实生产力值都包含与睡眠有关的参数（也可以在最后计算总rwd的时候再乘）："productivity" function of each task is independent according to the task type, but the "real" productivity of the task should multiply a parameter that is related to "sleeping time" and "sleeping hour"
	- 可以是discrete的函数，参数是time slot的编号，就能用离散的算法来减少计算量等；以后改了time sample的长度也只是改这些离散函数的局部变量的time slot的编号就行
- 任务切换有缓冲时间（或者直接用交通时间15min？）：if switch to new task, minus 3-5min to be new "effective time" in the next sampling time T
- 以下是生产力函数的定义方法：
	- sleeping
		- have enjoyment rewards, exponentially increasing function
		- low direct productivity, extra-productivity influence other tasks' productivity as a multiplication parameter and enjoyment by bedtime and duration
		- 睡眠时间和长度都对其他活动的生产力和愉悦值有一个乘法参数的影响；其中睡眠长度的影响以5h14min作为一个极大值的初始值，以1.5h为周期在极大极小里变化，符合深度睡眠和浅睡眠周期，所以要乘一个三角函数
	- fixed-time tasks
		- example: fixed task/lecture/appointment/etc
		- use an extremely high constant, step, reward function
		- fix it in the function to avoid unnecessary iteration (?)
		- fixed-time task also have elasticity（虽然说是fixed-time但是其实有些也是可以有弹性的）：按照reward作为概率来决定去不去、去多久/迟到多久、大于多少的productivity就是一个接近1的概率表示必须去不能迟到
	- fixed-DDL tasks
		- zero rewards after DDL
		- the later the lower both rewards, constant minus stress level (exponentially increasing function)
		- starting enjoyment constant depends on how much you like about the task
	- as-soon-as-possible (ASAP) (without DDL) tasks (原称the-earlier-the-better tasks)
		- exponentially decreasing function for both rewards
		- starting rewards value depend on how important and fun the task is
		- 对不同的ASAP任务，指数衰减速度都相同：constant decreasing speed over different ASAP tasks
	- fun tasks
		- high-constant enjoyment
		- low-constant productivity
		- weighted-randomly pick
	- long-term tasks
		- 定义/特点：not so beneficial for now, beneficial if stick longer
		- linearly increasing rewards (for both) over time
		- randomly replace/add into the plan if none in weekly/daily plan
	- meal
		- 定义了一个时间段范围，只有在范围内吃饭才能有比较高的rwd (for both)，根据时间段的上下bound作为高斯函数的参数得到某种类似拉宽的高斯或者边缘比较圆润的step funcs
		- 烧饭时间也算进meal时间里了
	- trivial/daily-necessity tasks
		- gaussian function for both rewards
		- add fixed time (after get up, before classes/fixed-time appointments, before go to bed, etc) for transportation
		- -> Update: 交通时间算到每件事件单独里面去？或者单独定义成一个type再重新考虑一下)
		- rewards funcs对于不同的trivial task都一样（为了减少工作量，没必要单独考虑各个不重要不紧急又必须做的小事）
		- 选择/schedule的时候随机：randomly pick some，增加一些（基于rwd的）随机函数进行选择，所以最终的总reward可能不是necessarily最优的reward但是更符合人自己的行为习惯
		- 大部分都可以被压缩：can squeeze some of them
		- 看手机这种可以写到fun type里去，所以trivial task（已经扣掉了吃饭、睡觉、交通（可能）、看手机等，剩下的只有洗漱穿衣洗澡扫地等了）
- generate in sampling time of 30min (tomato clock) for now (may be shorter or longer later, according to the practical come-out result，以后改的sample也最好是能被60除完还是整数的为了方便计算，所以只从60的因数里面选), for at least 2 days, at most 7 days
- 在每种设定下寻找（寻找最优解的）policy的iteration（来自robotics的算法们）中：
	- initial policy：可以用完全随机生成的策略，每一个下一段time sample都从任务列表里任意选一个还没有完成的（已使用总时间<需要的总时间×拖延比例）
	- 稍微有点优化的policy：在每一个下一段time sample的时候寻找当前的局部最优解（选择哪个活动可能让今日总reward最大） -> 缺陷：找不到全局最优解，对于那些当前/活动早期阶段reward还较低需要积累效果的任务就会（几乎）没有安排（就像生活中有些人确实用的是这种策略所以没法坚持那些long-term goal比如健身、学习新语言新乐器等）
	- 进一步优化的policy：……（**重点TODO**：需要查文献找MDP、SLAM算法进行参考等，重点的reference paper的来源）

- 可以有3种不同设定（每种设定有不止一种寻找最优值的算法）：
	1. 第1种是reward-based，包括一定比例的enjoyment和productivity，目标schedule可以得到尽量大的总reward
	1. 第2种是cost-based，设定人一天的能量值（精神方面的energetic）和体力值（physically的衡量）
	1. 第3种可以把这两个都组合起来
- 关于第1种设定已经在前面写了很多了，关于第2种：
	- 人一天的初始能量和体力值可以在早上的时候自己更新作为强制输入，也可以用前一天晚上的输入值根据睡眠时长和时间的某种函数（可以基本类似设定1的那些函数）
	- 每一个活动都有对能量和体力的增减，注意这里的能量值在经过一个（喜欢的/有趣的）活动之后增加，体力值只能减少
	- 但是经过一天的各种活动安排schedule，睡前的能量值和体力值必须低于某个阈值，否则就需要推迟睡眠时间（/就会不困不想睡等）
	- 最好一天保持能量值都在某个阈值范围内（所以必做任务和开心任务就能掺起来协调一下）
	- 有些活动有最低能量值和最低体力值要求，所以必须趁着体力值下降到这个最低要求前（在一天里比较早的时间）执行掉，同时又要有提高能量、低体力消耗的活动掺在中间调剂
	- 对于不能完全确定能量影响的活动可以增加随机函数或者在某个constant附近增加高斯随机噪音
	- 缺点：
		- 不能体现出ASAP task需要尽早完成，在处理时跟fixed-time task几乎一样
		- 可能找不到存在的解决/安排方案 -> which is 正常的，因为日常生活中因为想做的事情太多确实有可能安排不出能实现所有事情的time schedule -> 解决方案：调节所有设定了硬性阈值/上下bound的地方
- 第1种设定的缺点：不能劳逸结合，不同任务安排在不同时间对总reward没有影响（除了sleeping、transportation、fixed-time task等有强制时间节点要求的任务） -> 所以结合第1、2种设定的优缺点就有了结合版的第3种：用第1种搜索出适合安排在这一天的任务，用第2种把它们合理安排到一天中去，理论上这第3种应该是能得出最合理结果的（能体现各个任务的不同重要性、也能劳逸结合、理论上也应该不会出现不可解/得不出schedule建议的问题）
- 关于每种设定的每种算法都可以找user-study（第一批user study从身边朋友开始，允许online地参与），让他们提供输入值，对提供的输出建议进行打分或严格实施一段时间来进行反馈；在user-study的最前面进行采访，询问平常的时间管理方法和a typical day；与其他time management的方法（传统或其他算法）作对比实验；要确定用什么方法来衡量效果

## Future works
collaborate with Google Calendar, plan out time management depends on tasks/hobbies/etc -> negative influence on human (?): 可能会让人更懒更有依赖、更加不能自己安排schedule/time
