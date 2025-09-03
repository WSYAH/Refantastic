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


# import sys

# x,y,z = map(int,sys.stdin.readline().strip().split())
# mod = 998244353
# result = 0

# if x > z:
#     print(0)

# if (x-1) * y <= z:
#     result += ((z-(y*(x-1))) % mod) * pow(y,x-1,mod)
#     result %= mod


MOD = 998244353

def main():
    import sys
    data = sys.stdin.readline().split()
    X = int(data[0])
    Y = int(data[1])
    Z = int(data[2])
    
    n = X
    m = Y
    M = Z
    
    if M < n:
        print(0)
        return
        
    k = min(M - n, (n - 1) * m)
    
    if k < 0:
        print(0)
        return
        
    max_val = n * m + 1
    dp = [0] * (max_val + 1)
    prefix = [0] * (max_val + 2)
    
    dp[0] = 1
    prefix[1] = 1
    
    for i in range(1, n):
        new_dp = [0] * (max_val + 1)
        for j in range(0, max_val + 1):
            L = max(0, j - m)
            R = j
            total = prefix[R + 1] - prefix[L]
            new_dp[j] = total % MOD
        dp = new_dp
        prefix[0] = 0
        for j in range(0, max_val + 1):
            prefix[j + 1] = (prefix[j] + dp[j]) % MOD
            
    total_ways = 0
    for j in range(0, k + 1):
        total_ways = (total_ways + dp[j]) % MOD
        
    print(total_ways % MOD)

if __name__ == "__main__":
    main()