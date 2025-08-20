# 给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出 和为目标值 target  的那 两个 整数，并返回它们的数组下标。
#
# 你可以假设每种输入只会对应一个答案，并且你不能使用两次相同的元素。
#
# 你可以按任意顺序返回答案。
# 示例
# 1：
#
# 输入：nums = [2, 7, 11, 15], target = 9
# 输出：[0, 1]
# 解释：因为
# nums[0] + nums[1] == 9 ，返回[0, 1] 。
# 示例
# 2：
#
# 输入：nums = [3, 2, 4], target = 6
# 输出：[1, 2]
# 示例
# 3：
#
# 输入：nums = [3, 3], target = 6
# 输出：[0, 1]
#
# 提示：
#
# 2 <= nums.length <= 10^4
# -109 <= nums[i] <= 10^9
# -109 <= target <= 10^9
# 只会存在一个有效答案

# 想出来一个时间复杂度小于O(n2)的答案

from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        operate_list = sorted(enumerate(nums), key=lambda i: i[1]) # 排序后，那么时间复杂度最多就是 O(nlogn)了
        x,y = (0, len(operate_list)-1)
        while x < y:
            if operate_list[x][1] + operate_list[y][1] < target:
                x += 1
            elif operate_list[x][1] + operate_list[y][1] > target:
                y -= 1
            else:
                return [operate_list[x][0], operate_list[y][0]]
        return []

if __name__ == '__main__':
    result = Solution().twoSum([2, 7, 11, 15], 9)
    print(result)
    result2 = Solution().twoSum([3,2,4], 6)
    print(result2)