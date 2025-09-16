# HBase
### 1. 介绍下HBase 
你可以把它理解为 一个构建在 Hadoop HDFS 之上的“哈希表”，能够存储数十亿行、数百万列的超大规模数据集。

支持高并发、低延迟的随机读写操作。这得益于其 LSM-Tree 的存储结构和内存缓存机制。
___
### 2. HBase优缺点
___
3. 说下HBase原理
___
4. 介绍下HBase架构
___
5. HBase读写数据流程
___
6. HBase的读写缓存
___
7. 在删除HBase中的一个数据的时候，它什么时候真正的进行删除呢?当你进行删除操作，它是立马就把数据删除掉了吗?
___
8. HBase中的二级索引
___
9. HBase的RegionServer宕机以后怎么恢复的?
___
10. HBase的一个region由哪些东西组成?
___
11. HBase高可用怎么实现的?
___
### 12. 为什么HBase适合写多读少业务?

核心原因：LSM树 (Log-Structured Merge-Tree)
LSM树的设计哲学是：将大量的随机写入转换为顺序写入，从而极大提升写入吞吐量。
___
13. 列式数据库的适用场景和优势?列式存储的特点?
___
14. HBase的rowkey设计原则
___
15. HBase的rowkey为什么不能超过一定的长度?为什么要唯一?rowkey太长会影响Hfile的存储是吧?
___
16. HBase的RowKey设置讲究有什么原因
___
17. HBase的大合并、小合并是什么?
___
18. HBase和关系型数据库(传统数据库)的区别(优点)?
___
19. HBase数据结构
___
20. HBase为什么随机查询很快?
___
21. HBase的LSM结构
___
22. HBase的Get和Scan的区别和联系?
___
23. HBase数据的存储结构(底层存储结构)
___
24. HBase数据compact流程?
___
25. HBase的预分区
___
26. HBase的热点问题
___
27. HBase的memstore冲刷条件
___
28. HBase的MVCC
___
29. HBase的大合并与小合并，大合并是如何做的?为什么要大合并
___
30. 既然HBase底层数据是存储在HDFS上，为什么不直接使用HDFS，而还要用HBase
___
31. HBase和Phoenix的区别
___
32. HBase支持SQL操作吗
___
33. HBase适合读多写少还是写多读少
___
34. HBase表设计
___
35. Region分配
___
36. HBase的Region切分
___
