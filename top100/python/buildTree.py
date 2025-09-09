"""给定两个整数数组 preorder 和 inorder ，其中 preorder 是二叉树的先序遍历， inorder 是同一棵树的中序遍历，请构造二叉树并返回其根节点。


"""

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

from typing import List, Optional
class Solution:
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
       return self.helper(preorder, inorder)
    def helper(self, preorder, inorder):
        if len(inorder) == 0:
            return None
        root = TreeNode(preorder[0])
        x = inorder.index(preorder[0])
        left = self.helper(preorder[1:x+1], inorder[:x])
        right = self.helper(preorder[x+1:], inorder[x+1:])
        root.left = left
        root.right = right
        return root
