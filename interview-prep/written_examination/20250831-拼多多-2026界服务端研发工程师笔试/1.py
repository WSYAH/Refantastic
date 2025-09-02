# 可选时间1-H，要求找出所有不繁忙的时间总和，比如[10,20]下雨，[15.25]有活动，则[10,25]区间时间不可选。
# 输入： 1<=T <=10, H 为总时间，1<=H<=10^9，N为不可选时间段的个数，最大可100000，接下来N行每行各两位数字 xi,yi 作为不可选时间的开始与结束。
#
#
# #coding=utf-8
# # 本题为考试多行输入输出规范示例，无需提交，不计分。
# import sys
# if __name__ == "__main__":
#     # 读取第一行的n
#     n = int(sys.stdin.readline().strip())
#     ans = 0
#     for i in range(n):
#         # 读取每一行
#         line = sys.stdin.readline().strip()
#         # 把每一行的数字分隔后转化成int列表
#         values = list(map(int, line.split()))
#         for v in values:
#             ans += v
#     print(ans)

# 这一题可以先排序，然后合并重叠区间，然后遍历就可以了，计算所有没有覆盖的间隙，可以用H-所有覆盖区间时长。
# 但是Python会超时，只能过85%左右的测试用例，最好还是使用C++/Java。
# C++ 安装与使用参考： https://blog.csdn.net/qq_42417071/article/details/137438374
