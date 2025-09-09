"""二叉树中的 路径 被定义为一条节点序列，序列中每对相邻节点之间都存在一条边。同一个节点在一条路径序列中 至多出现一次 。该路径 至少包含一个 节点，
且不一定经过根节点。

路径和 是路径中各节点值的总和。

给你一个二叉树的根节点 root ，返回其 最大路径和 。"""


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
from typing import Optional
class Solution:
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        self.max_sum = float('-inf') # 初始化最小，意为小于任何值。
        self.max_gain(root)
        return self.max_sum

    def max_gain(self, root: Optional[TreeNode]) -> int:
        """需要计算以node能向父节点提供的贡献值"""
        if not root:
            return 0
        left = self.max_gain(root.left)
        right = self.max_gain(root.right)
        result = max(0, max(left,right)) + root.val
        if result < 0:
            result = 0
        tem = root.val
        if left > 0:
            tem += left
        if right > 0:
            tem += right
        self.max_sum = max(self.max_sum, tem)
        return result


