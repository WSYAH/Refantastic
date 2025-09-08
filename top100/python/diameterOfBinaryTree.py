"""给你一棵二叉树的根节点，返回该树的 直径 。

二叉树的 直径 是指树中任意两个节点之间最长路径的 长度 。这条路径可能经过也可能不经过根节点 root 。

两节点之间路径的 长度 由它们之间边数表示。"""

from typing import Optional
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def __init__(self):
        self.max_depth = 0
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:
        self.dfs(root)
        return self.max_depth

    def dfs(self, node: Optional[TreeNode]) -> int:
        if node is None:
            return 0
        left_depth,right_depth = 0, 0
        if node.left is not None:
            left_depth = self.dfs(node.left) + 1
        if node.right is not None:
            right_depth = self.dfs(node.right) + 1

        self.max_depth = max(self.max_depth, left_depth + right_depth)
        return max(left_depth, right_depth)


