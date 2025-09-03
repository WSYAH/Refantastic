### 48. Spark参数(性能)调优
调优一般从问题入手，在UI上面先定位问题，确认到底是资源不足还是数据倾斜问题。  
一般遇到了问题，任务挂掉，先进行资源扩展，因为大部分都是因为这个挂掉的。  
通过Spark-submit 调整参数，调整Executor数量、CPU核数、Executor内存、Driver端内存。  
spark.sql.shuffle.partitions（这个比较重要的），是用来调整并行度的，Shuffle 后分区数（默认200）。这个参数不对会导致大量小文件或单个分区过大OOM。
原则是让每个分区的数据量在 128MB ~ 1GB 之间。如果数据量小，则调小（如100），如果分区量大则调大（如 1000 或更多）。可粗略按 总Shuffle数据量 / 目标分区大小(如512MB) 估算。  
```
// 开启自适应查询执行-AQE
spark.conf.set("spark.sql.adaptive.enabled", true)
// 自动合并Shuffle后的小分区
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", true)
// 动态调整Join策略
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", true)
// 动态处理数据倾斜
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", true)
# 动态调整Executor数量
spark.conf.set("spark.dynamicAllocation.enabled", true)
spark.conf.set("spark.dynamicAllocation.minExecutors", 10) // 最小Executor数
spark.conf.set("spark.dynamicAllocation.maxExecutors", 100) // 最大Executor数
# Shuffle优化
spark.shuffle.file.buffer：增加 Shuffle Write 时的缓冲大小（默认 32k），减少 I/O 次数。可增至 64k 或 128k。
spark.sql.adaptive.advisoryPartitionSizeInBytes：配合 AQE 使用，建议目标分区大小（如 256MB）。
```
___
### 49. 介绍一下Spark怎么基于内存计算的
显式的内存持久化（persist()）供重复使用。
  
隐式的流水线执行（DAG 优化）避免不必要的中间结果。
  
高效的内存管理（Tungsten）减少 GC 开销和 CPU 缓存命中。
  
弹性的容错机制（血缘关系）保证内存计算的可靠性。

___
### 50. 说下什么是RDD(对RDD的理解)?RDD有哪些特点?说下知道的RDD算子
RDD是弹性分布式数据集，是 Spark 对数据和计算的一种抽象，它是 Spark 最根本、最核心的数据结构。  
数据集：RDD 本质上是一个只读的、分区的数据集合。它可以来源于 HDFS 文件、本地文件、程序中的集合，或者是其他 RDD 转换而来。  
分布式：RDD 的数据并非集中存储在一台机器上，而是被分片（Partition） 并分布存储在集群的多个节点上。这使得 Spark 可以并行计算。  
弹性：这是 RDD 最精髓的特性。它主要体现在三个方面：  
存储的弹性：数据可以存储在内存或磁盘上，并能在两者之间自动切换。RDD 会优先使用内存，但当内存不足时，会弹性地将数据 spill 到磁盘。  
容错的弹性：RDD 通过 血缘关系 来实现高效的容错。如果某个分区的数据丢失了（比如节点宕机），Spark 不需要从头复制整个数据集，而是根据记录的
血缘关系（即这个 RDD 是如何从其他 RDD 计算得来的），只重新计算丢失的那部分分区数据即可。这比传统的数据复制容错机制高效得多。  
分区的弹性：可以根据需要重新划分数据分区，以优化计算效率（例如 repartition 操作）。
   
简单来说，RDD 就是一个不可变的、分布式的对象集合，Spark 通过它来将对数据的操作（转换、动作）抽象成一个有向无环图，并基于此进行高效的并行计算和容错。  

### 50-2 RDD 特点
分区：一个 RDD 由多个分区组成，每个分区在集群中的不同节点上运行。分区是 Spark 中并行计算的基本单元。   

只读：RDD 是不可变的。一旦创建，你就不能直接修改它。所有的“修改”操作实际上都是通过转换生成一个新的 RDD。这种不可变性保证了数据的一致性和容错的简便性。  

血缘关系：每个 RDD 不仅包含数据本身，还记录了它是如何从其他 RDD 转换而来的依赖关系，这个关系链就叫血缘。这是实现容错机制的关键。  

缓存：对于会被重复使用的 RDD（例如在迭代计算中），可以显式地调用 persist() 或 cache() 方法将其持久化到内存或磁盘中。这样在后续计算中就可
以直接使用，而无需从头再计算一遍，极大地提升了性能。  

计算：Spark 采用 “惰性计算” 模式。对 RDD 的转换操作（如 map, filter）并不会立即执行，而是先记录下来，构建一个由转换操作组成的有向无环图。
只有当遇到一个行动操作（如 count, collect）时，所有累积的转换才会被真正触发执行。  

### 50-2 RDD 算子
RDD的操作分为两大类：转换和行动。  
转换是惰性的，它们只记录操作，返回一个新的 RDD，而不会立即执行计算。  
- Value 数据类型：  
map(func)：对 RDD 中的每个元素应用 func 函数，返回一个新的 RDD。  
filter(func)：过滤，返回一个由能使 func 返回 true 的元素组成的新 RDD。  
flatMap(func)：类似于 map，但每个输入元素可以映射为 0 或多个输出元素（func 返回一个序列）。  
mapPartitions(func)：类似于 map，但以分区为单位进行处理，func 的类型是 Iterator[T] => Iterator[U]。效率比 map 高，因为减少了函数调用次数。   
union(otherRDD)：返回两个 RDD 的并集。  
distinct([numPartitions])：对 RDD 中的元素进行去重。   
groupBy([func])：根据 func 的返回值对数据进行分组。    
sortBy(func, [ascending], [numPartitions])：使用 func 对数据进行处理，对处理后的结果进行排序。  
- 双 Value 数据类型（操作两个 RDD）   
intersection(otherRDD)：返回两个 RDD 的交集。
subtract(otherRDD)：返回一个由只存在于第一个 RDD 中而不存在于第二个 RDD 中的所有元素组成的 RDD（差集）。
cartesian(otherRDD)：返回两个 RDD 的笛卡尔积。   
- Key-Value 数据类型    
partitionBy(partitioner)：根据指定的分区器（如 HashPartitioner）对 RDD 进行重分区。
reduceByKey(func, [numPartitions])：在一个 (K, V) 对的 RDD 上调用，返回一个 (K, V) 对的 RDD，使用指定的 func 函数将每个 key 的值聚合在一起。  
groupByKey([numPartitions])：对具有相同 key 的 value 进行分组。  
aggregateByKey(zeroValue)(seqOp, combOp, [numPartitions])：使用不同的函数对每个分区内和分区间的数据进行聚合，比 reduceByKey 更通用。  
sortByKey([ascending], [numPartitions])：在一个 (K, V) 的 RDD 上调用，K 必须实现 Ordered 接口，返回一个按 key 排序的 RDD。  
join(otherRDD, [numPartitions])：对两个 (K, V) 和 (K, W) 的 RDD 进行内连接，输出 (K, (V, W))。   
cogroup(otherRDD, [numPartitions])：对两个 RDD 中的相同 key 的 value 分别进行分组，输出 (K, (Iterable[V], Iterable[W]))。  
- 行动算子 行动是急切的，它们会触发所有累积的转换操作形成一个有向无环图，并由 DAGScheduler 和 TaskScheduler 最终执行，得到一个具体的值或输出结果。  
reduce(func)：通过函数 func（接受两个参数，返回一个值）聚合数据集中的所有元素。  
collect()：将数据集中的所有元素以一个数组的形式返回给驱动程序。注意：数据量很大时不要用，可能导致驱动程序 OOM。     
count()：返回 RDD 中元素的个数。  
first()：返回 RDD 中的第一个元素（类似于 take(1)）。  
take(n)：返回一个由 RDD 的前 n 个元素组成的数组。  
takeSample(withReplacement, num, [seed])：返回一个数组，该数组由从数据集中随机采样的 num 个元素组成。  
takeOrdered(n, [ordering])：返回 RDD 中按自然顺序或自定义顺序排序后的前 n 个元素。  
saveAsTextFile(path)：将数据集的元素以文本文件的形式保存到指定的路径下（如 HDFS）。  
saveAsSequenceFile(path)：将数据集中的元素以 Hadoop SequenceFile 的格式保存到指定的目录下。  
countByKey()：针对 (K, V) 类型的 RDD，返回一个 (K, Int) 的 Map，表示每个 key 对应的元素数量。  
foreach(func)：对 RDD 中的每个元素应用函数 func。通常用于将数据发送到外部存储系统（如数据库）或更新累加器。  
___
### 51. RDD底层原理
- 分布式存储与分区: 一个 RDD 在物理上并不是一个完整的数据块，而是被切分成多个分区，这些分区分布在整个集群的不同节点上。   
- 依赖关系与有向无环图: 当你对一个 RDD 进行转换操作（如 map, filter）得到一个新的 RDD 时，新的 RDD 会记录它是从哪个（或哪些）RDD 转换而来的，
以及转换的逻辑（即函数 func）。这种 RDD 之间的生成关系被称为血缘关系。      
- 计算调度与任务划分:当遇到一个行动操作时，Spark 会根据 RDD 的血缘关系，构建一个完整的有向无环图。  
- 容错与血缘机制: 当某个节点宕机导致 RDD 的某个分区数据丢失时，Driver 端的 DAGScheduler 会察觉到任务失败。由于 RDD 记录了其血缘关系，
Spark 可以准确地知道丢失的分区是从哪些父 RDD 的哪些分区计算得来的。Spark 会重新调度任务，只重新计算那些丢失的分区所依赖的父分区，最终
计算出丢失的数据。对于宽依赖，由于 Shuffle 数据可能已经丢失，可能需要重新计算整个上游的 Stage。
- 内存管理与持久化: RDD 的计算结果会优先存储在内存中，供后续操作快速访问，避免了像 MapReduce 那样频繁读写 HDFS。
通过 persist() 或 cache() 方法，用户可以指定 RDD 的存储级别，在内存和磁盘之间做出权衡，比如存内存、磁盘、先内存内存不足则spill到磁盘。
通过checkpointing来设置检查点，直接从检查点读取数据，无需从头计算。  
___
### 52. RDD属性
- 一个 RDD 由一个或多个分区组成。每个分区是其数据集的一个逻辑切片，是并行计算的基本单位。  
- 每个 RDD 都包含一个用于计算其每个分区的函数。   
- RDD 的每次转换都会生成一个新的 RDD，新的 RDD 会记录它依赖于哪些父 RDD。这种依赖关系的集合就是血缘。   
- 对于 Key-Value 类型的 RDD，可以有一个 Partitioner（分区器），它决定了数据在 Shuffle 过程中如何被重新分区。    
- 首选位置： 每个分区都有一个首选位置的偏好列表。它指示了“计算应该在哪里执行更高效”。
___
### 53. RDD的缓存级别?
RDD 的缓存（持久化）本质上是一种机制，允许将 RDD 的计算结果保存在内存或磁盘中，以便在后续的操作中重复使用，从而避免重复计算。   
在 Spark 的惰性计算模型中，每次遇到一个行动操作（如 count, collect），它都会从血缘关系图的最开始重新计算。如果一个 RDD 会被多个行动操作使用，那么它就会被重复计算多次，造成巨大的性能浪费。  
通过调用 rdd.persist() 或 rdd.cache() 方法，你可以告诉 Spark：“请把这个 RDD 的结果保存起来，后面我还要用”。这样，在第一次行动操作触发计算后，结果就会被存储起来，后续的所有行动操作都会直接使用已存储的结果，极大地提升计算效率。

| 缓存级别	               | 含义            | 	解释                                                                             | 	使用场景                                            |
|---------------------|---------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| MEMORY_ONLY         | 只存内存          | 将 RDD 以反序列化的 Java 对象形式存储在 JVM 内存中。如果内存不足，部分分区将不会被缓存，每次需要时重新计算。                  | 默认级别。性能最快，因为完全基于内存。适合内存足够且对象不大的情况。               |
| MEMORY_ONLY_SER     | 	序列化后存内存      | 	将 RDD 以序列化的字节数组形式存储（如 Java Serialization, Kyro）。更省内存，但读写时会增加 CPU 开销用于序列化/反序列化。 | 	在 MEMORY_ONLY 内存不足时使用。用 CPU 时间换内存空间，可以缓存更大的数据集。 |
| MEMORY_AND_DISK     | 	内存不够存磁盘      | 	将 RDD 以反序列化对象形式存内存。如果内存不足，溢出的分区会被存储到磁盘上。需要时从磁盘读取。	                             | 当 RDD 太大，无法完全放入内存时使用。优先保证内存速度，部分数据退到磁盘。          |
| MEMORY_AND_DISK_SER | 	序列化后，内存不够存磁盘 | 	类似于 MEMORY_AND_DISK，但存储在内存中的数据是序列化后的形式。溢出到磁盘的数据也是序列化的。                         | 	最常用的通用级别之一。在内存使用和 CPU 开销之间取得了很好的平衡，适合大型数据集。     |
| DISK_ONLY           | 	只存磁盘	        | 只将 RDD 分区存储到磁盘上。	                                                               | 内存极度稀缺，或者数据集非常大且重用次数不多的情况。速度最慢，但可靠。              |
| OFF_HEAP	           | 堆外内存	         | 与 MEMORY_ONLY_SER 类似，但数据存储在堆外内存（如 Alluxio/Tachyon）。不受 JVM GC 影响，但访问速度稍慢。        | 	用于解决因为 JVM 垃圾回收暂停而导致的大量缓存数据抖动的问题。               |

cache()： 等价于 persist(MEMORY_ONLY)。这是最常用的方法。
persist()： 如果不带参数，默认也是 persist(MEMORY_ONLY)。带参数时，可以指定上述任意缓存级别。
___
### 54. Spark广播变量的实现和原理?
在 Spark 作业中，通常会在 Task 中用到一些只读的、大型的共享数据（比如一个巨大的查询表、机器学习模型参数、字典等）。按照默认行为，这些变量会被复制到每个 Task 中。如果一个变量大小是 100MB，并且有 1000 个 Task，那么总共会在网络中传输 100GB 的数据！这会导致：
巨大的网络开销：成为性能瓶颈。
巨大的内存开销：每个 Executor 上的多个 Task 可能会存储多份相同的数据，消耗大量内存。
解决方案：广播变量
广播变量允许程序员在每台机器（每个 Executor）上缓存一个只读的变量，而不是将其副本与每个 Task 一起发送。这样，一台机器上的所有 Task 都可以共享这一份数据。
这样维护的变量副本数就可以为Executor的数量而非Task数量了。  
广播变量的实现原理可以分为两大步骤：分发 和 获取。  
**分发**当你调用 sc.broadcast(v) 时，Driver 端会发生以下事情：  
- 创建BroadCast对象，将变量序列化、Driver 会创建一个 Broadcast[T] 对象（例如 TorrentBroadcast），这个对象本身很小，它并不包含实际数据，而是包含如何获取这些数据的元信息。  
- 切块与存储：Spark 将序列化后的数据切分成多个小块（默认是 4MB 的块）。这样做是为了提高分发的并行度和效率。Driver 将自己也作为其中的一个数据源，并将这些数据块存储到自己的 BlockManager 中。BlockManager 是 Spark 中统一管理内存、磁盘和堆外存储的组件。
- 信息告知：Driver 将这个 Broadcast 对象的元信息（包括数据块的 ID、位置等）作为 Task 闭包的一部分发送给 Executor。这个元信息很小，传输开销几乎可以忽略不计。
**获取**
- 当 Executor 上的 Task 第一次使用 broadcastVar.value 时，会发生以下过程：  
- 本地查。
- 远程拉取。 它不仅仅从 Driver 拉取！它可以从任何一个已经拥有该数据块的 Executor 拉取。这类似于 BitTorrent 协议（因此名为 TorrentBroadcast）。
- 本地存储与共享：Executor 拉取到一个数据块后，会立即将其存储到自己的 BlockManager 中。 这样，该 Executor 上的后续 Task 以及同一台机器上的其他 Executor（如果有的话）在需要时就可以直接从本地读取，无需再走网络。 最终，所有数据块拉取完毕后，会在本地重组并反序列化成完整的广播变量 v，提供给 Task 使用。

Spark 主要使用 TorrentBroadcast 类来实现广播变量，其名字就体现了其类似 BT 下载的分发思想。

- 分块传输：将大对象切分成小块，允许并行地从多个源获取，而不是一次性传输一个大文件。

- 去中心化分发：每个获取了数据块的 Executor 都会成为一个新的数据源，为其他 Executor 提供下载服务。这使得数据源像滚雪球一样越来越多，下载速度也越来越快。

- 自动容错：如果一个 Executor 失败，数据并不会丢失，因为其他拥有相同数据块的 Executor 仍然可以提供服务。

- 内存管理：广播的数据存储在 Executor 的 BlockManager 中，其存储级别是 MEMORY_AND_DISK。这意味着它会优先放内存，内存不足时溢出到磁盘，保证了可靠性。
___
### 55. reduceByKey和groupByKey的区别和作用?
reduceByKey：**对具有相同 key 的多个 value 应用一个聚合函数（func）**，最终将每个 key 的 value 列表缩减为单个聚合后的值。这个函数必须是可交换和可结合的（例如 (a, b) => a + b）。  
groupBykey： **RDD 中具有相同 key 的 value 分组到一个序列（Iterable）中。** 它不进行任何计算，只是将数据重新排列。  
目标如果是聚合（Reduce）：毫不犹豫，使用 reduceByKey（或更通用的 aggregateByKey）。
目标如果是拿到所有原始值进行后续处理（Group）：才使用 groupByKey。
___
### 56. reduceByKey和reduce的区别?
| 特性    | reduce                    | reduceByKey                       |
|-------|---------------------------|-----------------------------------|
| 类型	   | 行动操作                      | 	转换操作                             |
| 操作对象	 | 整个 RDD 中的所有元素	            | Pair RDD 中具有相同 key 的元素            |
| 输出	   | 一个单一的、聚合后的值（与 RDD 元素类型相同） | 	一个新的 RDD[(K, V)]，每个 key 对应一个聚合结果 |
| 并行度   | 	最终在 Driver 端汇总成一个结果      | 	完全并行，每个 key 的聚合独立进行              |
| 触发时机  | 	立即触发作业执行（Action）	        | 惰性求值，记录 lineage，等待 Action 触发      |

reduce 是一个行动算子，它是一个行动操作，用于将 RDD 中所有元素聚合成一个单一的结果。它接收一个二元函数 (T, T) => T，该函数满足结合律和交换律，从而可以并行计算。  
reduceByKey 是一个转换操作，专门用于 Pair RDD（元素为键值对的 RDD）。它将对每个 key 对应的所有 value 应用一个聚合函数 (V, V) => V，从而为每个 key 生成一个聚合后的值。

___
### 57. 使用reduceByKey出现数据倾斜怎么办?
可以使用两阶段聚合，也就是给key加盐，然后进行本地先聚合（达到预聚合的效果）然后再使用原来的key进行全局聚合。这能将一个倾斜key的压力分散到多个Task上。  
如果因为知道hotkey，那么可以单独处理这些hotkey。  
___
### 58. Spark SQL的执行原理?
Spark SQL 的执行流程可以概括为以下四个核心阶段，其中 Catalyst 优化器是整个过程的大脑和灵魂。  
阶段一：解析和分析   
- 生成“未解析的逻辑计划”，输入：用户提交的 SQL 语句或 DataFrame/Dataset 代码。Spark 使用 ANTLR 等工具将输入解析成一个初始的语法树（AST），称为 Unresolved Logical Plan。
此时，计划是“未解析的”，意味着它知道操作（如 select, filter, join），但不验证表名、列名是否存在，也不确定列的数据类型。它只是一个符号化的抽象结构。  
- 生成“逻辑计划”：分析器结合 Catalog（Spark SQL 的元数据仓库，存储了所有表、列、函数的信息）对“未解析的逻辑计划”进行解析。
解析关系：确认 SQL 中的表名、视图名是否存在。  
解析列名：确认指定的列是否在表中存在，是否有歧义。  
解析类型：确定每个列的表达式的数据类型。  
得到一个解析后的逻辑计划。此时，计划已经完全验证，但仍然是非常抽象的，不涉及任何具体的执行细节。  
<br>
阶段二：优化（Catalyst 优化器的核心）
- 谓词下推：将过滤操作尽量推到数据源附近，甚至推到数据源系统中（如 JDBC 数据库、Parquet 文件），从而尽早减少需要处理的数据量。  
- 列值裁剪：只读取查询中真正需要的列，忽略其他列。对于列式存储（如 Parquet、ORC）效果极佳。  
- 常量折叠：在编译期计算常量表达式，避免运行时重复计算。  
- 连接重排序：根据表的大小和过滤条件，决定多表连接的顺序，尽可能先过滤掉大量数据，再进行代价高昂的连接操作。  
- 将小表广播：自动检测小表，并将其广播到所有 Executor 节点，将 SortMergeJoin 转换为效率更高的 BroadcastHashJoin，避免 Shuffle。  
<br>

阶段三：物理计划与代码生成 

<br>
阶段四：执行
最终，生成的代码被分发到各个 Executor 节点上执行。Executor 以全阶段代码生成的方式运行这些代码，直接从数据源读取数据，并管道化地执行一系列操作（如过滤、投影、聚合），最终输出结果。

___
### 59. Spark SQL的优化?

___
### 60. 说下Spark checkpoint
___
### 61. Spark SQL与DataFrame的使用?
___
### 62. Sparksql自定义函数?怎么创建DataFrame?
___
### 63. HashPartitioner和RangePartitioner的实现
___
### 64. Spark的水塘抽样
___
### 65. DAGScheduler、TaskScheduler、SchedulerBackend实现原理
___
### 66. 介绍下Sparkclient提交application后，接下来的流程?
___
### 67. Spark的几种部署方式
___
### 68. 在Yarn-client情况下，Driver此时在哪
___
### 69. Spark的cluster模式有什么好处
___
### 70. Driver怎么管理executor
___
### 71. Spark的map和flatmap的区别?
___
### 72. Spark的cache和persist的区别?它们是transformaiton算子还是action算子?
___
### 73. Saprk Streaming从Kafka中读取数据两种方式?
___
### 74. Spark Streaming的工作原理?
___
### 75. Spark Streaming的DStream和DStreamGraph的区别?
___
### 76. Spark输出文件的个数，如何合并小文件?
___
### 77. Spark的driver是怎么驱动作业流程的?
___
### 78. Spark SQL的劣势?
___
### 79. 介绍下Spark Streaming和Structed Streaming
___
### 80. Spark为什么比Hadoop速度快?
___
### 81. DAG划分Spark源码实现?
___
### 82. Spark Streaming的双流join的过程，怎么做的?
___
### 83. Spark的Block管理
___
### 84. Spark怎么保证数据不丢失w
___
### 85. Spark SQL如何使用UDF?
___
### 86. Spark温度二次排序
___
### 87. Spark实现wordcount
___
### 88. Spark Streaming怎么实现数据持久化保存?
___
### 89. Spark SQL读取文件，内存不够使用，如何处理?
___
### 90. Spark的lazy体现在哪里?
___
### 91. Spark中的并行度等于什么
___
### 92. Spark运行时并行度的设署
___
### 93. Spark SQL的数据倾斜
___
### 94. Spark的exactly-once
___
### 95. Spark的RDD和partition的联系
___
### 96. spark 3.0特性
___
### 97. Spark计算的灵活性体现在哪里

___
### 98. PySpark 中的 worker，怎么和Java程序通信的
