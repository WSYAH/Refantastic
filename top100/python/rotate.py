# 给定一个整数数组 nums，将数组中的元素向右轮转 k个位置，其中 k是非负数。

# 示例
# 1:
#
# 输入: nums = [1, 2, 3, 4, 5, 6, 7], k = 3
# 输出: [5, 6, 7, 1, 2, 3, 4]
# 解释:
# 向右轮转 1步: [7, 1, 2, 3, 4, 5, 6]
# 向右轮转 2步: [6, 7, 1, 2, 3, 4, 5]
# 向右轮转 3步: [5, 6, 7, 1, 2, 3, 4]
# 示例
# 2:
#
# 输入：nums = [-1, -100, 3, 99], k = 2
# 输出：[3, 99, -1, -100]
# 解释:
# 向右轮转1步: [99, -1, -100, 3]
# 向右轮转2步: [3, 99, -1, -100]
#
# 提示：
#
# 1 <= nums.length <= 105
# -231 <= nums[i] <= 231 - 1
# 0 <= k <= 105
#
# 进阶：
#
# 尽可能想出更多的解决方案，至少有三种不同的方法可以解决这个问题。
# 你可以使用空间复杂度为O(1)的原地算法解决这个问题吗？
from typing import List

class Solution:
    def rotate(self, nums: List[int], k: int) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        k = k % len(nums)
        if k == 0:
            return nums
        left1,right1 = 0,len(nums)-1
        left2,right2 = right1 - k + 1, len(nums)-1
        right1 = left2 - 1
        for i in range(left1,(left1+right1+1)//2):
            nums[i], nums[right1 - i + left1] = nums[right1 - i + left1], nums[i]
        print(nums)
        for i in range(left2,(left2+right2+1)//2):
            nums[i], nums[right2 - i + left2] = nums[right2 - i + left2], nums[i]
        print(nums)
        for i in range(0, (len(nums))//2):
            nums[i],nums[len(nums)-i-1] = nums[len(nums)-i-1],nums[i]
        return nums

if __name__ == "__main__":
    s = Solution()
    print(s.rotate([1,2,3,4], 2))

