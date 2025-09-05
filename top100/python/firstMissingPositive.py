# 给你一个未排序的整数数组 nums ，请你找出其中没有出现的最小的正整数。
# 请你实现时间复杂度为 O(n) 并且只使用常数级别额外空间的解决方案。
# 示例
# 1：
# 输入：nums = [1, 2, 0]
# 输出：3
# 解释：范围[1, 2]中的数字都在数组中。
# 示例
# 2：
#
# 输入：nums = [3, 4, -1, 1]
# 输出：2
# 解释：1
# 在数组中，但 2没有。
# 示例
# 3：
#
# 输入：nums = [7, 8, 9, 11, 12]
# 输出：1
# 解释：最小的正数1 没有出现。
# 提示：
# 1 <= nums.length <= 105
# -231 <= nums[i] <= 231 - 1
from typing import List

class Solution:
    def firstMissingPositive(self, nums: List[int]) -> int:
        n = len(nums)
        for i in range(len(nums)):
            while 1<=nums[i]<=n and nums[nums[i-1]] != nums[i]:
                cur = nums[i] - 1
                nums[i], nums[cur] = nums[cur], nums[i]
        for i in range(len(nums)):
            if nums[i] != i+1:
                return i+1

        return len(nums) + 1

if __name__ == '__main__':
    s = Solution()
    print(s.firstMissingPositive([7, 8, 9, 11, 12]))