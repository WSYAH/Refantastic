# Spark基础
### 0.spark的一些基本概念
|       |                                                                   | 
|-------|-------------------------------------------------------------------|
| RDD   | 弹性分布式数据集，是 Spark 中最基本的数据抽象，代表一个不可变、可分区的分布式数据集合，具备内置的容错机制          |
| DAG   | 有向无环图，Driver会将Spark任务转换成一个DAG，其中顶点是RDD，边是转换                       |
| Job   | 一个Action算子，（如collect(), saveAsFile())会触发一个Job，一个Job对应一个DAG        |
| Stage | Stage是Job的调度单位，DAGScheduler会根据RDD之间的宽依赖（Shuffle依赖）将DAG划分成多个Stage。 |
| Task  | Task是Stage的执行单位，代表在一个数据分区上进行的计算。一个Stage会启动多个Task在各个Executor上并行执行。 |

### 1. Spark的任务执行流程

| 流程                     | 说明/关键操作                                                                                              | 
|------------------------|------------------------------------------------------------------------------------------------------|
| 应用启动:Driver初始化与环境准备    | Spark应用的起点是创建 SparkContext（每个应用的唯一入口），它负责与集群管理器（YARN、Standalone）通信，完成下面关键操作                          |
|                        | 向集群管理器注册应用，申请 Executor 资源（指定 CPU、内存大小等）                                                              |
|                        | 解析用户代码(比如说 RDD 转换/行动操作，为后续执行计划构建做准备                                                                  |
|                        | 维护应用的全局状态（如任务进度、资源使用情况）。                                                                             |
| 构建DAG:逻辑执行计划生成         | 用户通过RDD的转换操作（如map、filter、join）定义数据处理逻辑，这些操作会被Spark记录为RDD依赖链（如RDD A→RDD B→RDD C）。随后，Spark将依赖链转换为DAG   |
|                        | 节点： 达标一个 RDD（或者 RDD 的分区）；                                                                            |
|                        | 边：代表RDD间的依赖关系（分为窄依赖（如map,父RDD分区与子 RDD 分区一对一）） 和宽依赖（如groupByKey，父RDD分区与子RDD分区多对多））。                   |
|                        | DAG是 Spark 优化的基础，它能识别可并行执行的任务，并避免不必要的计算(如缓存中间结果)。                                                    |
| Stage划分：物理执行计划拆分       | DAG会被DAGScheduler根据宽依赖拆分为多个Stage（阶段），拆分规则如下                                                          |
|                        | 窄依赖：属于同一Stage，可并行执行（如RDD A→RDD B→RDD C的窄依赖链为一个Stage）；                                                |
|                        | 宽依赖：作为Stage边界（如RDD B→RDD C的宽依赖，RDD B的处理为一个Stage，RDD C的处理为下一个Stage）。                                  |
|                        | 每个Stage包含多个Task（任务），Task是最小执行单元，数量等于对应RDD的分区数（如RDD有10个分区，则该Stage有10个Task）。                           |
| 任务调度：Task分配与执行         | TaskScheduler将每个Stage的Task打包为TaskSet（任务集），并根据数据本地性（Data Locality）策略分配给Executor;                      |
|                        | 数据本地性优先：尽量将Task分配给存储有其处理数据的节点（如HDFS block所在节点），减少网络传输；                                               |
|                        | 资源匹配：根据Executor的资源（CPU、内存）情况，分配合适数量的Task（如每个Executor分配2个CPU核心，则每个核心可同时运行1个Task）；                     |
|                        | 失败重试：若Task执行失败（如Executor崩溃），TaskScheduler会重新分配任务（默认重试4次）。                                            |
|                        | Executor接收到Task后，启动线程执行Task，处理对应分区的数据（如执行map函数的逻辑）。                                                  |
| 数据Shuffle：跨Stage数据重新分布 | 当Stage间存在宽依赖（如groupByKey、reduceByKey）时，需要触发Shuffle操作，目的是将数据按照新的分区规则（如key的哈希值）重新分布到下游Stage的Executor中。 |
|                        | Map端：将数据按照分区规则排序、分区，并写入本地磁盘（生成多个临时文件）；                                                               |
|                        | Reduce端：从Map端拉取对应分区的数据，合并、排序后进行处理（如reduceByKey的聚合操作）。                                                |
|                        | Shuffle是Spark的性能瓶颈之一，涉及大量网络传输和磁盘I/O，因此需通过调参（如spark.shuffle.spill.compress=true开启压缩）优化。               |
| 结果收集与处理：最终结果返回         |                                                                                                      |
|                        | 行动操作触发：当遇到行动操作（如collect、count、saveAsTextFile）时，下游Stage的Task开始执行，处理后的结果会返回给Driver；                    |
|                        | 结果聚合：Driver收集所有Task的结果（如collect将所有分区数据汇总到Driver内存），并根据操作类型处理（如count返回总数，saveAsTextFile将结果写入HDFS）；    |
|                        | 结果输出：最终结果可通过控制台打印、存储到外部系统（如Hive、MySQL）或传递给后续应用。                                                      |
| 应用结束：资源释放与清理           | 当所有Task执行完成且结果处理完毕后                                                                                  |
|                        | 通知集群管理器释放Executor资源（停止Executor进程，释放CPU、内存）；                                                          |
|                        | 关闭SparkContext，终止与应用相关的所有连接（如与集群管理器的通信、与Executor的心跳）。                                                |
|                        | 此时，应用生命周期结束，集群资源可被其他应用复用。                                                                            |
以上流程体现了Spark的并行计算（Task分布在多个Executor上）、容错机制（RDD lineage血统恢复数据）、资源优化（数据本地性、Stage拆分）等核心优势，使其能高效处理大规模数据。
___
### 2. Spark的运行流程
这个跟任务执行流程没啥区别吧。

___
### 3. Spark的作业运行流程是怎么样的?
重复了喂！

___
### 4. Spark的特点
① 速度快；
- 首先是基于内存计算，中间计算结果尽可能的保存在 RAM 中，并不是想 Hadoop MapReduce那样频繁读写磁盘，从而大幅度减少 I/O开销，提高计算速度。
支持 RDD 的缓存(cache()/persist())，对于迭代计算（比如机器学习、图计算）的交互式查询尤其高效。
- DAG 执行引擎，Spark使用 DAG 对用户的计算逻辑进行优化，将多个操作合并成一个执行计划，避免不必要的 Shuffle 和重复计算，提高执行效率。
通过 DAGScheduler和 TaskScheduler 实现高效的调度和任务切分。  
- 优秀的 Shuffle 与任务调度机制
Spark 对 Shuffle 过程进行了优化，支持多种压缩和序列化方式，减少网络与磁盘开销。？？支持推测执行，对执行慢的 Task 会启动备份任务，提高整体作业完成速度。？？

② 通用性强  
支持读取和写入 HDFS、Hive、Kafka、HBase、MySQL、JSON、Parquet、ORC 等多种数据源和格式，具备强大的数据集成能力。  

③ 容易使用  
提供了更丰富的更高级易用的编程模型，比如RDD，支持 map、filter、reduce、join等函数式操作；DataFrame/DataSet：类似于 SQL 表或者 pandas DataFrame，
支持结构化处理。还可以直接使用 SQL 进行查询。Java、Python、Scala 都有 API。  

④ 容错性强  
⑤ 可扩展性高，支持大规模集群，跟多种集群管理器兼容，Standalone（spark自己的）、YARN（常用的Hadoop的）。  
⑥ 支持流批一体，可以支持流式处理也支持批处理、但是在我们组，一般将流式任务处理交给 flink。  

___
### 5. Spark源码中的任务调度
Spark 的任务调度是其分布式计算的核心组件之一，负责将用户提交的作业（job）拆解为可执行的子任务（Task），并通过资源管理器将任务分配到集群中的 Executor
上面执行，其调度机制主要分为 Stage 级的调度（DAGScheduler 负责）和 Task 级别的调度(由 TaskScheduler 负责)两部分，两者协同工作以实现高效的并行计算。

- Stage级调度（DAGScheduler）
是 Spark 任务调度的高层组件，主要负责将用户提交的作业（Job）转换为 Stage DAG（有向无环图），并按照宽依赖划分为Stage，最终将每个 Stage的任务集（TaskSet）
提交给 TaskScheduler 执行。  
> Job 和 Stage 的划分
> Job触发条件： Spark 采用惰性计算模式，只有当遇到 Action 算子（比如 collect、count、saveAsTextFile）时，才会触发 Job 的提交。此时，SparkContext
> 会将 Job 交给 DAGScheduler 处理。 
> 
> Stage划分逻辑： DAGScheduler 会根据 RDD 的依赖关系（dependencies）构建 DAG。具体来说，它会从 Action 触发的最终 RDD 开始，反向回溯其依赖项：  
> 如果遇到了窄依赖，比如 map、filter，则将当然 RDD 与父RDD 合并到同一个 Stage（因为窄依赖可以在同一个节点上流水线执行，无需 shuffle）；  
> 如果遇到了宽依赖，则以该宽依赖为边界划分 Stage（因为宽依赖需要 Shuffle，必须等待上有 Stage 完成才能执行）。  
> 
>> 举个例子，对于WordCount作业，（textFile → flatMap → map → reduceByKey → saveAsTextFile），DAGScheduler会划分两个Stage   
> ShuffleMapStage（处理textFile → flatMap → map）：为下游Stage准备Shuffle数据；   
> ResultStage（处理reduceByKey → saveAsTextFile）：由Action算子触发，生成最终结果。  
> 
> TaskSet 的生成与提交
> Task生成：每个Stage会生成一组Task（ShuffleMapTask或ResultTask），数量等于对应RDD的分区数（partitions.size）。
>> ShuffleMapTask：负责将数据写入本地磁盘（Shuffle输出），供下游Stage读取；  
>ResultTask：负责处理最终数据（如saveAsTextFile），生成Action结果。
> 
> TaskSet封装：DAGScheduler会将同一Stage的所有Task封装为TaskSet（包含Task的二进制代码、分区信息、数据本地性等），并通过submitStage方法提交给TaskScheduler。

- Task级调度（TaskScheduler）
TaskScheduler是Spark任务调度的底层组件，主要负责将DAGScheduler提交的TaskSet分配到Executor上执行，并监控任务的运行状态（如成功、失败、重试）。
> TaskSetManager的作用  
> TaskScheduler会将每个TaskSet封装为TaskSetManager（TaskScheduler的内部类），用于管理TaskSet的生命周期：
>> 任务分配：TaskSetManager会根据Task的数据本地性（preferredLocations，如RDD分区所在的Executor或节点）和调度策略（如FIFO、Fair），将Task分配给SchedulerBackend（资源调度接口）;    
>  状态监控：TaskSetManager会监听Task的执行状态（通过SchedulerBackend接收Executor的心跳），若Task失败，会根据重试策略（spark.task.maxFailures，默认4次）重新提交任务；
> 若重试次数超过阈值，则标记Stage为失败，触发DAGScheduler重新提交Stage。   
> 
> 调度策略  
> TaskScheduler支持两种主要的调度策略，通过spark.scheduler.mode参数配置：  
>> FIFO（先进先出）：默认策略，先提交的Job优先分配资源，同一Job内的Task按Stage顺序执行。适用于批处理作业，保证作业的执行顺序;   
>  Fair（公平调度）：通过FairScheduler实现，为每个Job分配公平的资源份额（如spark.scheduler.pool配置资源池），避免长作业占用过多资源。适用于多租户环境（如共享集群），保证每个Job都能获得资源。
> 
> 数据本地性优化  
> TaskScheduler会优先将Task调度到存储了其处理数据的节点（如RDD分区所在的Executor），以减少网络传输开销。数据本地性分为以下级别（优先级从高到低）：
>> PROCESS_LOCAL：Task与数据在同一Executor上；  
> NODE_LOCAL：Task与数据在同一节点（不同Executor）；   
> RACK_LOCAL：Task与数据在同一机架（不同节点）；  
> ANY：Task与数据在不同机架（任意节点）。  
> 

- 两种调度的协同流程
> DAGScheduler与TaskScheduler的协同流程可概括为：  
Job提交：Action算子触发Job，SparkContext调用DAGScheduler.submitJob；  
Stage划分：DAGScheduler从最终RDD反向回溯，划分Stage并生成TaskSet；  
Task提交：DAGScheduler将TaskSet提交给TaskScheduler；  
资源申请：TaskScheduler通过SchedulerBackend向资源管理器（如YARN）申请Executor资源；  
任务分配：SchedulerBackend返回可用资源（WorkerOffer），TaskScheduler将Task分配给Executor；  
任务执行：Executor执行Task，完成后将结果返回给Driver；  
状态监控：TaskScheduler监控Task状态，失败时重试，Stage完成后通知DAGScheduler。  

- 关键组件交互
> DAGScheduler与TaskScheduler：DAGScheduler负责Stage级调度，将TaskSet交给TaskScheduler；TaskScheduler负责Task级调度，将Task分配到Executor。  
TaskScheduler与SchedulerBackend：SchedulerBackend是TaskScheduler与资源管理器的桥梁，负责申请资源和接收Executor注册信息。  
Executor与Driver：Executor执行Task，定期向Driver发送心跳（汇报资源状态和任务进度）；Driver通过心跳监控Executor状态，更新任务进度。  

___
### 6. Spark作业调度
这个跟上面的没什么区别，依然是分为，作业提交，阶段划分，任务调度，任务执行。

___
### 7. Spark的架构
Spark是一个经典的主从式的分布式架构，主要通过内存计算和高效的调度机制来提升大数据处理速度。Spark的核心组件之间的相互协调见下图：  
![spark架构](../../images/spark_infra.png)   
Spark还提供了一系列有用的库，构建在Spark Core之上。  
Spark SQL，处理结构化数据，支持SQL语句或者DataFrame\Dataset API 查询。  
Spark Streaming, 用于处理实时数据流，采用微批次（micro-batch）架构。  
MLlib， 机器学习库，提供了常见的机器学习算法和流水线（pipeline）构建工具。  
Graphx，图计算框架，用于处理图结构数据和执行图算法。 

___
### 8. Spark的使用场景
复杂的结构批处理，RFC存在两个场景，就是批特征和流特征，批处理就使用Spark。  
大规模的 ETL 作业，将原始日志数据清洗、转换后加载到数据仓库（如 Hive, AWS Redshift）中。  
分析用户行为日志，生成报表（如每日活跃用户、用户留存率）。  
机器学习同样适用于Spark，提供了可扩展机器学习库，适合大规模数据集上面进行模型训练。  

___
### 9. Spark on standalone模型、YARN架构模型(画架构图) 
差别还挺多的，写在这里感觉不太写的下，回头将下面的参考回答精简一下贴在这里@TODO
https://developer.aliyun.com/article/1578917  
https://blog.csdn.net/lyq7269/article/details/107847319  

![spark on standalone](../../images/spark on standalone.png)
___
### 10. Spark的yarn-cluster涉及的参数有哪些?  
参考： https://blog.csdn.net/penriver/article/details/116143661  
但是内容太多太杂太琐碎，挑几个常用的吧。
从 spark submit出发，一般需要配置的参数有： --deploy-mode 应该指定为cluster  
一定要指定 --driver-memory 和 driver-cores 和 Executor-memory 和 executor-cores， 
反正举个例子： 
```
spark-submit  
 --deploy-mode cluster 
 --driver-memory 4g  
 --executor-cores 2  
 --executor-memory 4g  
 --num-executors 1  
 --conf spark.dynamicAllocation.enabled=false  
 --conf spark.yarn.dist.archives=s3://rfc-test-1/jars/rfc_py39.tar.gz#rfc_py39  
 --conf spark.pyspark.python=./rfc_py39/bin/python3   
 --conf spark.speculation=true   
 --conf spark.speculation.quantile=0.9   
 --jars s3://rfc-test-1/jars/uff_main_spark33_aws.fat.jar,/usr/share/aws/iceberg/lib/iceberg-spark3-runtime.jar  s3://rfc-test-1/jars/oversea_mvp_pyspark_job.py env=dev ir_bucket=rfc-test-1 ir_file_key=jars/oversea_batch_mvp_feature.pbtxt current_date=20250425 deploy_env=aws
```
对于生产环境，强烈建议启用动态资源分配(spark.dynamicAllocation.enabled=true)。  
这允许 Spark 根据工作负载自动调整 Executor 的数量，从而提高集群资源利用率。
启用后，通常只需设置 minExecutors和 maxExecutors，而不再需要指定固定的 --num-executors.
___
### 11. Spark提交job的流程
第一步是任务提交，通过spark-submit提交应用程序到集群，这一步申请资源，初始化SparkContext作为程序的唯一入口。
第二步就是Driver根据提交的任务划分Stage，这一步涉及到DAG构造和Stage划分，sparkcontext 根据应用程序当中的Transformers操作和行动操作Action，构建出
RDD及其之间的依赖关系，构建出来一个DAG。然后根据RDD之间的宽依赖划分Stage。  
第三步是TaskScheduler 进行调度与执行，接受上一步DAGScheduler给的TaskSet（Stage带有一组Task）然后负责将这些TaskSet分发到不同的Executor上面
执行。  
第四步就是结果返回与资源清理了。
___
### 12. Spark的阶段划分
Spark的阶段（Stage）划分是其调度系统的核心，它决定了任务如何被组织和并行执行。   
Spark根据RDD之间的依赖关系来划分Stage。主要分为两种：
>窄依赖:父RDD的每一个分区最多被一个子RDD的分区使用。窄依赖允许数据进行pipeline优化，多个操作可以在同一个任务中连续执行，无需数据移动和等待，
因此，窄依赖的操作会被划分到同一个Stage中去。  
宽依赖（shuffle Dependency）: 父RDD的分区可能会被多个子RDD的分区使用，比如操作groupByKey，reduceByKey. 宽依赖要求所有父分区数据准备完成后，
必须经过Shuffle（数据重新洗牌、分区，网络传输）才能进行下一步计算。宽依赖是Stage划分的边界，遇到宽依赖一定会划分Stage。

STAGE的划分是由DAGScheduler在Driver端进行的，过程如下: 
>当遇到一个行动Action（比如collect()，count()）时，Spark会触发作业Job，DAGScheduler会从Action操作对应的最终RDD开始，按照DAG反向回溯，
自底向上遍历RDD的依赖链。  
遇到宽依赖则切断，在反向遍历的过程中，每当遇到宽依赖，则进行切断，宽依赖之前的RDD操作被划归为当前Stage，宽依赖之后的操作将开始一个新的Stage。  
遇到窄依赖则合并: 在反向遍历的过程中，如果遇到的是窄依赖，则将当前RDD加入到当前Stage中，一连串的窄依赖可以划分到一个Stage中，形成一个流水线化计算的计算任务（Pipeline 。  
递归进行: 这个过程会一直递归向上进行，知道遍历完所有的依赖关系。 

Stage的类型分为ShuffleMapStage和ResultStage: 
>ShuffleMapStage是一个中间阶段，该阶段内的任务ShuffleMapTask会计算数据，并根据分区规则将数据写入内存或者磁盘，为其下游的Stage准备数据，
一个Job可能会有多个ShuffleMapStage。  
ResultStage是最终阶段，该阶段的任务会执行最终的计算任务，比如聚合、输出或返回结果到Driver，一个Job只有一个ResultStage。

Stage划分完后，每个Stage会被进一步分解为多个Task，这些Task才是真正的在集群节点上执行的计算单元。
>一个分区对应一个Task，一个Stage的Task数量应该是由Stage最后一个RDD的分区数（Partitions）决定的。  
Task的并行执行，这些Task封装了相同的计算逻辑，但是处理不同的数据分区，它们会被TaskScheduler分配给集群中的各个Executor并行执行。

为什么要划分Stage？
>有两个目的。  
一是为了实现流水线计算，将窄依赖合并到一个Stage中，可以让多个操作在同一个Task内连续执行，避免了不必要的中间结果落盘，大大提升了计算效率。   
二是为了明确Shuffle边界，宽依赖必须等待所有的父分区计算完成才能开始Shuffle，Stage划分明确了这些同步点，为调度器提供了明确的依赖关系，以便按照
顺序调度Stage，父Stage必须先于子Stage执行。  
___
### 13. Spark处理数据的具体流程说下
Spark 处理数据可以看做一个高效的、分布式的流水线，核心思想是惰性求值和内存计算。  
 &emsp;&emsp;第一步是初始化和数据源加载：先创建一个SparkSession，2.0之后它就是与应用程序交互的唯一入口，提供了链接集群、配置参数、读取数据的能力。  
创建SparkSession后，便可以通过它从多种数据源（HDFS、本地文件系统、S3、Kafka、JDBC数据库）加载数据，生成最初的数据抽象，如RDD、DataFrame等。 
Spark支持多种数据格式，parquet、csv、Json等。  
 &emsp;&emsp;第二步就是数据转换和惰性求值： 数据加载后，可以定义一系列的Transforms转换操作，例如map、join等，对数据进行处理和加工。惰性求值是Spark实现优化的
核心机制，在调用Action之前，所有的Transform都只是被记录下来，构建一个逻辑执行计划DAG，但是并不会立刻执行任何计算，这使得Spark可以对整体操作进行
审视和优化。  
 &emsp;&emsp;第三步就是物理执行和作业调度： 当调用一个Action如count()、show()时候，真正的计算过程便被触发。这个过程首先会进行Stage划分、然后每个Stage会被
进一步转化成一系列的Task，这些TaskSet会被TaskScheduler分配给各个Executor进行实际执行；在Executor接收到Task后，便开始执行具体的计算逻辑（比如
定义的filter、map函数），将数据加载至内存进行处理，并将结果保存在内存中、磁盘上或者进行shuffle操作以供后续的Stage使用，Executor本质上是线程池
Task在其内部以多线程的形式运行。  
 &emsp;&emsp;第四步就是结果收集与资源释放：最终Stage的Task执行结果会被汇集到Driver程序。根据不同的Action操作，结果可能会被直接返回（如collect()），也可能
被写入到外部存储系统（saveAsTextFlies()）。当整个Spark程序运行完毕后，SparkSession和SparkContext会被关闭，并通知集群管理器释放所有为本次
申请的计算资源（比如Executors）。
___
### 14. Spark join的分类
Inner Join最为常用的就是，只返回满足Join条件的数据，Join默认都是Inner Join。  
Cross Join，就是笛卡尔积。  
left outer Join， 就是在Inner Join的基础上，将左表未匹配的数据，保留原表，右表项置空null。  
right outer Join同理。  
full outer Join，更是同理，左右不匹配的都保持原表并在各自缺失项置空null。   
left semi join只返回匹配右表的数据，并且不显示右表项，这样可能不理解，但是如果我说这就是in/exist操作呢？  
left anti join恰恰与semi相反，只返回不匹配右表的数据，可以理解为not in/exist。
___
### 15. Spark map join的实现原理
Map Join又称为广播连接或者广播哈希连接（BHJ），是Spark中用于优化表连接的一种关键技术。核心思想是将小表广播到集群所有工作节点上，从而避免
大规模的shuffle操作，显著提升性能。  
这种连接方式特别适用于星型模型或雪花模型中常见的事实表与维度表连接场景，其中事实表通常包含大量的业务数据（大表），而维度表则包含相对较少的
描述信息（小表）。与传统的shuffle Join需要将数据按照Key重新分区不同，Map Join通过在Map端完成所有连接操作，完全避免了Shuffle过程，这对于
减少网络传播和数据倾斜问题有重要意义。  
Map Join的适用性取决于小表的大小。通常，当小表的数据量小于Spark配置的广播阈值（通常为10MB）时候，Spark会自动选择使用Map Join策略。

___
### 16. 介绍下Spark Shuffle及其优缺点
https://zhuanlan.zhihu.com/p/67061627  
https://cloud.tencent.com/developer/article/1913486?policyId=1004  
Spark Shuffle是Spark分布式计算框架中用于处理数据在Map和Reduce阶段之间交换和重组的关键机制。它描述了数据从map task输出到reduce task输入
的整个过程，连接着Map和Reduce两个阶段，是这两个阶段之间数据交换的桥梁。
Shuffle过程通常分为两个阶段：Map阶段的数据准备（Shuffle Write）和Reduce阶段的数据拷贝处理（Shuffle Read） 。
在Spark中，Shuffle是一个必要但昂贵的操作，因为它涉及到大量的磁盘I/O、网络传输和数据序列化/反序列化操作，这些操作会消耗大量的计算和网络资源.  

Spark Shuffle的执行流程可以分为三个主要阶段：Map阶段处理、中间结果存储和Reduce阶段处理。整体上，这是一个复杂的"数据长征"过程，
数据从Map任务产生，经过分区、排序和聚合，最终被Reduce任务拉取和处理.  
      &emsp;&emsp;Map阶段处理：每个Map任务执行用户逻辑（如map、filter）后，输出<Key, Value>键值对。这些数据首先需要按Key分区，确定每个Key属于哪个
Reduce任务。分区规则由Partitioner决定，默认是HashPartitioner（key.hashCode % numPartitions）。数据会被缓存在内存中的
ShuffleBuffer（内存缓冲区），当缓冲区使用率达到阈值时，会溢写到磁盘，生成临时文件（Spill File）。 
      &emsp;&emsp;中间结果存储：Map任务结束后，会将所有溢写文件合并为一个最终的Shuffle文件和一个索引文件。索引文件记录每个分区在Shuffle文件中的起始位置
和长度。这些文件存储在Map节点的本地磁盘，由BlockManager管理。Map任务完成后，会将Shuffle文件的元信息（如文件路径、分区大小）通过
MapOutputTracker注册到Drive。
      &emsp;&emsp;Reduce阶段处理：Reduce任务启动后，首先通过MapOutputTracker向Driver查询需要的分区数据分布信息。然后根据返回的元信息，通过
BlockManager向各个Map节点发起拉取请求。拉取的数据会缓存在内存中，若内存不足则溢写到磁盘。最后，Reduce任务将来自不同Map节点的数据合并为
一个有序的数据集，并进行必要的聚合操作。  

**如果可以，还可以了解一下shuffle write与shuffle read操作**
___
### 17. 什么情况下会产生Spark Shuffle?  
当Spark需要对数据进行跨分区的重新组织，例如为了聚合连接的时候，就会发生shuffle，通常是因为操作要求需要相同的键的所有数据汇集到同一个分区中
进行处理。  
如果数据已预先分区：例如，两个要进行 join的 RDD 已经使用相同的分区器（Partitioner）和分区数进行了分区，那么 Spark 可能无需再次 Shuffle
___
### 18. 为什么要Spark Shuffle?
**https://jishuzhan.net/article/1901993468061364226**   
shuffle通常发生在需要重新分组或者聚合的操作中，比如groupbyKey，reduceByKey
Join，repartition等操作中。  
一般当数据处理要求将相同key的数据汇集到同一个分区（或者同一个计算节点）进行计算的时候，就必须进行shuffle，因为在分布式系统中，相同 key 的
数据最初可能散落在不同的机器或分区上，Shuffle 就是那个负责“搬运”和“重组”数据的关键过程。  
___
### 19. Spark为什么快?
内存计算，中间数据有限内存存储，减少磁盘IO。  
DAG执行引擎， 有向无环图划分Stage，优化执行计划，减少不必要的shuffle。   
高效shuffle机制， 提供多种shuffle策略，可选择是否排序聚合，减少计算量。   
线程级别任务执行， Task线程方式在Executor的JVM中执行，复用JVM，减少启动开销。    
更优的序列化，支持Kryo等高效序列化库，减少数据序列化开销和时间。   
___
### 20. Spark为什么适合迭代处理? 
Spark适合迭代处理，主要是内存计算、弹性分布式数据集和基于DAG的执行引擎的特性。  
内存结算，将中间数据存放在内存，迭代计算不用频繁读取磁盘。  
**通过RDD的血缘关系实现**，仅仅重新计算丢失的分区，而相对的，MapReduce需要重新计算整个任务或者阶段。  
基于DAG的执行引擎，可以将多个操作流水线优化，相对的，MapReduce两阶段间依赖磁盘shuffle。
___
### 21. Spark数据倾斜问题，如何定位，解决方案。 
数据倾斜问题可能会导致某个Task特别慢或者导致OOM，可以通过在Spark UI里面定位stage和Task耗时以及数据量来定位问题：如果个别的Task的耗时远高于其他的Task，通常可以认为是数据倾斜，数据量也是如此，查看Shuffle Read Size/Records，如果某个别Task的持续时间远高于其他的，基本可以确定了。    
然后进行代码分析，识别Shuffle算子与可能倾斜的Key：代码中使用了容易引起Shuffle的算子，比如说GroupByKey、reduceByKey、Join等。同时在Executor日志中，如果发现了OOM错误或者FetchFailedException等异常，并结合UI看到某个Task处理数据量巨大，可以确定了。    
进一步判断倾斜key的情况：如果是热点key，那么可以通过采样统计key的分布：   
```
// 示例：采样并统计Key出现的次数，找出热点Key
val sampledPairs = yourRdd.sample(false, 0.1) // 对RDD采样10%
val sampledWordCounts = sampledPairs.countByKey()
sampledWordCounts.foreach(println(_))
```  
如果是少数几个热点key，可以过滤掉这些key，或者单独处理。  
如果是大量不同的key导致倾斜，则可以提高并行度或者通过两阶段聚合解决。  
如果是Join操作中的大表关联小表，可以广播小表，Map Join，但是广播表不能太大，不然广播的时候易造成Driver和Executor内存溢出。  
如果Join操作中两个表都是大表且有热点key的话，可以拆分Join或者通过随机扩容的方式。   
可以参考：https://mp.weixin.qq.com/s?__biz=Mzk0MTI0OTI1NA==&mid=2247507912&idx=1&sn=367f3e3753130c683a8cc2cd84c4e6fd&chksm=c37ea9ec4d76d154bf2d4e8a87884ecb87b22c45dd3fa9b455df7747b2065eda1ada362706e7#rd
___
### 22. Spark的stage如何划分?在源码中是怎么判断属于Shuffle Map Stage或Result Stage的?
是靠RDD之间的依赖关系划分的。  
如下所示,从最后的Action操作反向追溯，进行Stage划分：
Stage1 (ShuffleMapStage) -> (Shuffle) -> Stage2 (ShuffleMapStage) -> (Shuffle) -> Stage3 (ResultStage)。
```
sc.textFile("hdfs://...") // RDD0
  .flatMap(_.split(" "))  // RDD1 (窄依赖)
  .map(word => (word, 1)) // RDD2 (窄依赖)
  .reduceByKey(_ + _)    // RDD3 (宽依赖！)
  .filter(_._2 > 10)     // RDD4 (窄依赖)
  .sortByKey()           // RDD5 (宽依赖！)
  .collect()             // Action
```
参考： https://blog.csdn.net/m0_73889530/article/details/148657045  
Spark UI: https://www.cnblogs.com/bigdata1024/p/12194298.html
或者可以自己启动一个pyspark程序，会提供web界面的。
___
### 23. Spark join在什么情况下会变成窄依赖?
是否会变成窄依赖，关键在于参与join的两个RDD是否已经使用了相同的分区器Partition而进行了预分区，并且分区数相同，这种情况下，因为相同key的数据
已经位于一个节点，因此无需Shuffle。  
可以使用PartitionBy方法对RDD进行预处理：  
```
val rddA = ... // 第一个RDD
val rddB = ... // 第二个RDD

// 使用相同的HashPartitioner和分区数对两个RDD进行预分区
val partitioner = new HashPartitioner(8)
val rddAPartitioned = rddA.partitionBy(partitioner)
val rddBPartitioned = rddB.partitionBy(partitioner)

// 此时进行join操作，Spark会识别到分区状态，避免Shuffle，形成窄依赖
val resultRDD = rddAPartitioned.join(rddBPartitioned)
```
___
### 24. Spark的内存模型?
https://blog.csdn.net/wintershii/article/details/104169123
___
### 25. Spark分哪几个部分(模块)?分别有什么作用(做什么，自己用过哪些，做过什么)? 
Spark Core、Spark SQL、Spark Streaming、MLib、GraphX。  
虽然没有用过Streaming，可以用来处理来自kafka的是使用户点击数据流，进行实时统计和简单过滤。    
https://mp.weixin.qq.com/s?__biz=Mzg2Mzc0Mjc3Nw==&mid=2247492143&idx=1&sn=45c8da33d0e5698d8aca2ecc550a45ac&chksm=ce715c79f906d56ff605146a5f839d7cc49acd46adebdbdb3eb7fe180e787d3871f2debec0c0#rd
___
### 26. RDD的宽依赖和窄依赖，举例一些算子
窄依赖 父RDD的一个分区只对应子RDD的一个分区，没有Shuffle，高效，支持流水线执行，容错成本低
map, filter, flatMap, union, sample, mapPartitions   
宽依赖 父RDD的一个分区对应子RDD的多个分区 有Shuffle，开销大.
groupByKey, reduceByKey, join(非协同划分), repartition, distinct, coGroup, sortByKey

___
### 27. Spark SQL的GroupBy会造成窄依赖吗?
不是，是宽依赖，需要根据指定的键进行重新Shuffle。  
___
### 28. GroupBy是行动算子吗
不是，是一个Transform，不会立刻进行计算，行动算子会引发计算。  
___
### 29. Spark的宽依赖和窄依赖，为什么要这么划分?
方便Stage划分，任务可以串联在一起，形成流水线，无需将中间结果落盘。  
窄依赖的恢复：高效且简单。由于子分区只依赖于父RDD的少量分区（甚至一个），Spark只需要重新计算父RDD中那些丢失的分区即可。无需回溯整个血缘关系。
宽依赖的恢复：昂贵且复杂。由于子分区依赖于父RDD的所有分区（因为Shuffle需要所有数据来重新计算Key的分布），单个节点的失败可能导致整个阶段的所有分区都需要重新计算。这被称为血统链过长问题。  
流水线优化：窄依赖允许Spark将多个操作（如多个map)合并成一个Task，在一个线程内连续执行，避免了不必要的中间数据物化，极大提升了性能。  
Shuffle优化：宽依赖就是Shuffle。Shuffle是Spark作业中最昂贵、最耗时的操作，因为它涉及网络I/O、磁盘I/O和数据序列化/反序列化。识别出宽依赖就意味着识别出了性能瓶颈点。开发者应该优先考虑使用带有“预聚合”功能的算子（如reduceByKey代替groupByKey）来减少Shuffle的数据量。

___
### 30. 说下Spark中的Transform和Action，为什么Spark要把操作分为Transform和Action?常用的列举一些，说下算子原理
Actions: 用于触发计算并输出结果的操作。它要么将计算结果返回给驱动程序（Driver Program），要么将结果写入外部存储系统
Transformations: 用于构建计算逻辑的操作。它从一个已有的 RDD/DataFrame/Dataset 创建一个新的数据集,惰性（Lazy）。调用转换操作时，Spark
不会立即执行计算，它只是记录下这个操作，并将其添加到逻辑执行计划（DAG） 中。  
为什么？   
为了优化执行计划: Spark 的 DAG 调度器可以看到完整的计算流程图（所有转换操作构成的血缘关系图）。在行动操作被触发时，它可以进行全局优化。  
减少不必要的计算和I/O: 如果用户定义了一系列转换操作后发现自己写错了，在没有行动操作的情况下，不会有任何实际的计算发生，从而节省了宝贵的集群资源。只有在最终需要结果时，才会触发整个计算流程.  
降低复杂度: 开发者可以像编写单机程序一样，一步步地定义复杂的数据流水线，而无需担心中间结果的存储和分布式计算的细节。Spark 会在幕后为你安排好一切。
___
### 31. Spark的哪些算子会有shuffle过程?
宽依赖都会造成。
___
### 32. Spark有了RDD，为什么还要有Dataform和DataSet?
RDD： 是Spark的基础和数据处理的底层核心，提供了最灵活、最底层的API。  
DataFrame： 是建立在RDD之上的高级抽象，以列式存储为核心，为结构化数据的处理进行了深度优化。  
DataSet： 是DataFrame的扩展，在提供DataFrame所有优化的同时，融合了RDD的类型安全和面向对象编程的优点。  

RDD存储的是Java/Scala对象。无论是序列化、反序列化还是在内存中存储，对象本身的开销（如JVM对象头、包装类等）和GC（垃圾回收）成本都非常高，尤其是在数据量巨大。  
Spark引擎无法理解RDD中数据的内部结构，因此无法做深度优化。每个转换操作（如map、filter）都是在“黑盒”上执行。  
RDD API是面向JVM对象的，没有 schema（模式）的概念。例如，要过滤一个Person对象的RDD，你需要写rdd.filter(_.age > 18)。Spark完全不知道age是什么，无法进行优化。  
对于SQL查询、聚合等常见数据分析任务，用RDD API写起来相对繁琐且效率不高。  

DataFrame是一个以命名列（Column）组织的分布式数据集，等同于关系型数据库中的一张表或Python/R中的DataFrame。  
它有一个明确的Schema，定义了每一列的名称和数据类型（如name: String, age: Int）。  
底层仍然是RDD，但存储的不再是JVM对象，而是二进制格式的Row对象（InternalRow）。

DataSet又是面向对象的强类型的，DataFrame可以看成DataSet\[row\]

___
### 33. Spark的RDD、DataFrame、DataSet、DataStream区别?
上面已经提到了RDD、DataFrame、DataSet，那么DataStream和前几个又有什么区别呢？  
RDD, DataFrame, Dataset 主要用于处理有限的、静态的数据集（批处理）。
DataStream 主要用于处理无限的、连续的、实时的数据流（流处理）。     
批处理： 用 spark.read + DataFrame + df.write   
流处理： 用 spark.readStream + DataStream + df.writeStream  
___
### 34. Spark的Job、Stage、Task分别介绍下，如何划分?
Job： 由一个行动操作触发的整个计算流程。每次你在代码中调用一个像 count(), collect(), saveAsTextFile(), show() 这样的行动算子时，就会产生一个Job。  
一个Spark应用（Application）可以由多个Job组成，每个行动算子产生一个Job。  
Stage：  Job的子集。一个Job会根据宽依赖被划分成一个或多个Stage。每个Stage包含一系列可以流水线化执行的窄依赖转换操作。  
Stage内部是纯窄依赖的操作（如多个连续的map、filter），因此可以并行计算，无需数据移动。Stage之间是宽依赖，需要进行Shuffle（数据混洗），必须等待前一个Stage执行完毕才能开始下一个Stage。  

Task：Stage的子集，是Spark中最小的执行单元。一个Stage会根据其分区数被拆分成多个Task。  
每个Task负责处理一个分区的数据。每个Task在一个Executor的CPU Core上执行，是真正干活的单元。 同一个Stage中的所有Task执行的逻辑完全相同，只是处理的数据不同。
___
### 35. Application、job、Stage、task之间的关系.
和上面一样。
___
### 36. Stage内部逻辑
将一个 Stage 中的所有窄依赖转换操作拼接成一个“函数链”，然后将这个函数链应用到每个数据分片上，整个过程在一个线程内连续、流水线地执行，无需将中间结果物化（落盘）。
___
### 37. 为什么要根据宽依赖划分Stage?
宽依赖是数据需要重新洗牌（Shuffle）的信号，而Shuffle是分布式计算中最昂贵、最需要同步的操作，因此它自然成为了划分计算阶段的边界。  
想象一下reduceByKey()操作：为了对相同的key进行汇总，所有分布在集群不同节点上的、相同key的数据，必须被发送到同一个节点上去处理。  
如果没有Stage划分：Spark将无法知道必须在Shuffle处进行同步和物化，可能会尝试将Shuffle操作和之前的操作流水线化，这将导致错误，因为一个Task无法获取其他Task还未计算出来的数据。  
  
Spark的容错机制基于RDD的血缘关系图重新计算。但重新计算的范围需要最小化以提升效率。  
通过根据宽依赖划分Stage，Spark将计算流程分成了一系列步骤（Stage）。 每个Stage内部的窄依赖变换被捆绑在一起，它们的结果在Stage边界处（即Shuffle时）会被物化到磁盘。  
如果Stage N（宽依赖之后）的计算失败，Spark不需要从最原始的数据开始重新计算。它可以直接从Stage边界处物化的Shuffle数据开始，重新计算Stage N。这极大地减少了容错的开销。  
  
DAGScheduler（负责Stage划分的组件）的最终目标是生成一个最优的执行计划。Stage内部是连续的窄依赖，这意味着这些操作可以被流水线化。多个map、filter操作可以被组合成
一个Task，在一个线程内连续执行，无需将中间结果溢出到磁盘，效率极高。Stage的边界明确了可以进行流水线化的范围。这种清晰的阶段划分使得调度变得非常简单和高效。  

___
### 38. 为什么要划分Stage
如上所示。  
___
### 39. Stage的数量等于什么。
宽依赖RDD的数量+1.  

___
### 40. 对RDD、DAG和Task的理解
RDD是一个不可变的、分布式的对象集合，每个RDD不仅包含数据，更重要的是记录了它是如何从其他RDD计算得来的（它的血缘关系）。  
DAG是有向无环图。当你对一个RDD进行一系列转换操作时，Spark会将这些RDD的依赖关系（血缘）记录下来，形成一个DAG。  
Task是Spark中最小的工作单元，代表了一个分区数据在一个阶段内的计算任务。   
___
### 41. DAG为什么适合Spark?
因为它完美地契合了Spark惰性计算、内存迭代和全局优化的核心理念，解决了传统MapReduce模型的根本性瓶颈。 
如果没有DAG：Spark就无法看到完整的计算逻辑，只能一步一步地执行，无法进行这些深度的优化。  
RDD的弹性（Resilient）很大程度上依赖于DAG记录的血缘关系。如果没有DAG： 就无法实现这种精确的、按需的容错机制，可能需要进行昂贵的数据备份或全链路重算。  

总结：DAG是Spark的灵魂。 它不仅仅是一个数据结构的表示，更是一个强大的优化引擎和调度指南。它将用户编写的看似一步一步的代码，
转换成一个经过高度优化的、可在分布式集群上高效执行的物理计划。正是DAG的存在，才使得Spark能够实现其“速度更快”的承诺，同时
保持了编程的灵活性和容错的弹性。没有DAG，Spark就退化为一个普通的分布式计算框架，无法发挥其巨大的性能优势。
___
### 42. 介绍下Spark的DAG以及它的生成过程
DAG 的生成过程是 Spark 惰性计算 的完美体现。整个过程可以分为两个核心阶段: 
逻辑计划阶段：构建 DAG  
物理计划阶段：将 DAG 转换为执行计划  
___
### 43. DAGScheduler如何划分?干了什么活?
DAGScheduler 的核心工作是面向 Stage 的任务调度。它介入的时机是：当一个行动操作被调用，触发了 Job 的执行。  
划分 Stage：根据 RDD 的依赖关系（DAG），以宽依赖为边界，将一个 Job 的计算图划分为多个 Stage。 
提交 Stage：按照 Stage 的依赖关系，依次或并行地将 Stage 提交给 TaskScheduler 去执行。  
处理故障：如果某个 Task 执行失败，DAGScheduler 会负责重新提交计算失败的 Stage。（注意：Task 级别的重试和调度由 TaskScheduler 负责）。  
如何划分应该之前已经提到了。  
___
### 44. Spark容错机制?
Spark 的容错机制是其“弹性”的核心体现，它并不是通过简单的数据备份来实现的，而是利用 RDD 的血缘关系和 Stage 的划分来实现高效的低成本容错。  
Spark 的容错机制核心是：如果某个分区的数据丢失了，我可以根据它最初是如何被计算出来的“配方”（即血缘），重新计算它。
___
### 45. RDD的容错
RDD 级别的容错,  
窄依赖的容错: 代价小。如果某个分区的数据丢失（例如，一个 Task 执行失败），由于窄依赖的子分区只依赖于父 RDD 的少量特定分区，Spark 只需要重新计算父 RDD 中那些丢失的分区即可。  
宽依赖的容错：代价大。如果宽依赖后的某个分区数据丢失，问题就严重了。因为它的数据来源于父 RDD 的所有分区（因为 Shuffle 需要所有数据来重新计算 Key 的分布）。要重建它，几乎需要重新计算整个父 RDD。  

Spark 的容错是一个多层次的、协同工作的系统。它建立在 RDD血缘 这一核心概念之上，通过 DAG调度器的Stage划分 来优化恢复过程，并由 Task调度器
和 集群管理器 共同协作来处理各种运行时故障，从而在分布式环境下提供了高效且强大的容错能力。
___
### 46. Executor内存分配?
Spark Executor 的内存分配并不简单，它被划分成了几个具有不同用途的区域。理解这些区域的作用对于避免 OutOfMemoryError（内存溢出）和提升应用性能至关重要。  
一个 Executor 的内存主要由三大部分构成，由 spark.executor.memory 参数控制:  

JVM Heap Memory：堆内内存。由 JVM 统一管理，受 GC（垃圾回收）影响。这是最主要的部分。

Off-Heap Memory：堆外内存。不受 JVM 管理，也就不受 GC 影响，由 Spark 自己管理。用于减少大型工作负载的 GC 开销。

Overhead Memory：预留内存。用于 JVM 自身开销（如线程栈、本地数据结构等）。这是除了堆内和堆外之外，额外分配的一块安全区。
___
### 47. Spark的batchsize，怎么解决小文件合并问题?
Spark 本身的 batchSize 通常指的是在读取数据源（如 JDBC）时，一次获取多少行数据，它不直接用于解决小文件问题。 
解决小文件问题的核心思路是：在写入数据时，主动控制每个输出文件的数据量，而不是事后补救。  
小文件的根本原因是：Task 的数量决定了文件的个数。如果一个作业有太多的 Task，并且每个 Task 都输出一个文件，就会产生大量小文件。  
使用算子：使用 coalesce 或 repartition 控制输出文件数（最常用）。  
使用 Spark SQL 的自适应查询执行（AQE）: AQE 会在 Shuffle 后统计每个分区的大小，如果发现很多小的分区，它会自动将它们合并成更大的分区。
___
