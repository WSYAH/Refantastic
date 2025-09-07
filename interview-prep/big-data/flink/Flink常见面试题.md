# Flink基础
### 1. Flink架构
![flink架构](../../images/flink_infa.png)
Flink 架构是一个经典的主从（Master-Worker）架构，设计目标是支持高吞吐、低延迟、 Exactly-Once 语义的大规模分布式流处理。其核心组件如下图所示，协同工作以执行分布式数据流应用。
Flink采用经典的主从（Master-Worker）架构：JobManager作为主节点负责接收作业、调度任务、协调检查点（Checkpoint）及故障恢复；TaskManager
作为工作节点提供多个任务槽（Task Slots）执行具体任务、进行数据交换和状态存储；客户端提交作业后，JobManager将任务分配至TaskManager槽位，
并通过分布式快照机制实现容错，共同构成高吞吐、低延迟的分布式流处理系统。
___
### 2. Flink的窗口了解哪些，都有什么区别，有哪几种?如何定义?
Flink的窗口（Window）是将无界数据流划分为有限数据块进行处理的核心机制，主要分为三类：滚动窗口（Tumbling Window）（固定大小、不重叠）、滑
动窗口（Sliding Window）（固定大小、可重叠）和会话窗口（Session Window）（基于不活动间隔的动态窗口）。它们的区别主要在于窗口划分方式和重
叠性，可通过window()算子并传入相应窗口分配器（如TumblingEventTimeWindows.of(Time.seconds(5)))来定义。
```text
// 1. 滚动窗口（固定5秒）
dataStream
  .keyBy(...)
  .window(TumblingEventTimeWindows.of(Time.seconds(5))) // 事件时间
  .reduce(...);

// 2. 滑动窗口（每5秒统计一次最近10秒的数据）
dataStream
  .keyBy(...)
  .window(SlidingEventTimeWindows.of(Time.seconds(10), Time.seconds(5)))
  .reduce(...);

// 3. 会话窗口（会话超时时间5秒）
dataStream
  .keyBy(...)
  .window(EventTimeSessionWindows.withGap(Time.seconds(5)))
  .reduce(...);
```
滚动窗口：固定大小，无重叠，适用于周期性聚合（如每分钟浏览量）。  
滑动窗口：固定大小，有重叠，适用于连续统计（如每5秒更新最近10秒均值）。  
会话窗口：动态大小，基于数据活跃度，适用于用户行为分析（如用户会话划分）。  
___
### 3. Flink窗口函数，时间语义相关的问题
Flink的窗口函数依赖于特定的时间语义（由env.setStreamTimeCharacteristic()设置）来决定如何划分窗口和计算时间：事件时间（Event Time） 以数据自带的时间戳为准，结合水位线（Watermark）处理乱序事件，保证计算结果准确但延迟较高；处理时间（Processing Time） 以系统处理时刻为准，延迟最低但无法处理乱序数据；摄入时间（Ingestion Time） 是折中方案，以数据进入Flink的时间为准。窗口函数（如ReduceFunction、AggregateFunction或ProcessWindowFunction）则基于这些时间语义在窗口触发时对框选的数据进行聚合计算
___
### 4. 介绍下Flink的watermark(水位线)，watermark需要实现哪个实现类，在何处定义?有什么作用?
Flink的水位线（Watermark）是一种衡量事件时间进度的特殊时间戳，用于在乱序事件流中合理推断所有数据是否已到位；它需要实现WatermarkGenerator接口（或使用内置策略），通常在数据源或其后通过assignTimestampsAndWatermarks方法定义；其核心作用是解决乱序问题，通过设定一个允许延迟的时间阈值来触发窗口计算、保障计算结果的相对准确性，并在保证低延迟的同时实现正确性。
___
### 5. Flink的窗口(实现)机制
Flink的窗口实现机制基于分配器（Window Assigner） 和触发器（Trigger） 的协同工作：分配器负责将到达的数据元素分配到对应的窗口（如滚动、滑动或会话窗口），触发器则基于时间（事件时间或处理时间）或数据特征（如计数）决定何时触发该窗口的计算；窗口内容由状态后端(State backend) 存储，并在触发时由窗口函数（如ReduceFunction） 进行聚合处理，最后输出结果并清理窗口状态。
<br>
State（状态）是计算过程中的中间数据（如累加器的值、窗口内聚合的结果、用户会话信息），而状态后端（State Backend）是存储、访问和管理这些State的底层基础设施和策略，它决定了State存储在何处（内存、磁盘）、如何存储（Java堆、堆外、RocksDB）以及如何做容错（异步/同步快照到HDFS/S3）。

___
### 6. 说下Flink的CEP
Flink CEP（复杂事件处理）是其内置的一个库，用于在数据流中检测基于时间关系的复杂事件模式（Pattern）；用户通过定义由简单事件构成的规则序列（如“登录失败后5分钟内再次失败”），CEP引擎即可实时匹配并输出满足该模式的事件组合，广泛应用于实时风控、入侵检测和业务流程监控等场景。
___
### 7. 说一说Flink的Checkpoint机制
Flink的Checkpoint机制是其实现容错和精确一次（Exactly-Once）语义的核心：它通过周期性、异步地对分布式数据流中的所有算子状态（State）生成
全局一致性快照（包含处理位置和状态值），并将这些快照持久化到可靠存储（如HDFS/S3）中；当发生故障时，Flink可从最近一次成功的Checkpoint恢复
整个流处理作业的状态和处理位置，实现无数据丢失和状态一致性。
___
### 8. Flink的Checkpoint底层如何实现的?savepoint和checkpoint有什么区别?
Flink Checkpoint的底层实现基于Chandy-Lamport分布式快照算法：JobManager会定期向所有Source算子注入一种特殊的屏障信号（Barrier），该屏障会随着数据流向下游传播；当算子收到屏障时，会立即对自己的状态进行异步快照（写入状态后端），并将屏障广播到所有输出通道；屏障流经整个DAG图后，所有算子的状态快照组合起来即形成一个全局一致的、具有同一时间戳的检查点（Checkpoint），并最终由JobManager确认后存储到持久化系统（如HDFS/S3）中，从而保证分布式状态的一致性。
<br>
Savepoint和Checkpoint的核心区别在于目的与生命周期：Checkpoint是Flink自动周期性触发的容错机制，设计轻量且生命周期由框架管理（故障恢复后自动清理），主要用于快速故障恢复；而Savepoint是用户手动触发的全局状态快照，格式稳定且可长期保存，主要用于版本升级、代码迁移、A/B测试等有计划的操作，其本质是一次“全局Checkpoint”，但更强调操作灵活性和状态的可移植性。
___
### 9. Flink的Checkpoint流程
Flink的Checkpoint流程由JobManager周期性地触发，其核心是基于Barrier（屏障）的一致性快照机制：JobManager向Source算子注入Checkpoint Barrier，该屏障随数据流向下游广播；每个算子接收到Barrier后立即异步快照当前状态并持久化到外部存储（如HDFS），同时将Barrier传递至下游；当所有算子（包括Sink）完成快照后，JobManager确认该Checkpoint完成，从而形成一个全局一致的分布式快照点用于故障恢复
___
### 10. Flink Checkpoint的作用 

___
### 11. Flink中Checkpoint超时原因
Flink中Checkpoint超时的根本原因在于Checkpoint Barrier在数据流中传播受阻，无法在规定时间内完成全局状态快照，这通常由资源不足（CPU/内存瓶颈）、反压（数据处理速度跟不上接收速度，导致Barrier排队）、外部系统交互慢（如Sink到外部API耗时过长）或状态过大（生成或持久化快照耗时）等因素引起。
___
### 12. Flink的ExactlyOnce语义怎么保证?
Flink通过分布式快照（Checkpoint）机制和两阶段提交协议（2PC） 共同保证端到端的Exactly-Once语义：Checkpoint定期对算子的状态和流处理位置进行全局一致性快照，确保故障恢复后状态与数据源重放位置一致；而对于Sink连接的外部系统，Flink通过2PC预提交（Pre-commit）和提交（Commit）阶段协调，确保数据要么原子性写入外部系统，要么在故障时回滚，从而避免重复输出。
___
### 13. Flink的端到端ExactlyOnce
Flink的端到端Exactly-Once语义通过分布式快照（Checkpoint） 和两阶段提交协议（2PC） 协同实现：Checkpoint机制周期性地对数据源读取位置、算子状态及Sink输出状态进行全局一致性快照，确保故障恢复后状态与处理进度一致；同时Sink连接器需支持2PC（如Kafka事务），在Checkpoint完成前数据处于"预提交"状态，仅当所有组件确认快照成功后才会原子性提交数据到外部系统，从而保证数据从源到目的地的精确一次处理。
___
### 14. Flink的水印(Watermark)，有哪几种?
Flink的水印（Watermark）本质上是流中插入的一种特殊时间戳，用于推进事件时间并处理乱序，主要分为周期性水印（Periodic Watermark）（根据时间或数据量间隔定期生成）和标点性水印（Punctuated Watermark）（基于特定事件触发生成）两种；前者通过assignPeriodicWatermarks定义，适用于大多数连续处理的场景，后者通过assignPunctuatedWatermarks定义，常用于依赖特殊标记事件（如数据边界）触发水印更新的场景。
___
### 15. Flink的时间语义
Flink提供三种时间语义：事件时间（Event Time） 以数据自带的时间戳为准，结合水位线处理乱序，保证结果准确性；处理时间（Processing Time） 以系统处理时刻为准，延迟最低但忽略乱序；摄入时间（Ingestion Time） 以数据进入Flink的时间为准，平衡延迟和乱序处理能力，用户可根据业务需求在环境中通过setStreamTimeCharacteristic()灵活选择时间语义。
___
### 16. Flink相比于其它流式处理框架的优点?
___
### 17. Flink和Spark的区别?什么情况下使用Flink?有什么优点?
___
### 18. Flink backPressure反压机制，指标监控你是怎么做的?
___
19. Flink如何保证一致性?
___
20. Flink支持JobMaster的HA啊?原理是怎么样的?
___
21. 如何确定Flink任务的合理并行度?
___
22. Flink任务如何实现端到端一致?
___
23. Flink如何处理背(反)压?
___
24. Flink解决数据延迟的问题
___
25. Flink消费kafka分区的数据时flink件务并行度之间的关系
___
26. 使用flink-client消费kafka数据还是使用flink-connector消费
___
### 27. 如何动态修改Flink的配置，前提是Flink不能重启
Flink支持通过其REST API或命令行工具（CLI）动态修改部分运行参数（如并行度、Checkpoint间隔），而无需重启作业，这依赖于底层原地重启或状态复用机制；但对于需要改变作业拓扑图（如SQL逻辑）的修改，则通常仍需通过Savepoint重启或依赖外部配置中心（如Nacos）结合广播流实现动态更新。
___
28. Flink流批一体解释一下
___
29. 说一下Flink的check和barrier
___
### 30. 说一下Flink状态机制
Flink的状态（State）机制是其实现有状态流处理的核心，分为算子状态（Operator State）（与算子并行度绑定，如Kafka偏移量）和键控状态（Keyed State）（与Key绑定，仅限KeyedStream使用，如累加器）；状态由状态后端（State Backend） 统一管理存储（内存/RocksDB）并通过检查点（Checkpoint） 持久化到外部存储，确保故障恢复时状态一致性，支撑了窗口聚合、模式检测等复杂流处理场景。
___
31. Flink广播流
___
32. Flink实时topN
___
33. 在实习中一般都怎么用Flink
___
34. Savepoint知道是什么吗
___
35. 为什么用Flink不用别的微批考虑过吗
___
### 36. 解释一下啥叫背压
背压（Backpressure） 是分布式流处理系统中一种重要的流量控制机制：当下游组件的处理速度跟不上上游的数据发送速度时，系统会通过反向压力迫使上游降低生产速率，而不是丢弃数据或导致内存溢出；在Flink中，背压会通过任务间网络栈向上游传递，最终可能暂缓数据源的数据读取，从而形成一种自然的反馈调节，保障系统稳定运行。
___
37. Flink分布式快照
___
38. Flink SQL解析过程
___
39. Flink on YARN模式
___
40. Flink如何保证数据不丢失
___
