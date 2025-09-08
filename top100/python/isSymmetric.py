# 给你一个二叉树的根节点 root ， 检查它是否轴对称。
from typing import Optional

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        if root is None or root.left is None and root.right is None:
            return True
        return self.isSymmetric2(root.left,root.right)
    def isSymmetric2(self, root1, root2) -> bool:
        if root1 is None and root2 is None:
            return True
        if root1 is None or root2 is None:
            return False
        if root1.val != root2.val:
            return False
        return self.isSymmetric2(root1.left, root2.right) and self.isSymmetric2(root1.right, root2.left)
