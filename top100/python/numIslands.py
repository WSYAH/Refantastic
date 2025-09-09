"""给你一个由 '1'（陆地）和 '0'（水）组成的的二维网格，请你计算网格中岛屿的数量。

岛屿总是被水包围，并且每座岛屿只能由水平方向和/或竖直方向上相邻的陆地连接形成。

此外，你可以假设该网格的四条边均被水包围。
输入：grid = [
  ['1','1','1','1','0'],
  ['1','1','0','1','0'],
  ['1','1','0','0','0'],
  ['0','0','0','0','0']
]
输出：1

输入：grid = [
  ['1','1','0','0','0'],
  ['1','1','0','0','0'],
  ['0','0','1','0','0'],
  ['0','0','0','1','1']
]
输出：3

"""

# 这个还有一种算法，就是并查集算法，但是最简单的还是dfs
from typing import List
class Solution:
    def numIslands(self, grid: List[List[str]]) -> int:
        result = 0
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                if grid[i][j] == '1':
                    result += 1
                    self.dfs(grid, i, j)
        return result


    def dfs(self,grid, i,j):
        if grid[i][j] == '1':
            grid[i][j] = '0'
            if i > 0:
                self.dfs(grid, i-1, j)
            if i < len(grid) - 1:
                self.dfs(grid, i+1, j)
            if j > 0:
                self.dfs(grid, i, j-1)
            if j < len(grid[0]) - 1:
                self.dfs(grid, i, j+1)

