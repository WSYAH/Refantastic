# 给定一个未排序的整数数组 nums ，找出数字连续的最长序列（不要求序列元素在原数组中连续）的长度。
#
# 请你设计并实现时间复杂度为 O(n) 的算法解决此问题。
# 示例 1：
#
# 输入：nums = [100,4,200,1,3,2]
# 输出：4
# 解释：最长数字连续序列是 [1, 2, 3, 4]。它的长度为 4。
# 示例 2：
#
# 输入：nums = [0,3,7,2,5,8,4,6,0,1]
# 输出：9
# 示例 3：
#
# 输入：nums = [1,0,1,2]
# 输出：3
#
#
# 提示：
#
# 0 <= nums.length <= 105
# -109 <= nums[i] <= 109

# 如下解法已经是 O(N)但是如果想要更快可以将字典替换为集合
from typing import List
class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        is_here = {}
        for num in nums:
            is_here[num] = True
        max_count = 0
        for num in nums:
            if is_here.get(num, False) is True:
                max_count = max(max_count, self.look_after(num, is_here) + self.look_front(num,is_here) + 1)
        return max_count

    def look_front(self,point:int, is_here: dict[int, bool]) -> int:
        count = 0
        while is_here.get(point-1,False) is True:
            is_here[point] = False
            count += 1
            point -= 1
        return count

    def look_after(self, point:int, is_here:dict[int, bool]) -> int:
        count = 0
        while is_here.get(point+1,False) is True:
            is_here[point] = False
            count += 1
            point += 1
        return count


if __name__ == '__main__':
    s = Solution()
    nums = [100,4,200,1,3,2]
    print(s.longestConsecutive(nums))