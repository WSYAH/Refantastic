# 思路整理：
# 包裹字符串，如果字符串首位与末尾相同，则是包裹字符串
# 求解一个字符串全部子传中多少不是包裹字符串
# 现在这个问题是进阶版
# 对于给定的字符串s， 对每个前缀依次求解，全部非空字符串
# 有多少个不是包裹字符串。

# 输入n ,n的数量接为2*10^5
# 接下来输入一个长度为n的字符串。

# 思路1，暴力求解，因为要求所有子串。
# 思路2，在思路1 的基础上优化，因为后续的子串集合包含前序子串集
# 设结果为result，result[i] 就是第i个字符的求解
# result[i+1] = resullt[i-1] + 以i为结尾的非包裹子串的数量
# 那么可以用字典存储所有字符的个数
import sys

n = int(sys.stdin.readline().strip())
s = sys.stdin.readline().strip()

result = [0] * n
mem = {}
mem[s[0]] = 1
for i in range(1,n):
    result[i] += result[i-1]
    result[i] += (i-mem.get(s[i],0))
    mem[s[i]] = mem.get(s[i],0) + 1

for i in range(n):
    print(result[i])