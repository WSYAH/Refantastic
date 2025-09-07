# 思路整理
# n 条 plog， 每条plog点赞数为ai，内容杂乱度为ci，都是正整数
# 需要分成若干收藏夹，满足
# 每个收藏夹中点赞数量从小到大排序s，s+1，s+2...，s+|s|-1
# 每个收藏夹的杂乱程度取决于该收藏夹中所有ci的最大值。
# 目的是全部收藏夹杂乱度之和最小，并输出该最小值。

# 输入， 第0行 T，T表示测试用例数量，【1，10^4】
# 第一行 n，【1，2*10^5】
# 第二行 n 个正整数a，【1，10^9】
# 第三行 n 个正整数c，【1，10^9】
# 所有n的和不超过2*10^5

# 输出，一个整数，表示最小杂乱度之和
#2
# 6
# 2 2 3 4 3 1
# 3 5 2 6 4 1
# 5
# 5 6 7 8 9
# 5 4 3 2 1
# 输出
# 9
# 5


# 思路，这个就是求所有的ai的最长递增子序列，如果连续，则可以放在一个收藏夹中
# 如果不连续，那么只好分开，混乱度一定增加，如果重叠，那么将最大的混乱度划分到存在更大的混乱度的收藏夹中
# 就是如果重复的ai，如果当前的ci更大，那么就将其划分到前一个收藏夹中，否则就带有小c的ai划分到当前收藏夹中

import sys

t = int(sys.stdin.readline().strip())

while t:
    t -= 1
    n = int(sys.stdin.readline().strip())
    a = list(map(int,sys.stdin.readline().strip().split()))
    c = list(map(int,sys.stdin.readline().strip().split()))
    x = []
    for i in range(n):
        x.append((a[i],c[i]))
    x.sort(key=lambda k:k[0])
