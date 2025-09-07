# 面经

大数据或者特征工程的话，尽可能的去了解：https://developer.aliyun.com/live/254684?spm=a2c6h.12873639.article-detail.26.7c357098KwZ2am
另外，Python - Java 在执行特征任务的时候，如何从定义视图-执行的。以及如何实现交互的，交互的话离不开剪枝，也就是 prune，将 pipeline-dag-目标节点-祖先节点保留-其他节点不要-dag-pipeline。
对于 Spark 任务来说，传输 broadcastvalue 可以通过pyspark 的 session 传输，比较简单，但是我们没有 pyflink，使用的是原生的 Flink，那么就需要使用https://github.com/alibaba/pemja，实际上也是 Flink 的实现
在 python 中定义的 udf，怎么注册的。但是我们并不想让用户都用 python 去定义，因为不好管理，我们不知道他的逻辑。我们更倾向于将一些 udf 的共性逻辑抽取出来，然后通过算子去实现它。