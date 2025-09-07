# 题目解析，给两个数，一个数n，一个数k，对于n，每次变换规则如下：
# 如果 n 为 偶数，那么 n = n / 2
# 如果 n 为 奇数，那么 n = 3 * n + 1
# 这里面的n和k都可能为 10^18，十分大，如果暴力求解肯定超时
# 但是这里，按照这种变换规则来说的话，最后一定是1->4->2->1 循环，看看怎么利用吧
import sys

for line in sys.stdin:
    a = line.strip()
    n, k = int(a[0]), int(a[1])
    while k:
        if n % 2 == 0:
            n = n / 2
        else:
            n = 3 * n + 1
        k -= 1
        if n == 1:
            break
    if k == 0:
        print(n)
    elif k % 3 == 0:
        print(1)
    elif k % 3 == 1:
        print(4)
    elif k % 3 == 2:
        print(2)


