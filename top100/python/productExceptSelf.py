# 给你一个整数数组nums，返回数组answer ，其中 answer[i]等于 nums 中除 nums[i]之外其余各元素的乘积 。
#
# 题目数据保证数组 nums之中任意元素的全部前缀元素和后缀的乘积都在 32 位整数范围内。
#
# 请不要使用除法，且在O(n)时间复杂度内完成此题。
# 示例
# 1:
#
# 输入: nums = [1, 2, 3, 4]
# 输出: [24, 12, 8, 6]
# 示例
# 2:
#
# 输入: nums = [-1, 1, 0, -3, 3]
# 输出: [0, 0, 9, 0, 0]
#
# 提示：
#
# 2 <= nums.length <= 105
# -30 <= nums[i] <= 30
# 输入 保证 数组answer[i] 在 32 位整数范围内
#
# 进阶：你可以在O(1)的额外空间复杂度内完成这个题目吗？（ 出于对空间复杂度分析的目的，输出数组 不被视为额外空间。）
from typing import List

class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        result = [1 for i in range(len(nums))]
        pre = 1
        for i in range(0, len(nums)):
            result[i] *= pre
            pre *= nums[i]
        post = 1
        for i in range(len(nums) - 1, -1, -1):
            result[i] *= post
            post *= nums[i]
        return result


if __name__ == "__main__":
    solution = Solution()
    print(solution.productExceptSelf(nums=[1, 2, 3, 4 ]))