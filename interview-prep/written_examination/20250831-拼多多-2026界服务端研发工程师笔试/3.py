# 提供A，B两个字符串，仅有a,b两种字符组成，lenA=n, lenB=m,组成一个n*m的矩形。
# 比如 A = aba, B=aaaa,那么就会形成一个矩形C ：
# aaaa
# bbbb
# aaaa
# Cij = Ai and Bj(这里设a=True，b=False） 输入n,m,k(k为子矩形n'*m'的大小,1<=n,m<=10^6）
# 然后再输入两行分别为A和B
# 想要求子矩阵中全是a 的子矩阵的个数，子矩阵覆盖的字符数为k。
# 比如上面的k=4的话，A=aba，B=aaaa，那么答案就是2，如果k=2，那么答案就是6，k=3那么答案就是4

import sys

# 下面的时间复杂度为O(n+m)
def main():
    n,m,k = map(int,sys.stdin.readline().split())
    A = sys.stdin.readline().strip()
    B = sys.stdin.readline().strip()

    # 处理k为0或超过总面积的情况
    if k == 0 or k > n * m:
        print(0)
        return

    # 预处理字符串A，找出所有连续'a'段及其长度
    segments_A = []
    i = 0
    while i < n:
        if A[i] == 'a':
            start = i
            while i < n and A[i] == 'a':
                i += 1
            length = i - start
            segments_A.append(length)
        else:
            i += 1

    # 预处理字符串B，找出所有连续'a'段及其长度
    segments_B = []
    i = 0
    while i < m:
        if B[i] == 'a':
            start = i
            while i < m and B[i] == 'a':
                i += 1
            length = i - start
            segments_B.append(length)
        else:
            i += 1

    # 如果没有连续的'a'段，则直接返回0
    if not segments_A or not segments_B:
        print(0)
        return

    # 找出k的所有因子对(x, y)，使得x * y = k, x<=n, y<=m
    factors = []
    for x in range(1, min(n, k) + 1):
        if k % x == 0:
            y = k // x
            if y <= m:
                factors.append((x, y))

    total = 0
    # 对于每个因子对(x, y)，统计贡献
    for x, y in factors:
        # 统计A中长度>=x的连续段数量
        count_A = 0
        for seg_len in segments_A:
            if seg_len >= x:
                count_A += (seg_len - x + 1)

        # 统计B中长度>=y的连续段数量
        count_B = 0
        for seg_len in segments_B:
            if seg_len >= y:
                count_B += (seg_len - y + 1)

        total += count_A * count_B

    print(total)


if __name__ == "__main__":
    main()