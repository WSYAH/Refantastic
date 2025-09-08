# 给你一棵二叉树的根节点 root ，翻转这棵二叉树，并返回其根节点。

# 就是根节点与所有子树的左右子节点交换
# Definition for a binary tree node.

from typing import List, Optional
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        if root is None or root.left is None and root.right is None:
            return root
        root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)
        return root