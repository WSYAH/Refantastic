# 给定一个长度为 n 的整数数组 height 。有 n 条垂线，第 i 条线的两个端点是 (i, 0) 和 (i, height[i]) 。
#
# 找出其中的两条线，使得它们与 x 轴共同构成的容器可以容纳最多的水。
#
# 返回容器可以储存的最大水量。
# 输入：[1,8,6,2,5,4,8,3,7]
# 输出：49
# 解释：图中垂直线代表输入数组 [1,8,6,2,5,4,8,3,7]。在此情况下，容器能够容纳水（表示为蓝色部分）的最大值为 49。
# 示例 2：
#
# 输入：height = [1,1]
# 输出：1
# n == height.length
# 2 <= n <= 105
# 0 <= height[i] <= 104


from typing import List

class Solution:
    def maxArea(self, height: List[int]) -> int:
        # 解法说明：面积最大受边界最低与两边界距离影响，要么使得高度比较高，要么宽度比较宽，可以从两边夹击，先保证宽度，因为夹击都要减宽度，不如从矮墙那里减，
        # 为什么？ 从高墙那里减，不论下一堵墙更高还是更低，那么面积一定比现在的小，更高：高度不变，宽度变小，更低：高度可能不变可能变小，宽度一定变小，面积一定变小。所以既然面积更小，那么就不用考虑参与比较了
        # 可以跳过这种比较。后面可能更大吗？不可能，假如从高墙处往里夹，那么高度已经被矮墙限死了，不可能更高，从高墙夹击的未来所有情况，都比目前更小。
        maxArea = 0
        left,right = 0,len(height) - 1
        # area = min(height[left],[right]) * (right - left) 题目是这个意思，找出其中 area 的最大值
        while left < right:
            maxArea = max(maxArea, min(height[left],height[right]) * (right - left))
            if height[left] > height[right]:
                right -= 1
            else: left += 1

        return maxArea

if __name__ == '__main__':
    s = Solution()
    height = [1,8,6,2,5,4,8,3,7]
    print(s.maxArea(height))
