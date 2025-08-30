# 给一个t，然后接下来t行每行有三个输入p，q，k，需要判断p/q 在 k进制下是否是不循环的
# 比如，p=1，q=2，k=10，那么1/2 在十进制下就是0.5，自然是不循环的，可以输出yes
# p=1. q=3，k=10，那么在十进制下就是0.3333..., 无限循环下去了，就需要输出no
# p=3，q=4，k=2,那么在2进制下就是0.11，就不循环，输出yes
# 但是，这里面的p，q，k都可能达到10^18，非常之大
import sys


# 这一道题目我的思路是，将p和q都转换为k进制下的表达，比如 p=3=11(2),q=4=100(2), 所以自然就是0.11
# 那么如何判断是否为无限循环呢，应该求所有约数，但是事实证明这个方法十分麻烦，求所有质因数需要预计算所有质数，不方便

# 先将q、p进行约分，这样p、q就约无可约，之后就不用再考虑p的事儿了，只需要考虑q在k进制下能不能化为1了，不能就是约不了，能就是能约
def change_frac(n: int, k: int):
    w = 0  # 表示权重
    result = 0  # 表示结果
    while n:
        result = result + w * (n % k)
        n = n // k
        w = w + 1
    return result

def gcd(a,b):
    while b != 0:
        a, b = b, a%b
    return a

t = 0

for line in sys.stdin:
    a = line.split()
    print(a)
    if t == 0:
        t = int(a[0])
    else:
        p, q, k = int(a[0]), int(a[1]), int(a[2])
        g = gcd(p,q)
        q_prime = q/g  # 获取最简洁形式的分母
        if q_prime == 1:  # 约分都给你约干净了，肯定不循环了
            print('yes')
            continue

        # 然后就需要求q_prime 与 k的公共质因数了，直到为1为止
        g_kq = gcd(q_prime, k)
        while g_kq != 1:
            while q_prime % g_kq == 0:
                q_prime = q_prime / g_kq
            g_kq = gcd(q_prime, k)

        if q_prime == 1:
            print('yes')
        else:
            print('no')



