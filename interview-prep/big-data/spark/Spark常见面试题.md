# Spark基础
1. Spark的任务执行流程
___
2. Spark的运行流程
___
3. Spark的作业运行流程是怎么样的?
___
4. Spark的特点
___
5. Spark源码中的任务调度
___
6. Spark作业调度
___
7. Spark的架构
___
8. Spark的使用场景
___
9. Spark on standalone模型、YARN架构模型(画架构图)
___
10. Spark的yarn-cluster涉及的参数有哪些?
___
11. Spark提交job的流程
___
12. Spark的阶段划分
___
13. Spark处理数据的具体流程说下
___
14. Sparkjoin的分类
___
15. Spark map join的实现原理
___
16. 介绍下Spark Shuffle及其优缺点
___
17. 什么情况下会产生Spark Shuffle?
___
18. 为什么要Spark Shuffle?
___
19. Spark为什么快?
___
20. Spark为什么适合迭代处理?
___
21. Spark数据倾斜问题，如何定位，解决方案
___
22. Spark的stage如何划分?在源码中是怎么判断属于Shuffle Map Stage或Result Stage的?
___
23. Spark join在什么情况下会变成窄依赖?
___
24. Spark的内存模型?
___
25. Spark分哪几个部分(模块)?分别有什么作用(做什么，自己用过哪些，做过什么)?
___
26. RDD的宽依赖和窄依赖，举例一些算子
___
27. Spark SQL的GroupBy会造成窄依赖吗?
___
28. GroupBy是行动算子吗
___
29. Spark的宽依赖和窄依赖，为什么要这么划分?
___
30. 说下Spark中的Transform和Action，为什么Spark要把操作分为Transform和Action?常用的列举一些，说下算子原理
___
31. Spark的哪些算子会有shuffle过程?
___
32. Spark有了RDD，为什么还要有Dataform和DataSet?
___
33. Spark的RDD、DataFrame、DataSet、DataStream区别?
___
34. Spark的Job、Stage、Task分别介绍下，如何划分?
___
35. Application、job、Stage、task之间的关系
___
36. Stage内部逻辑
___
37. 为什么要根据宽依赖划分Stage?为
___
38. 什么要划分Stage
___
39. Stage的数量等于什么
___
40. 对RDD、DAG和Task的理解
___
41. DAG为什么适合Spark?
___
42. 介绍下Spark的DAG以及它的生成过程
___
43. DAGScheduler如何划分?干了什么活?
___
44. Spark容错机制?
___
45. RDD的容错
___
46. Executor内存分配?
___
47. Spark的batchsize，怎么解决小文件合并问题?
___
48. Spark参数(性能)调优
___
49. 介绍一下Spark怎么基于内存计算的
___
50. 说下什么是RDD(对RDD的理解)?RDD有哪些特点?说下知道的RDD算子
___
51. RDD底层原理
___
52. RDD属性
___
53. RDD的缓存级别?
___
54. Spark广播变量的实现和原理?
___
55. reduceByKey和groupByKey的区别和作用?
___
56. reduceByKey和reduce的区别?
___
57. 使用reduceByKey出现数据倾斜怎么办?
___
58. Spark SQL的执行原理?
___
59. Spark SQL的优化?
___
60. 说下Spark checkpoint
___
61. Spark SQL与DataFrame的使用?
___
62. Sparksql自定义函数?怎么创建DataFrame?
___
63. HashPartitioner和RangePartitioner的实现
___
64. Spark的水塘抽样
___
65. DAGScheduler、TaskScheduler、SchedulerBackend实现原理
___
66. 介绍下Sparkclient提交application后，接下来的流程?
___
67. Spark的几种部署方式
___
68. 在Yarn-client情况下，Driver此时在哪
___
69. Spark的cluster模式有什么好处
___
70. Driver怎么管理executor
___
71. Spark的map和flatmap的区别?
___
72. Spark的cache和persist的区别?它们是transformaiton算子还是action算子?
___
73. Saprk Streaming从Kafka中读取数据两种方式?
___
74. Spark Streaming的工作原理?
___
75. Spark Streaming的DStream和DStreamGraph的区别?
___
76. Spark输出文件的个数，如何合并小文件?
___
77. Spark的driver是怎么驱动作业流程的?
___
78. Spark SQL的劣势?
___
79. 介绍下Spark Streaming和Structed Streaming
___
80. Spark为什么比Hadoop速度快?
___
81. DAG划分Spark源码实现?
___
82. Spark Streaming的双流join的过程，怎么做的?
___
83. Spark的Block管理
___
84. Spark怎么保证数据不丢失
___
85. Spark SQL如何使用UDF?
___
86. Spark温度二次排序
___
87. Spark实现wordcount
___
88. Spark Streaming怎么实现数据持久化保存?
___
89. Spark SQL读取文件，内存不够使用，如何处理?
___
90. Spark的lazy体现在哪里?
___
91. Spark中的并行度等于什么
___
92. Spark运行时并行度的设署
___
93. Spark SQL的数据倾斜
___
94. Spark的exactly-once
___
95. Spark的RDD和partition的联系
___
96. park 3.0特性
___
97. Spark计算的灵活性体现在哪里
