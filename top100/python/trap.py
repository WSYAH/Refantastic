# 给定 n 个非负整数表示每个宽度为 1 的柱子的高度图，计算按此排列的柱子，下雨之后能接多少雨水。
# 输入：height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
# 输出：6
# 解释：上面是由数组[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
# 表示的高度图，在这种情况下，可以接
# 6
# 个单位的雨水（蓝色部分表示雨水）。
# 示例
# 2：
#
# 输入：height = [4, 2, 0, 3, 2, 5]
# 输出：9
#
# 提示：
#
# n == height.length
# 1 <= n <= 2 * 104
# 0 <= height[i] <= 105

from typing import List

class Solution:
    def trap(self, height: List) -> int:
        result = 0
        left = 0
        sum_height = 0
        for i in range(len(height)):
            sum_height += height[i]
            if height[i] >= height[left]:
                result += (i -left - 1) * height[left] - sum_height + height[left] + height[i]
                left = i
                sum_height = height[i]

        right = len(height) - 1
        sum_height = 0
        for i in range(len(height)-1,-1,-1):
            sum_height += height[i]
            if height[i] >= height[right]:
                result += (right - i - 1) * height[right] - sum_height + height[right] + height[i]
                right = i
                sum_height = height[i]
        if right < left:  # 重复计算了
            for i in range(right + 1, left):
                result -= (height[right] - height[i])
        return result

if __name__ == '__main__':
    s = Solution()
    height = [2,0,2]
    print(s.trap(height))