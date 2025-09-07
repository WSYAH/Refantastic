# 给你一个 m 行 n 列的矩阵 matrix ，请按照 顺时针螺旋顺序 ，返回矩阵中的所有元素。
# 输入：matrix = [[1,2,3],[4,5,6],[7,8,9]]
# 输出：[1,2,3,6,9,8,7,4,5]

# 输入：matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]
# 输出：[1,2,3,4,8,12,11,10,9,5,6,7]

from typing import List


class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        n = len(matrix) - 1
        m = len(matrix[0]) - 1
        result = []
        maxlens = (n+1) * (m+1)
        x, y = 0, 0
        a, b = 0, 0
        tox = [0,1,0,-1]
        toy = [1,0,-1,0]
        p = 0
        while len(result) < maxlens:
            result.append(matrix[x][y])

            if (x,y) == (a, m) and p == 0:
                a += 1
                p = (p + 1) % 4
            elif (x,y) == (n, m) and p == 1:
                m -= 1
                p = (p + 1) % 4
            elif (x,y) == (n, b) and p == 2:
                n -= 1
                p = (p + 1) % 4
            elif (x, y) == (a, b) and p == 3:
                b += 1
                p = (p + 1) % 4
            x += tox[p]
            y += toy[p]

        return result

if __name__ == '__main__':
    s = Solution()
    print(s.spiralOrder([[1,2,3,4],[5,6,7,8],[9,10,11,12]]))
