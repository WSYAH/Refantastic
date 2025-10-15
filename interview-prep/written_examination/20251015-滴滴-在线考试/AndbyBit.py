import sys

n = int(sys.stdin.readline().strip())
a = [0 for i in range(n)]
for i in range(n):
    a[i] = int(sys.stdin.readline().strip())

a.sort(reverse =True)
bits = [1 << (30 - i) for i in range(31)]
left = 0
right = n - 1
ans = 0
for i in range(31):
    tem = 0
    tem2 = left
    for j in range(left, right + 1):
        if a[j] & bits[i] != 0:
            tem += 1
        elif tem == 0:
            tem2 += 1
        else:
            break
    if tem >= 2:
        left = tem2
        ans += bits[i]
        right = left + tem - 1

print(ans)
