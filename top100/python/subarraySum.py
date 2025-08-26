# 给你一个整数数组
# nums 和一个整数k ，请你统计并返回 该数组中和为k的子数组的个数。
#
# 子数组是数组中元素的连续非空序列。
# 示例
# 1： 输入：nums = [1, 1, 1], k = 2
# 输出：2
# 示例
# 2：
#
# 输入：nums = [1, 2, 3], k = 3
# 输出：2
#
# 提示：
#
# 1 <= nums.length <= 2 * 104
# -1000 <= nums[i] <= 1000
# -107 <= k <= 107

from typing import List

class Solution:
    def subarraySum(self, nums: List[int], k: int) -> int:
        result = 0
        sum_a = 0
        sum_d = dict()
        sum_d[0] = 1
        for i,c in enumerate(nums):
            sum_a += c
            tok = sum_a - k
            result += sum_d.get(tok,0)
            sum_d[sum_a] = sum_d.get(sum_a,0) + 1
        return result

if __name__ == '__main__':
    solution = Solution()
    nums = [1,2,3]
    k = 3
    print(solution.subarraySum(nums,k))

    with open("input/subarraySum.input", 'r') as file:
        lines = file.readlines()
        nums = eval(lines[0])
        k = int(lines[1])
        print(solution.subarraySum(nums,k))

