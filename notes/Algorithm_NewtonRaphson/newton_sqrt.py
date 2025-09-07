import sys

epsilon = 0.0000001  # 判断是否收敛的标志


def sqrt_newton(n: float) -> float:
    if n == 0:
        return 0.0
    if n < 0:
        raise ValueError("n is negative")
    max_iter = 50  # 默认迭代50次
    # 首先用二分法逼近真正的解
    left = 0
    right = n
    while left < right:
        mid = (left + right) // 2
        if mid * mid == n:
            return mid
        if mid * mid > n:
            right = mid - 1
        else:
            left = mid + 1

    x = left
    for _ in range(max_iter):
        next_x = 0.5 * (x + n / x)
        if abs(next_x - x) < epsilon:
            return next_x  # 判断是否收敛
        x = next_x
    return x


if __name__ == "__main__":
    n = float(sys.stdin.readline().strip())
    print(sqrt_newton(n))
