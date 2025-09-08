# 1. 导入PySpark并创建SparkContext
from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("WordCount")
sc = SparkContext(conf=conf)

# 2. 核心WordCount逻辑（链式编程）
word_counts = sc.textFile("./textfile.txt") \
    .flatMap(lambda line: line.split(" ")) \
    .map(lambda word: (word, 1))           \
    .reduceByKey(lambda a, b: a + b)                  # 相同单词计数相加

# 3. 触发计算并输出结果
results = word_counts.collect()
for (word, count) in results:
    print(f"{word}: {count}")

# 4. 停止SparkContext
sc.stop()