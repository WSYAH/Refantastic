# 给定一个二叉树的根节点 root ，返回 它的 中序 遍历 。


from typing import Optional, List
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        result = []
        self.inorder(root,result)
        return result
    def inorder(self, root, result):
        if root == None:
            return
        self.inorder(root.left, result)
        result.append(root.val)
        self.inorder(root.right, result)