# 给你一个整数数组
# nums ，判断是否存在三元组[nums[i], nums[j], nums[k]]
# 满足
# i != j、i != k
# 且
# j != k ，同时还满足
# nums[i] + nums[j] + nums[k] == 0 。请你返回所有和为
# 0
# 且不重复的三元组。
#
# 注意：答案中不可以包含重复的三元组。
#
# 示例
# 1：
#
# 输入：nums = [-1, 0, 1, 2, -1, -4]
# 输出：[[-1, -1, 2], [-1, 0, 1]]
# 解释：
# nums[0] + nums[1] + nums[2] = (-1) + 0 + 1 = 0 。
# nums[1] + nums[2] + nums[4] = 0 + 1 + (-1) = 0 。
# nums[0] + nums[3] + nums[4] = (-1) + 2 + (-1) = 0 。
# 不同的三元组是[-1, 0, 1]
# 和[-1, -1, 2] 。
# 注意，输出的顺序和三元组的顺序并不重要。
# 示例
# 2：
#
# 输入：nums = [0, 1, 1]
# 输出：[]
# 解释：唯一可能的三元组和不为
# 0 。
# 示例
# 3：
#
# 输入：nums = [0, 0, 0]
# 输出：[[0, 0, 0]]
# 解释：唯一可能的三元组和为
# 0 。
#
#
# 提示：
#
# 3 <= nums.length <= 3000
# -105 <= nums[i] <= 105

from typing import List

# 思路如下： 遍历正负，然后二分找第三个数。
# 二分找第三个数也有讲究，比如 0位在 x 处，那么正负分别在 x+i 与 x-j 处，那么第三者一定在 （x-j、x+i）之外，因为里面的一定已经处理过
# 其实组合数也才4,495,501,000个，直接在所有的情况中查找应该不行。
class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        result = []
        nums.sort()
        left,right = 0, len(nums) - 1
        if nums[0] * nums[right] > 0:
            return []
        for i in range(right-1):

            if i > 0 and nums[i-1] == nums[i]:  # 不加这个就容易出现重复，因为以相同元素开头的所有情况已经囊括在上一次循环中了
                continue
            if nums[i] + nums[i+1] + nums[i+2] > 0:  # 当扫描到 0 界点就不用再扫描了
                break
            j, k = i+1, right
            while j < k:
                s = nums[i]+ nums[j] + nums[k]
                if s > 0:
                    k -= 1
                    continue
                if s < 0:
                    j += 1
                    continue
                if s == 0:
                    result.append([nums[i], nums[j], nums[k]])

                    tem = nums[j]
                    j += 1
                    while j < k and nums[j] == tem:
                        j += 1
                    tem = nums[k]
                    while k > j and nums[k] == tem:
                        k -= 1
        return result

if __name__ == "__main__":
    s = Solution()
    nums = [-1,-1,0,1]
    print(s.threeSum(nums))



        



