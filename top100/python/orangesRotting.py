"""在给定的 m x n 网格 grid 中，每个单元格可以有以下三个值之一：

值 0 代表空单元格；
值 1 代表新鲜橘子；
值 2 代表腐烂的橘子。
每分钟，腐烂的橘子 周围 4 个方向上相邻 的新鲜橘子都会腐烂。

返回 直到单元格中没有新鲜橘子为止所必须经过的最小分钟数。如果不可能，返回 -1 。

输入：grid = [[2,1,1],[1,1,0],[0,1,1]]
输出：4
输入：grid = [[2,1,1],[0,1,1],[1,0,1]]
输出：-1
解释：左下角的橘子（第 2 行， 第 0 列）永远不会腐烂，因为腐烂只会发生在 4 个方向上。
"""
# 这个显然就是层序遍历
from typing import List
from queue import Queue
class Solution:
    def orangesRotting(self, grid: List[List[int]]) -> int:
        q = Queue()
        t = Queue()
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 2:
                    q.put((i, j))
                    t.put(0)
        result = 0
        while not q.empty():
            i, j = q.get()
            ts = t.get()
            result = max(ts, result)
            if i > 0 and grid[i - 1][j] == 1:
                grid[i - 1][j] = 2
                q.put((i - 1, j))
                t.put(ts + 1)

            if j > 0 and grid[i][j - 1] == 1:
                grid[i][j - 1] = 2
                q.put((i, j - 1))
                t.put(ts + 1)
            if i < len(grid) - 1 and grid[i + 1][j] == 1:
                grid[i + 1][j] = 2
                q.put((i + 1, j))
                t.put(ts + 1)
            if j < len(grid[0]) - 1 and grid[i][j + 1] == 1:
                grid[i][j + 1] = 2
                q.put((i, j + 1))
                t.put(ts + 1)

        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == 1:
                    return -1
        return result

s = Solution()
print(s.orangesRotting([[2,1,1],[1,1,0],[0,1,1]]))