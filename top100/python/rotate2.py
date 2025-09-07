# 给定一个 n × n 的二维矩阵 matrix 表示一个图像。请你将图像顺时针旋转 90 度。
#
# 你必须在 原地 旋转图像，这意味着你需要直接修改输入的二维矩阵。请不要 使用另一个矩阵来旋转图像。

# 输入：matrix = [[1,2,3],[4,5,6],[7,8,9]]
# 输出：[[7,4,1],[8,5,2],[9,6,3]]

# 输入：matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]
# 输出：[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]

# 提示：
#
# n == matrix.length == matrix[i].length
# 1 <= n <= 20
# -1000 <= matrix[i][j] <= 1000
from typing import List
# https://boardmix.cn/app/editor/qo7YmiM45dgkBMNRaCqnBg
class Solution:
    def rotate(self, matrix: List[List[int]]) -> None:
        # 顺时针旋转可以拆分成两步走
        # ① 以（0,0）- （n.n)为轴旋转
        # ② 左右旋转
        for i in range(len(matrix)):
            for j in range(i):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
        for i in range(len(matrix)):
            for j in range((len(matrix)) // 2):
                matrix[i][j], matrix[i][len(matrix) - 1 - j] = matrix[i][len(matrix) - 1 - j], matrix[i][j]


if __name__ == '__main__':
    s = Solution()
    x = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]
    s.rotate(x)
    print(x)