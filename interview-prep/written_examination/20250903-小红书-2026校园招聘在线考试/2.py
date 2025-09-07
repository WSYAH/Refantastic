# 思路整理
# 题目表意为连续X天签到积分制度。
# 签到规则：
# 1. 第i天签到获得积分ai （0，Z]
# 2. 从第2天开始，积分要严格递增，但是增量不能超过Y。

# 要计算a序列的符合条件的所有可能的总数。对mod取模。
# mod = 998244353

# 输入描述： 在一行中输入3个数字X,Y，Z。 X,Y的范围为[1,10^6] Z的范围是[10^12,10^18]。

# 输出描述： 输出符合条件的a序列的总数对998244353取模的结果。

# 3 2 4
# 输出： 4
# 提示，q^-1 mod p = p ^ (p-2) mod p
# 2 6 1145140
# 6870819
# 方案1： dfs搜索，一定会超时。
# 方案2： 也不能用动态规划，x太大了。看错了，x是10的6次方，如果线性dp是可行的。仔细想了不合适
# 方案3： 尝试数字归纳法，这个应该可以。
# 方案4： 纯模拟，如果XY<=Z,那么结果
# 方法思路
# 问题分析：我们需要生成一个长度为X的序列a，其中每个元素ai满足0 < a1 ≤ Z，且对于i从2到X，有a_{i-1} < a_i ≤ a_{i-1} + Y。这可以转化为组合数学问题，通过计算满足条件的序列数目。
#
# 关键 insight：将序列转换为差分序列，其中差分值d_i = a_i - a_{i-1}满足1 ≤ d_i ≤ Y。问题转化为计算这些差分序列的和以及对应的a1的选择数目。
#
# 组合数学：使用容斥原理来计算满足条件的差分序列数目，并通过预计算组合数来高效求解。对于X较小的情洀直接计算，对于X较大的情况采用更高效的算法（如Chirp-Z变换），但本实现主要处理X较小的情况。
#
# 模运算处理：由于结果需要对998244353取模，我们使用模逆元来处理组合数中的除法运算。




MOD = 998244353


def main():
    import sys
    data = sys.stdin.readline().split()
    X = int(data[0])
    Y = int(data[1])
    Z = int(data[2])

    # 如果只有一天，直接返回Z，因为积分可以是1到Z的任意值
    if X == 1:
        print(Z % MOD)
        return

    # n表示差分的数量（X-1个差分）
    n = X - 1
    # 如果Z小于n，无法形成序列，输出0
    if Z < n:
        print(0)
        return

    # K是容斥求和中参数t的最大值，取n*(Y-1)和Z-n的最小值
    K = min(n * (Y - 1), Z - n)
    if K < 0:
        print(0)
        return

    # max_i是容斥求和中i的最大值
    max_i = min(n, K // Y)

    # 预计算阶乘和逆阶乘，用于计算组合数
    max_k = n + 1
    fact = [1] * (max_k + 1)
    for i in range(1, max_k + 1):
        fact[i] = fact[i - 1] * i % MOD

    inv_fact = [1] * (max_k + 1)
    inv_fact[max_k] = pow(fact[max_k], MOD - 2, MOD)
    for i in range(max_k, 0, -1):
        inv_fact[i - 1] = inv_fact[i] * i % MOD

    # 计算组合数C(m, k) mod MOD
    def nCr(m, k):
        if k < 0 or k > m:
            return 0
        if k == 0:
            return 1
        num = 1
        for i in range(0, k):
            num = num * (m - i) % MOD
        return num * inv_fact[k] % MOD

    # S1和S2用于容斥求和
    S1 = 0
    S2 = 0
    for i in range(0, max_i + 1):
        # 计算m_val = K - i*Y + n
        m_val = K - i * Y + n
        # 计算term1：C(n, i) * C(m_val, n)
        term1 = nCr(n, i) * nCr(m_val, n) % MOD
        # 如果i为奇数，取负值
        if i % 2 == 1:
            term1 = (-term1) % MOD
        S1 = (S1 + term1) % MOD

        # 计算S2的部分：i*Y * C(m_val, n) 和 n * C(m_val, n+1)
        part1 = i * Y % MOD * nCr(m_val, n) % MOD
        part2 = n * nCr(m_val, n + 1) % MOD
        term2 = nCr(n, i) * (part1 + part2) % MOD
        if i % 2 == 1:
            term2 = (-term2) % MOD
        S2 = (S2 + term2) % MOD

    # 最终答案：(Z - n) * S1 - S2
    ans = ((Z - n) * S1 - S2) % MOD
    if ans < 0:
        ans += MOD
    print(ans)


if __name__ == "__main__":
    main()


# 代码详细解释
# 输入处理：读取输入的X、Y和Z值。
#
# 特殊情况处理：如果X为1，直接输出Z mod MOD，因为只有一天签到，积分可以是1到Z的任意值。
#
# 差分数量计算：n = X - 1，表示有n个差分值（每个差分值代表相邻两天的积分差）。
#
# 可行性检查：如果Z小于n，输出0，因为无法形成严格递增序列。
#
# 参数K计算：K是容斥求和中参数t的最大值，取n*(Y-1)和Z-n的最小值。这是因为t（差分值的和）受限于Y和Z。
#
# 预计算阶乘和逆阶乘：为了高效计算组合数，预计算阶乘数组fact和逆阶乘数组inv_fact。
#
# 组合数计算函数nCr：计算组合数C(m, k) mod MOD，使用预计算的阶乘和逆阶乘。
#
# 容斥求和：
#
# S1：计算所有有效差分序列的数目之和。
#
# S2：计算所有有效差分序列的t（差分和）之和。
#
# 通过循环i从0到max_i，应用容斥原理，计算每个i的贡献。
#
# 最终答案计算：答案表示为(Z - n) * S1 - S2，并对结果取模确保非负。
#
# 输出结果：打印最终答案。
#
# 这种方法通过组合数学和容斥原理高效地计算出满足条件的序列数目，适用于X和Y较大而Z非常大的情况。
