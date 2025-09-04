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
优先使用 DataFrame/Dataset API 而不是原始的 RDD API。因为 DataFrame/Dataset 的代码能被 Catalyst 和 Tungsten 充分优化，而 RDD 则被视为“黑盒”，无法享受这些优化。  
谓词下推：尽早过滤数据，减少后续处理的数据量。在读取数据源前就进行过滤。
```
// 好的做法：filter 下推
spark.read.parquet("/path/to/data")
  .filter($"date" === "2023-10-27")
  .select($"id", $"value")
  .write.save(...)

// 不好的做法：先 select 再 filter，数据量大
spark.read.parquet("/path/to/data")
  .select($"id", $"value", $"date")
  .filter($"date" === "2023-10-27")
  .write.save(...)
```
避免使用 UDF（User-Defined Functions）,因为UDF是优化盲区，尽量使用内置函数吧，
正确使用缓存，当一个RDD/dataFrame重复使用时候，需要使用缓存，如果只是用一次，就不适合缓存。
___
### 60. 说下Spark checkpoint
Checkpoint 是一种将 RDD 或 DataFrame/Dataset 物化（持久化）到可靠、容错的分布式文件系统（如 HDFS、S3） 的机制。
它的核心目的是切断冗长的 RDD 血缘关系（Lineage），并提高作业的容错能力。  
想象一个场景：你的 Spark 应用有一个非常长的计算链（例如，迭代了 100 次的机器学习算法），初始 RDD 经过大量的 map,
filter, join 等变换才得到最终结果。这个计算链就是 血缘关系（Lineage）。   
<br>
性能问题：如果某个节点失败，Spark 需要根据完整的血缘从头开始重新计算来恢复数据，这个计算过程非常漫长。  
<br>
栈溢出问题：过长的血缘关系本身会占用大量内存来存储元数据，在某些情况下甚至可能导致驱动程序的栈溢出错误。  
<br>
Checkpoint 通过将数据中途持久化到可靠存储来解决这些问题：
<br>
截断血缘（Truncates Lineage）：当对一个 RDD 执行 Checkpoint 后，Spark 会忘记它之前的所有血缘关系，而是将这个 Checkpoint 后的 RDD 作为新的起点。这意味着恢复数据时不再需要从头计算，只需从 Checkpoint 的点开始即可。
<br>
提供可靠存储（Reliable Storage）：数据被写入 HDFS 或 S3 等分布式存储，具备高容错性，即使整个集群重启，数据也不会丢失。
___
### 61. Spark SQL与DataFrame的使用?
不说，没啥可说的。

___
### 62. Sparksql自定义函数?怎么创建DataFrame?
UDF（User-Defined Function） 让你可以用自定义逻辑扩展 Spark SQL 的功能。可以定义def然后通过DataFrame API或者sql注册UDF
```
# 1. 定义普通Python函数
def add_suffix(name):
    return name + "_test"

def is_adult(age):
    return "Adult" if age >= 18 else "Minor"

# 2. 注册UDF（两种方式）

# 方式一：用于DataFrame API
add_suffix_udf = F.udf(add_suffix, StringType())
is_adult_udf = F.udf(is_adult, StringType())

# 方式二：用于SQL查询
spark.udf.register("is_adult_sql_udf", is_adult, StringType())

# 3. 使用UDF
# 在DataFrame API中使用
df.withColumn("name_with_suffix", add_suffix_udf(df["name"])) \
  .withColumn("age_group", is_adult_udf(df["age"])) \
  .show()

# 在SQL中使用
df.createOrReplaceTempView("people")
spark.sql("SELECT name, age, is_adult_sql_udf(age) as age_group FROM people").show()
```
DataFrame可以从列表创建、从字典列表创建、从文件读取、从RDD转换、从Pandas DataFrame创建

___
### 63. HashPartitioner和RangePartitioner的实现
HashPartitioner 通过计算键的哈希值并对其取模来确定数据分区。它的核心优势是计算极其高效，只需一次哈希和取模运算，能保证不同键的均匀分布。
但其致命缺点是无法处理数据倾斜，相同哈希值或极端热点键都会被分配到同一分区，导致负载不均，并且它完全不保持数据的任何顺序性，适用于不要求有序的常规聚合操作。  
<br>
RangePartitioner 通过采样估算整体数据分布，对样本排序后确定分区边界，再使用二分查找为每个键定位分区。它的核心优势是能产生全局有序的输出并有效缓解数据倾斜，
通过范围划分确保各分区数据量相对均衡。代价是实现复杂且开销较大，需要额外的采样、排序和查找操作，主要适用于需要全局排序或处理高度倾斜数据的场景。
```scala
class HashPartitioner(partitions: Int) extends Partitioner {
  def numPartitions: Int = partitions
  def getPartition(key: Any): Int = {
    // 使用非负模运算来确保分区号在 [0, numPartitions-1] 范围内
    (key.hashCode() & Integer.MAX_VALUE) % numPartitions
  }
}
```
```scala
class RangePartitioner[K : Ordering : ClassTag, V](partitions: Int, rdd: RDD[_ <: Product2[K, V]]) extends Partitioner {

  private var rangeBounds: Array[K] = ... // 通过采样和排序计算得到的边界数组

  def numPartitions: Int = rangeBounds.length + 1

  def getPartition(key: Any): Int = {
    val k = key.asInstanceOf[K]
    // 使用二分查找确定 k 在 rangeBounds 中的位置
    val partition = java.util.Arrays.binarySearch(rangeBounds, k)
    if (partition < 0) {
      // 返回值为 (-(insertion point) - 1)
      -partition - 1
    } else {
      partition
    }
  }
}
```
___
### 64. Spark的水塘抽样
Spark 的水塘抽样是一种经典的分布式随机抽样算法，其核心思想是在单次遍历数据流的过程中，通过动态替换样本池的方式，保证每个元素被选入最终样本
的概率完全相等。在 Spark 的分布式环境下，该算法分两阶段执行：首先各个分区并行地独立进行本地水塘抽样，生成候选样本集；然后 Driver 端将所有
分区的候选样本汇总，再次进行全局水塘抽样，最终得到一个无偏的、能代表整体数据分布的固定容量样本。这种高效且公平的抽样机制是 Spark 中 
RangePartitioner 能够实现数据均匀划分的关键基础。同样也是simple操作的基石。
___
### 65. DAGScheduler、TaskScheduler、SchedulerBackend实现原理
DAGScheduler、TaskScheduler 和 SchedulerBackend 是 Spark 作业调度的核心三级流水线：DAGScheduler 负责高层规划，它将用户的作业计算图（DAG）
根据宽依赖划分为多个执行阶段（Stage），并为每个 Stage 创建出一组任务（TaskSet）作为物理执行计划；TaskScheduler 负责中层的任务调度与资源分配，
它接收这些 TaskSet，并遵循 FIFO 或 FAIR 等调度策略，向底层资源管理器申请资源；SchedulerBackend 则负责底层的资源对接与任务执行，它与 
Cluster Manager（如 YARN、Standalone）进行通信，为申请到的资源（Executor）分配具体任务（Task），监控任务运行状态并将结果反馈回上层，共同协作完成分布式计算。
<br>
SchedulerBackend（资源对接层）：它的核心原理是抽象底层资源管理器，提供统一资源接口。它是一个抽象类，针对不同的集群管理器（如YARN、Standalone、K8s）
有不同实现（如YarnSchedulerBackend）。它的核心实现是与Cluster Master持续通信，协商申请资源（Executor），并向上层的TaskScheduler汇报可用的资源情况。
它是真正与集群打交道的“司机”。
___
### 66. 介绍下Sparkclient提交application后，接下来的流程?
户通过spark-submit脚本将Application提交后，首先会在本机启动一个JVM进程执行用户的main函数并初始化SparkContext；SparkContext作为驱动器（Driver）
会向集群资源管理器（如YARN ResourceManager）申请启动一个ApplicationMaster（AM）；AM启动后随即向资源管理器注册并申请计算资源（Container）；资源管理器分配Container后，
AM与各个NodeManager通信在Container中启动Executor进程；Executor启动后反向向Driver端的SparkContext注册并建立心跳连接；随后Driver将DAGScheduler划分
好的Stage和TaskScheduler生成的TaskSet分发给各个Executor执行；Executor在线程池中运行Task，期间通过心跳向Driver汇报状态并获取新任务，直至所有Task执行完毕，Application完成，资源被释放。
___
### 67. Spark的几种部署方式
 Local（本地模式）、Standalone（独立模式） 和 On YARN/Mesos/K8s（集群模式）。
___
### 68. 在Yarn-client情况下，Driver此时在哪
在 YARN-client 模式下，Driver 进程运行在客户端提交任务的机器上（即执行 spark-submit 命令的那台机器），而不是 YARN 集群中；此时由 YARN 
创建的 ApplicationMaster 角色只负责向 ResourceManager 申请 Executor 资源，而真正的驱动逻辑（如调度任务、收集结果）则由集群外部的客户端 
Driver 负责，这会导致客户端必须始终在线且存在网络瓶颈的风险。
<br>
因为是Client而不是cluster模式。
___
### 69. Spark的cluster模式有什么好处
Spark Cluster 模式的核心好处在于它将 Driver 进程部署在集群内部（而非客户端机器），由集群管理器统一管理，从而消除了单点故障和网络瓶颈，
使得应用运行更稳定、性能更高、资源调度更高效，非常适合需要高可靠性和吞吐量的生产环境。
___
### 70. Driver怎么管理executor
Driver 通过与其建立的双向心跳机制和 RPC 通信来全面管理 Executor：它在应用程序启动时向集群管理器申请 Executor 资源，随后直接向 Executor
分发任务代码和计算逻辑，并通过持续的心跳监控其活跃状态和任务执行进度，同时根据数据本地性原则动态分派任务，最后在任务完成后负责回收资源或是在 
Executor 失效时主动重新调度其上的任务，从而实现对整个计算过程的集中协调和容错管理。
___
### 71. Spark的map和flatmap的区别?
map 是一对一，每个输入元素都严格转换为一个输出元素；而 flatMap 是一对多（或一对零），每个输入元素可以转换为零个、一个或多个输出元素，最后将
所有子列表“压平”合并成一个单一列表。压平了。
```
rdd = sc.parallelize(["hello world", "spark tutorial"])

# 用 map 按空格拆分，会得到两个数组
mapped_rdd = rdd.map(lambda x: x.split(" "))

print(mapped_rdd.collect())
# 输出: [['hello', 'world'], ['spark', 'tutorial']]
```
```
rdd = sc.parallelize(["hello world", "spark tutorial"])

# 用 flatMap 按空格拆分，然后“压平”所有单词到一个列表中
flatmapped_rdd = rdd.flatMap(lambda x: x.split(" "))

print(flatmapped_rdd.collect())
# 输出: ['hello', 'world', 'spark', 'tutorial']
```
___
### 72. Spark的cache和persist的区别?它们是transformaiton算子还是action算子?
cache() 和 persist() 的核心功能完全相同，都是用于将 RDD/DataFrame 的计算结果持久化（存储）在内存或磁盘中，以避免重复计算。它们的唯一区
别在于灵活性：cache() 是 persist() 的一种特化、便捷形式。cache() 默认使用 MEMORY_ONLY 存储级别，即只将数据以原生对象的形式存储在内存中，
若内存不足则部分分区不会被缓存。而 persist() 方法允许用户显式地指定一个丰富的存储级别（StorageLevel），例如 MEMORY_AND_DISK（内存存不下
则溢写到磁盘）、DISK_ONLY（只存磁盘）、MEMORY_ONLY_SER（序列化后存内存，更省空间但耗CPU）等，从而根据数据大小和集群资源进行更灵活和精细化
的持久化策略控制。因此，你可以简单地将 cache() 理解为 persist(StorageLevel.MEMORY_ONLY) 的快捷方式。
<br><br>
cache() 和 persist() 都是 Transformation 算子。 这是因为调用它们并不会立即触发任何实际的计算或持久化操作，它们只是在 RDD 的血缘关系
（Lineage）上打上一个“需要持久化”的标记或元数据。真正的计算和物化操作是在后续的 Action 算子（如 count(), collect(), saveAsTextFile()）
被调用时才会触发。Spark 会在执行第一个 Action 并计算出该 RDD 的结果后，根据 cache 或 persist 指定的存储级别将其持久化到存储介质中。因此，
它们属于“惰性”的转换操作，仅用于定义计算逻辑，而不执行计算。
___
### 73. Spark Streaming从Kafka中读取数据两种方式?
Spark Streaming 从 Kafka 读取数据主要有两种方式：Receiver-based Approach 和 Direct Approach。
Receiver-based Approach（基于接收器的方式）<br>
这是一种较老的方式，其核心是使用一个专门的 Receiver 线程作为常驻服务运行在 Executor 上，它利用 Kafka 的高层级消费者 API（High-Level
Consumer API）持续地从 Kafka 拉取数据。为了保证零数据丢失，Receiver 会在将数据成功存储到 Spark 的工作内存（Memory）的同时，会预写日志
（Write-Ahead Log, WAL） 到像 HDFS 这样的可靠存储中。这种方式将数据偏移量的管理交给了 ZooKeeper，但由于数据是先被 Receiver 接收再由
Spark Streaming 处理，这导致了 至少一次（at-least-once） 的语义，且因为 WAL 和副本机制，吞吐量较低，并可能出现数据积压问题，因此在 
Spark 新版本中已被标记为“已弃用（deprecated）”。
<br><br>
Direct Approach（直接方式，现代首选）<br>
这是目前官方推荐的首选方式，它不再使用 Receiver，而是让每个 Spark Driver 中的 Executor 使用 Kafka 的简单消费者 API（Simple Consumer API）
直接连接到 Kafka 的各个分区进行拉取。Spark Streaming 会周期性地查询 Kafka 来获取每个 Topic Partition 的最新偏移量（Offset），并据此范围在
每个批次（Batch）中直接、精确地拉取数据，就像处理文件系统中的一个文件一样。这种方式实现了精确一次（exactly-once） 的语义，因为偏移量是由 Spark 
自己管理并 checkpoint 的，无需 ZooKeeper，且由于消除了 Receiver 和 WAL 的开销，它能提供更强的吞吐量和更简单的并行模型（分区与分区一对一），是
现代 Spark Structured Streaming 集成的基础。
___
### 74. Spark Streaming的工作原理?
Spark Streaming 的核心原理是“微批次（Micro-Batch）处理”，它将持续输入的实时数据流按时间间隔（如1秒）切分成一系列小的、离散的批处理数据
（称为DStream），然后使用Spark引擎对每个小批次数据像处理静态RDD一样进行分布式计算，从而将复杂的流处理转换为熟悉的批处理模型，最终通过窗口
操作和状态管理来实现有状态的流处理语义。
<br><br>
这个设计精髓在于：以批处理的方式实现流处理。它通过固定的时间窗口将无界的数据流切割成有界的数据集（RDD序列），然后直接复用强大的Spark Core
引擎对这些数据集进行高速处理。
___
### 75. Spark Streaming的DStream和DStreamGraph的区别?
DStream 是用户层面的数据视图，而 DStreamGraph 是系统层面的执行视图。用户通过组合 DStream 来间接地定义 DStreamGraph，而 Spark Streaming 
则通过解释执行 DStreamGraph 来完成实时计算任务。
<br>
DStream 是 Spark Streaming 中数据流的抽象表示，代表一个持续变化的、离散化的数据序列（由一系列 RDD 构成），是用户直接操作的逻辑对象；而
DStreamGraph 是 Spark Streaming 内部生成的、由这些 DStream 及其之间的转换依赖关系所组成的有向无环图（DAG），它定义了整个流处理应用的
计算逻辑和数据流向，是物理调度执行的蓝图。
<br>
DStream 类似于批处理 Spark 中的 RDD，是代表数据流的基本抽象；而 DStreamGraph 则类似于批处理中的 DAG，是由这些 DStream 及其转换关系所生
成的执行逻辑蓝图。前者定义了“是什么数据”，后者定义了“如何计算这些数据”。
___
### 76. Spark输出文件的个数，如何合并小文件?
Spark 输出文件的个数直接由最终 Stage 的 Task（或分区）数量决定，每个 Task 会生成一个对应的输出文件；若要合并这些小文件，可以在写入数据前使用
coalesce(n) 或 repartition(n) 算子主动减少分区数到 n，或者利用 spark.sql.adaptive.coalescePartitions.enabled 等自适应查询特性自动优化，
从而控制最终输出的文件数量和大小。
<br>
coalesce(n)：用于减少分区数（例如从 200 减到 10）。它通过合并现有分区来实现，避免了 Shuffle，效率较高。这是合并小文件最常用、最推荐的方法。
```df.coalesce(10).write.parquet("output_path") # 合并为大约10个文件```
___
### 77. Spark的driver是怎么驱动作业流程的?
Spark Driver 作为应用的“大脑”和指挥中心，首先将用户代码编译成由 RDD 转换组成的逻辑执行计划（DAG），然后通过 DAGScheduler 根据宽依赖将 DAG 划分为物理执行阶段（Stages），再通过 TaskScheduler 将每个阶段的任务集（Tasks）分发到集群的 Executor 上并行执行，并通过持续的心跳机制监控任务状态、处理故障并收集最终结果，从而全程驱动和协调整个分布式作业的流程。
___
### 78. Spark SQL的劣势?
Spark SQL 的核心劣势在于其“内存计算”架构带来的资源消耗和不稳定性，它高度依赖大量内存进行高效计算，一旦数据量超出集群内存容量就容易出现频繁的磁盘溢写（Spill）甚至 OOM（内存溢出）崩溃，同时由于其惰性执行和查询优化机制，作业排队资源竞争激烈时容易成为性能瓶颈，并且对实时性要求极高的毫秒级查询场景响应延迟远高于专门的MPP数据库或流处理引擎。
___
### 79. 介绍下Spark Streaming和Structed Streaming
Spark Streaming 是 Spark 最初的流处理解决方案，基于一种称为“离散化流”（DStream）的核心抽象。 DStream 本质上是一个由一系列连续的、不可变的 RDD 组成的序列，每个 RDD 代表一个特定时间间隔（例如 1 秒）内到达的数据微批次（Micro-batch）。开发者使用与 RDD 类似的 API（如 map, reduceByKey）来处理这些微批次数据。它的主要特点是提供了对底层批处理（RDD）的精细控制，支持各种状态操作和窗口操作。然而，其劣势也源于此：编程模型仍然是批处理的思维，开发者需要自行管理状态、无法实现端到端的精确一次（exactly-once）语义保证，并且其执行引擎无法基于数据本身进行优化。
<br>
Structured Streaming 是构建在 Spark SQL 引擎之上的新一代流处理库，于 Spark 2.x 版本正式推出。 它不再使用 DStream 概念，而是将无限的数据流抽象为一张持续增长的无界表（Unbounded Table），流计算被视作在这张表上持续执行的增量查询。开发者使用熟悉的 DataFrame 和 Dataset API 进行编程，享受 Spark Catalyst 优化器和 Tungsten 执行引擎带来的自动优化和高性能。其核心优势在于：1. 简洁统一的 API，实现了流处理和批处理代码的统一；2. 强大的语义保证，默认支持端到端的精确一次（exactly-once）处理语义；3. 基于事件时间的处理和容错机制，能更好地处理延迟数据。
<br>
Structured Streaming 并非 Spark Streaming 的简单替代，而是一次根本性的范式演进和能力飞跃。 二者在宏观目标上一致，都是为 Apache Spark 提供流处理能力，但其底层哲学和实现完全不同。Spark Streaming (DStreams) 是 “批模拟流”，用微批次来近似流处理；而 Structured Streaming 是 “流表二元性”，将流处理真正统一到声明式的 DataFrame API 之下。目前，Structured Streaming 是 Spark 官方主推且持续优化的流处理方案，适用于绝大多数新项目，它在易用性、性能和数据一致性方面都远超传统的 Spark Streaming。而 DStreams API 目前主要出于向后兼容性而保留，用于维护旧项目或极少数需要直接操作 RDD 的特殊场景。
___
### 80. Spark为什么比Hadoop速度快?
Hadoop MapReduce需要将每个阶段的中间结果写入磁盘，造成了大量的I/O延迟；而Spark则将中间数据尽可能保留在内存中进行迭代处理，消除了多次读写磁盘的开销，从而实现了比Hadoop快几个数量级的运算速度。
___
### 81. DAG划分Spark源码实现?
Spark通过DAGScheduler对用户提交的作业（Job）进行分析，根据RDD的依赖关系（窄依赖和宽依赖） 将计算链（RDD Lineage）逆向解析成一个由 stages 组成的有向无环图（DAG），其中每个stage包含一系列可以流水线化执行的窄依赖转换，而宽依赖则作为stage的划分边界。
<br>
DAG划分的核心源码实现就是在DAGScheduler.createStages方法中，通过递归地寻找宽依赖来切分Stage，将连续的窄依赖操作合并到一个Stage中，从而优化任务调度和执行效率。
___
### 82. Spark Streaming的双流join的过程，怎么做的?
Spark Streaming的双流Join（如stream1.join(stream2)）基于状态管理和窗口操作实现，其核心是Spark的有状态处理（Stateful Processing）：它会将两个流中需要Join的Key对应的所有批次数据（通常在一个时间窗口内）分别作为状态持久化存储下来（如存入内存或HDFS），每当一个新批次到达时，便将该批次数据与另一个流中已存储的对应Key的状态数据进行关联计算（如内连接、外连接），从而产生完整的Join结果并更新状态。
___
### 83. Spark的Block管理
Spark的Block管理由BlockManager组件提供统一的底层服务，它对集群中所有存储在内存、磁盘或堆外空间的RDD分区（Block）、广播变量及Shuffle数据等逻辑块进行统一抽象与管理；其核心是通过主从架构（Driver端的BlockManagerMaster和每个Executor本地的BlockManager）来跟踪所有Block的元数据（如位置、存储级别），并基于BlockID进行本地或跨节点的块读写、复制与删除，从而为Spark的计算和存储提供高效、可靠的数据存取基础。
<br>
所有数据（如RDD分区、Shuffle中间结果、广播变量等）都被划分为多个Block（数据块）。每个Block都有一个全局唯一的标识符，称为BlockId。Spark为不同类型的数据定义了不同的BlockID,比如RDDBlockID、ShuffleBlockId,BroadcastBlockId
___
### 84. Spark怎么保证数据不丢失
Spark通过其弹性分布式数据集（RDD）的血缘关系（Lineage） 和各种持久化与副本机制来保证数据不丢失：当某个分区的数据因节点故障丢失时，Driver端的DAGScheduler可根据其记录的RDD转换图谱（Lineage，即一系列确定性操作）自动从稳定的数据源（如HDFS）或检查点（Checkpoint）重新计算恢复该分区；此外，通过将RDD持久化（Cache/Persist）到内存或磁盘并配置多副本，以及Shuffle过程中写入磁盘和可选的预写日志（WAL），共同构成了数据丢失的防御体系。
___
### 85. Spark SQL如何使用UDF?
在Spark SQL中，您可以通过spark.udf.register函数将一个用Scala、Java或Python编写的普通函数（例如，一个字符串处理函数）注册到SparkSession的catalog中，从而将其转换为一个可以在SQL语句中像内置函数（如SUM()或SUBSTRING()）一样直接调用的UDF（用户自定义函数），Spark SQL在执行时会自动将您的逻辑分发到集群中的各个Executor上并行运行。
___
### 86. Spark温度二次排序
Spark温度二次排序的核心是创建一个组合键（Composite Key），即将需要首要排序的字段（如日期）和次要排序的字段（如温度）封装到一个自定义Key类中，并为该类实现Ordered接口或提供自定义的Ordering比较器，以定义先按日期升序、再按温度降序的比较逻辑；然后在Shuffle阶段前使用sortByKey或repartitionAndSortWithinPartitions等方法基于这个组合键对数据进行分区和排序，从而在Reduce阶段或后续操作中，相同日期的数据就能按温度高低有序地处理。
```
// 自定义Key类，并实现 Ordered 特质（trait），定义比较逻辑
class TemperatureKey(val date: String, val temp: Int)
  extends Ordered[TemperatureKey] with Serializable {

  // 核心：比较逻辑，先比较date，如果date相同，再按temp降序
  override def compare(that: TemperatureKey): Int = {
    val dateCompare = this.date.compareTo(that.date)
    if (dateCompare != 0) {
      dateCompare // 日期不同，按日期升序
    } else {
      // 日期相同，按温度降序（用 that.temp - this.temp）
      - (this.temp.compareTo(that.temp))
    }
  }

  // 重写hashCode和equals方法，用于分区
  override def hashCode(): Int = (date, temp).##
  override def equals(other: Any): Boolean = other match {
    case that: TemperatureKey => (this.date == that.date) && (this.temp == that.temp)
    case _ => false
  }
}
```
___
### 87. Spark实现wordcount
```scala
// 1. 创建SparkContext（Spark 3.0+ 推荐使用SparkSession）
val spark = SparkSession.builder().appName("WordCount").master("local[*]").getOrCreate()
val sc = spark.sparkContext

// 2. 核心WordCount逻辑（链式编程，一行搞定）
val wordCounts = sc.textFile("path/to/your/textfile.txt") // 读取文本，生成RDD[String]
                  .flatMap(_.split(" "))                  // 将每行拆分成单词，生成RDD[String]
                  .map(word => (word, 1))                 // 将每个单词映射为 (word, 1) 的元组，生成RDD[(String, Int)]
                  .reduceByKey(_ + _)                     // 将相同key（单词）的value（1）相加

// 3. 触发计算并输出结果（Action操作）
wordCounts.collect().foreach(println)
```
输出结果:
```text
(hello,3)
(world,2)
(spark,1)
```

```python
# 1. 导入PySpark并创建SparkContext
from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("WordCount")
sc = SparkContext(conf=conf)

# 2. 核心WordCount逻辑（链式编程）
word_counts = sc.textFile("path/to/your/textfile.txt") \
    .flatMap(lambda line: line.split(" ")) \          # 拆分单词
    .map(lambda word: (word, 1)) \                    # 映射为 (单词, 1)
    .reduceByKey(lambda a, b: a + b)                  # 相同单词计数相加

# 3. 触发计算并输出结果
results = word_counts.collect()
for (word, count) in results:
    print(f"{word}: {count}")

# 4. 停止SparkContext
sc.stop()
```
___
### 88. Spark Streaming怎么实现数据持久化保存?
Spark Streaming通过输出操作（Output Operations） 实现数据持久化保存，其中最常用的是foreachRDD设计模式：开发者在此方法中获取每个批次生成的RDD，然后使用其他API（如Spark SQL、Hadoop FileSystem API或JDBC）将RDD中的数据以原子操作的方式写入外部存储系统（如HDFS、MySQL、HBase、Kafka等），从而确保处理结果的持久化和一致性。
___
### 89. Spark SQL读取文件，内存不够使用，如何处理?
当Spark SQL读取文件内存不足时，核心解决思路是减少单次内存压力：通过选用列式存储格式（如Parquet/ORC）实现按需读取列数据，利用分区和谓词下推跳过无关数据，同时调整Executor内存配置（spark.executor.memory），增加分区数分散处理压力，并避免使用collect()等易导致内存溢出的操作，从而在有限内存资源下高效完成大数据处理。
___
### 90. Spark的lazy体现在哪里?
Spark的lazy（惰性）机制主要体现在转换操作（Transformations）的延迟执行：当用户调用如map、filter、reduceByKey等转换算子时，Spark并不会
立即计算数据，而是将这些操作记录在RDD的血缘关系（Lineage）中，构建一个逻辑执行计划（DAG）；只有当遇到行动操作（Actions）（如collect、count、
saveAsTextFile）时，Spark才会根据整个DAG图生成最优的物理执行计划并触发实际计算，这种设计避免了不必要的中间结果存储、优化了整体执行效率并支持运行时优化。
___
### 91. Spark中的并行度等于什么
Spark中的并行度本质上等于集群中所有Executor的CPU核心总数，它决定了Spark作业同时可以运行的最大任务（Task）数量，具体由spark.default.parallelism参数控制（默认值通常为所有Executor的核心数之和），但最终每个RDD的分区数（Partitions）决定了实际的数据并行处理粒度，用户可通过repartition()等操作调整分区数来改变并行度。
___
### 92. Spark运行时并行度的设署
Spark并行度主要通过三个层级设置：在代码层面使用repartition()或coalesce()方法直接调整RDD/DataFrame分区数；在Shuffle算子中显式指定numPartitions参数（如reduceByKey(_+_, 100)）；在配置层面通过spark.sql.shuffle.partitions（默认200）控制Shuffle后分区数，或用spark.default.parallelism设置全局默认值，其中代码级的显式设置优先级最高。
___
### 93. Spark SQL的数据倾斜
Spark SQL数据倾斜是指在Shuffle过程中，某个或某几个Key对应的数据量远大于其他Key，导致少数Task处理的数据量极大、耗时极长，成为整个作业的性能瓶颈，从而造成资源浪费和作业执行时间显著延长的问题。
___
### 94. Spark的exactly-once
Spark的exactly-once（精确一次）语义是指：在任何故障发生后，Spark都能确保对数据的状态转换操作只被精确地执行一次，即输出结果既不丢失也不重复；这主要通过基于检查点（Checkpointing）和预写日志（WAL）的容错机制，结合幂等性输出和事务性写入（如与Kafka集成时使用偏移量提交和事务协调器）来实现，确保数据从读取、处理到写入外部存储的端到端一致性。
___
### 95. Spark的RDD和partition的联系
RDD（弹性分布式数据集）是Spark的核心数据抽象，代表一个不可变、可分区的数据集合，而Partition（分区）是RDD的基本组成单位和并行计算的基本单元：每个RDD会被划分为多个Partition分布到集群不同节点上，每个Partition对应一个Task并行处理，从而实现了数据分布和计算并行化，RDD的转换操作（如map、filter）会应用到所有Partition上，而宽依赖（如groupByKey）则会导致Partition的重新洗牌（Shuffle）。
___
### 96. spark 3.0特性
Spark 3.0的核心特性聚焦于性能优化与智能化：其革命性特性包括自适应查询执行（AQE）（能在运行时动态优化执行计划，如自动合并Shuffle分区、处理数据倾斜）、动态分区裁剪（DPP）（显著提升星型查询性能）以及加速器感知调度（初步支持GPU），同时提供了更好的ANSI SQL兼容性和Pandas API扩展，使得大规模数据处理更加高效和智能
___
### 97. Spark计算的灵活性体现在哪里
Spark计算的灵活性体现在其多层次的API和统一的引擎架构：它同时提供面向不同场景的RDD（细粒度过程式控制）、DataFrame/SQL（声明式结构化查询）和Streaming（流处理）API，允许开发者根据需求灵活选择编程范式；并且所有计算都可在同一引擎中无缝混合执行（如批流一体），支持多种数据源和丰富的算子，既能进行低级的迭代算法开发，也能执行高级的分布式SQL分析，无需切换框架。
___
### 98. PySpark 中的 worker，怎么和Java程序通信的
PySpark中的Worker（Python进程）与Java程序（JVM）通信是通过基于Socket的二进制协议实现的：当Driver端的Java SparkContext启动后，它会创建一个特殊的Py4J Gateway Server，每个Python Worker进程都会启动一个Py4J Gateway Client，通过TCP socket与JVM进行通信；Python端通过序列化（Pickle）将数据和方法调用转换为二进制流发送给JVM，JVM执行实际计算后同样以二进制格式返回结果，从而实现了跨语言的方法调用和数据交换。
<br>
在JVM中创建：广播变量最初在Driver的JVM中创建和初始化。

序列化与传输：JVM将广播对象序列化，并通过Py4J网关将其传输到Python驱动端。

分发与重建：Python驱动端将序列化后的数据作为普通数据块通过Spark自己的机制分发到各个Executor。每个Executor上的Python Worker进程接收到数据后，会在其附带的本地JVM中反序列化并重建广播对象。

代理访问：当Python代码（如UDF）读取广播变量bc.value时，Python Worker会通过Py4J向本地JVM发送一个请求，本地JVM在其内存中找到真正的Scala/Java对象，调用其方法或获取其值，然后将结果返回给Python进程。