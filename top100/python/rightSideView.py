"""给定一个二叉树的 根节点 root，想象自己站在它的右侧，按照从顶部到底部的顺序，返回从右侧所能看到的节点值。
解释一下题意，就是每一层只能看到一个节点，如果该层最右侧右节点，那么就看到这个节点，取每一层最右侧的节点。
"""
from typing import Optional, List
from collections import deque
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def rightSideView(self, root: Optional[TreeNode]) -> List[int]:
        if not root:
            return []
        dq = deque()
        dq.append((root, 0))
        ptr = 0
        result = []
        tem = []
        while dq:
            node, level = dq.popleft()
            if node.left:
                dq.append((node.left, level + 1))
            if node.right:
                dq.append((node.right, level + 1))
            if level > ptr:
                ptr = level
                result.append([x for x in tem])
                x = []
            tem.append(node.val)

        if tem:
            result.append([x for x in tem])
        re2 = []
        for l in result:
            re2.append(l[-1])
        return re2

