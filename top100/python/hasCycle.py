from typing import Optional
# 给你一个链表的头节点 head ，判断链表中是否有环。
# 如果链表中存在环 ，则返回 true 。 否则，返回 false 。

# Definition for singly-linked list.
class ListNode:
    def __init__(self, x):
        self.val = x
        self.next = None

class Solution:
    def hasCycle(self, head: Optional[ListNode]) -> bool:
        a = head
        if head is None or head.next is None:
            return False

        b = head.next
        while b and b != a:
            a = a.next
            b = b.next
            if b is None:
                return False
            b = b.next

        if b is None:
            return False
        return True
