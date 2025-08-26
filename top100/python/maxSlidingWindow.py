# 给你一个整数数组nums，有一个大小为k的滑动窗口从数组的最左侧移动到数组的最右侧。你只可以看到在滑动窗口内的k个数字。滑动窗口每次只向右移动一位。
#返回滑动窗口中的最大值 。
#
# 示例
# 1：
# 输入：nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3
# 输出：[3, 3, 5, 5, 6, 7]
#
# 示例
# 2：
#
# 输入：nums = [1], k = 1
# 输出：[1]
#
# 提示：
#
# 1 <= nums.length <= 105
# -104 <= nums[i] <= 104
# 1 <= k <= nums.length
from typing import List
# 这里的最佳做法其实是，维护一个有序队列，然后每次窗口最右边的元素作为比较值，队列中小于该值的元素，在之后的窗口永远也不可能为最大值，就可以排除掉了
# 有序队列天然可以找到最大值 deque
class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        if k == 1:
            return nums
        result = []
        nums_scan = dict()
        left = 0
        heaps = [0]
        heap_c = dict()
        for i,n in enumerate(nums):
            heap_push(heaps,n)
            heap_c[n] = heap_c.get(n, 0) + 1
            if i - left + 1 < k:
                continue
            result.append(heaps[1])
            heap_c[nums[left]] -= 1
            while heap_c[heaps[1]] == 0:
                heaps[1] = -100000
                heap_pop(heaps,1)
            left += 1

        return result

def heap_push(nums, num):
    nums.append(num)
    n = len(nums) - 1
    while nums[n] > nums[n // 2] and n > 1:
        nums[n],nums[n//2] = nums[n//2], nums[n]
        n = n // 2

def heap_pop(nums, root):
    left_child = root * 2
    right_child = root * 2 + 1
    n = len(nums) - 1
    if right_child <= n:
        if nums[left_child] > nums[right_child]:
            nums[left_child],nums[root] = nums[root], nums[left_child]
            heap_pop(nums,left_child)
        else:
            nums[right_child],nums[root] = nums[root], nums[right_child]
            heap_pop(nums,right_child)
    else:
        if left_child > n:
            return
        else:
            nums[left_child], nums[root] = nums[root], nums[left_child]


def heapify(nums, root):  # 建一个堆
    left_child = root * 2
    right_child = root * 2 + 1
    if left_child >= len(nums):
        return
    if nums[left_child] > nums[root]:
        nums[root], nums[left_child] = nums[left_child], nums[root]
    heapify(nums,left_child)
    if right_child >= len(nums):
        return

    if nums[right_child] > nums[root]:
        nums[root], nums[right_child] = nums[right_child], nums[root]
    heapify(nums, right_child)


if __name__ == '__main__':
    solution = Solution()
    nums = [1, 3, -1, -3, 5, 3, 6, 7]
    k = 3
    print(solution.maxSlidingWindow(nums,k))
    nums = [1]
    k = 1
    print(solution.maxSlidingWindow(nums,k))