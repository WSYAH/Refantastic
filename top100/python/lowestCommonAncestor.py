"""给定一个二叉树, 找到该树中两个指定节点的最近公共祖先。

百度百科中最近公共祖先的定义为：“对于有根树 T 的两个节点 p、q，最近公共祖先表示为一个节点 x，满足 x 是 p、q 的祖先且 x 的深度尽可能大
（一个节点也可以是它自己的祖先）。”

"""


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None
from collections import deque
class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode', q: 'TreeNode') -> 'TreeNode':
        stack1 = deque()
        stack2 = deque()
        self.dfs(root,stack1, stack2,  p, q)
        while len(stack1) > len(stack2):
            stack1.popleft()
        while len(stack2) > len(stack1):
            stack2.popleft()
        while stack1[0] != stack2[0]:
            stack2.popleft()
            stack1.popleft()
        return stack1[0]

    def dfs(self, root, stack1: deque, stack2, target1, target2):
        if stack1 and stack1[0] == target1 and stack2 and stack2[0] == target2:
            return
        # root 不可能=None
        if not stack1 or stack1[0] != target1:
            stack1.appendleft(root)
        if not stack2 or stack2[0] != target2:
            stack2.appendleft(root)
        if root.left:
            self.dfs(root.left, stack1, stack2, target1, target2)
        if root.right:
            self.dfs(root.right, stack1, stack2, target1, target2)
        if stack1[0] != target1:
            stack1.popleft()
        if stack2[0] != target2:
            stack2.popleft()






