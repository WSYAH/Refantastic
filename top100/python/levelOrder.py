"""给你二叉树的根节点 root ，返回其节点值的 层序遍历 。 （即逐层地，从左到右访问所有节点）。
输入：root = [3,9,20,null,null,15,7]
输出：[[3],[9,20],[15,7]]

"""

from typing import List, Optional
from collections import deque
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        if not root:
            return []
        result = []
        level = 0
        dq = deque()
        dq.append((root, level))
        le = []
        while dq:
            node, l2 = dq.popleft()
            if l2 > level:
                result.append([x for x in le])
                le = [node.val]
                level = l2
            else:
                le.append(node.val)
            if node.left:
                dq.append((node.left, l2 + 1))
            if node.right:
                dq.append((node.right, l2 + 1))

        if le:
            result.append(le)
        return result

