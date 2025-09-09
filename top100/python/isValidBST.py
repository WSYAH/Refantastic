"""给你一个二叉树的根节点 root ，判断其是否是一个有效的二叉搜索树。

有效 二叉搜索树定义如下：

节点的左子树只包含 严格小于 当前节点的数。
节点的右子树只包含 严格大于 当前节点的数。
所有左子树和右子树自身必须也是二叉搜索树。"""

from typing import Optional
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        lower = -(2<<31) - 1
        upper = 2<<31 + 1
        return self.helper(root, lower, upper)
    def helper(self, root, lower, upper) -> int:
        if root is None:
            return True
        if root.val <= lower or root.val >= upper:
            return False

        return self.helper(root.left, lower, root.val) and self.helper(root.right, root.val, upper)