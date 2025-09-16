# YARN 
### 1. 介绍下YARN
YARN，全称是 Yet Another Resource Negotiator（另一种资源协调者）。它是Hadoop 2.0引入的核心组件，其核心思想是：将Hadoop 1.0中MapReduce引擎负责的【资源管理】和【作业调度/监控】两大功能分离开来，升级成一个通用的、与计算框架无关的集群资源管理和任务调度平台。

___
### 2. YARN有几个模块
ResourceManager、NodeManager、ApplicationMaster 和 Container。  

集群的总指挥或资源大脑。整个集群只有一个Active的RM。

___
### 3. YARN工作机制
___
### 4. YARN有什么优势，能解决什么问题?

YARN将资源管理和数据处理解耦，使Hadoop从一个单一的批处理系统进化成一个通用的“大数据操作系统

___
### 5. YARN容错机制
___
### 6. YARN高可用
ZooKeeper集群健康度：YARN HA强烈依赖于ZooKeeper。必须确保ZooKeeper集群本身是高可用的、稳定的，并且网络连接通畅。

___
### 7. YARN调度器
___
### 8. YARN中Container是如何启动的?
___
### 9. YARN的改进之处，Hadoop3.x相对于Hadoop 2.x?
___
### 10. YARN监控
___
