# 给你单链表的头节点 head ，请你反转链表，并返回反转后的链表。

# 输入：head = [1,2,3,4,5]
# 输出：[5,4,3,2,1]

# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
from typing import Optional
class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        a = head
        b = head
        c = None
        while a:
            a = a.next
            b.next = c
            c = b
            b = a
        return c




