# 题目：有n个节点，1<=n<=100000,  1<=ai<=n,ai表示可以从i到达ai节点。
# 可以（1） i -> ai (2) i->i-1 (3) i->i+1;
# 初始i=1，要求从1到达任意节点最少步行次数。
# 比如n = 3. a = [3,2,3]， 就是说从1可以直接到达3，属于穿越，没有步行，从1->2或者3->2才属于步行。
# 所以结果是[0,1,0].


# 解法思路： 采用双端队列BFS高效处理这种问题
# 遇到权重为0的，推到队列前端，遇到权重为1的，推到队尾。

from collections import deque
import sys

n = sys.stdin.readline().strip()
n = int(n)
a = [0]
a.extend(list(map(int, sys.stdin.readline().split())))
dq = deque()
dist = [1000000 for i in range(n+1)]
dist[1] = 0
dq.append(1)
while dq:
    u = dq.popleft()
    # 先将穿越的节点列出来
    neighbor = a[u]
    while dist[neighbor] > dist[u]:
        dist[neighbor] = dist[u]
        dq.appendleft(neighbor)

    left_neighbor = u - 1
    if left_neighbor > 0 and dist[left_neighbor] > dist[u] + 1:
        dist[left_neighbor] = dist[u] + 1
        dq.append(left_neighbor)

    right_neighbor = u + 1
    if right_neighbor <= n and dist[right_neighbor] > dist[u] + 1:
        dist[right_neighbor] = dist[u] + 1
        dq.append(right_neighbor)
    print(dist[1:])

print(" ".join(map(str, dist[1:])))
