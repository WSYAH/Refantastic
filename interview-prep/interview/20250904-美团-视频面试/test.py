
# 就是求二叉树的层序遍历
# 代码中已指定的类名、方法名、参数名，请勿修改，直接返回方法规定的值即可

# Definition for a binary tree node.
#  class TreeNode:
#      def __init__(self, val = 0, left = None, right = None):
#          self.val = val
#          self.left = left
#          self.right = right
#
from collections import deque


class Solution:
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        # write your code here.
        if not root:
            return []
        dq = deque()
        dq.append((root, 1))
        result = []
        result.append([root.val])
        tem_r = []
        point = 1
        while dq:
            tem, depth = dq.popleft()
            if depth > point:
                point = depth
                if tem_r:
                    result.append([i for i in tem_r])
                    tem_r = []
            if tem.left:
                tem_r.append(tem.left.val)
                dq.append((tem.left, depth + 1))
            if tem.right:
                tem_r.append(tem.right.val)
                dq.append((tem.right, depth + 1))

        if tem_r:
            result.append([i for i in tem_r])
        return result
