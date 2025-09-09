"""给你二叉树的根结点 root ，请你将它展开为一个单链表：

展开后的单链表应该同样使用 TreeNode ，其中 right 子指针指向链表中下一个结点，而左子指针始终为 null 。
展开后的单链表应该与二叉树 先序遍历 顺序相同。"""


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


from typing import Optional
from collections import deque

class Solution:
    def flatten(self, root: Optional[TreeNode]) -> None:
        """
        Do not return anything, modify root in-place instead.
        """
        if root is None or root.left is None and root.right is None:
            return
        dq = deque()
        dq.appendleft(root)
        result = TreeNode()
        ptr = result
        while dq:
            node = dq.popleft()
            if node.right:
                dq.appendleft(node.right)
            if node.left:
                dq.appendleft(node.left)
            ptr.right = node
            ptr = ptr.right
            ptr.left = None
        return result.right

