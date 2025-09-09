"""给定一个二叉搜索树的根节点 root ，和一个整数 k ，请你设计一个算法查找其中第 k 小的元素（从 1 开始计数）。"""

from typing import Optional
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

from collections import deque
class Solution:
    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
        dq = deque()
        while root or dq:
            while root:
                dq.appendleft(root)
                root = root.left
            root = dq.popleft()
            k -= 1
            if k == 0: return root.val
            root = root.right

        return -1


