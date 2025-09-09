"""给定一个二叉树的根节点 root ，和一个整数 targetSum ，求该二叉树里节点值之和等于 targetSum 的 路径 的数目。

路径 不需要从根节点开始，也不需要在叶子节点结束，但是路径方向必须是向下的（只能从父节点到子节点）。"""

from typing import Optional

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
# 树上前缀和，每个节点到root节点的前缀
class Solution:
    def pathSum(self, root: Optional[TreeNode], targetSum: int) -> int:
        if root is None:
            return 0
        sumMap = {}
        sumMap[0] = 1
        return self.dfs(root, 0, sumMap, targetSum)


    def dfs(self, root, current_sum, sumMap, targetSum):
        if root is None:
            return 0
        current_sum += root.val
        count = sumMap.get(current_sum - targetSum, 0)
        sumMap[current_sum] = sumMap.get(current_sum, 0) + 1 # 这一句一定要在上一句之后
        count += self.dfs(root.left, current_sum, sumMap, targetSum)
        count += self.dfs(root.right, current_sum, sumMap, targetSum)

        sumMap[current_sum] = sumMap.get(current_sum) - 1
        if sumMap[current_sum] == 0:
            del sumMap[current_sum]
        return count



