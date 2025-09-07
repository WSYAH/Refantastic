# 给你一个链表，删除链表的倒数第 n 个结点，并且返回链表的头结点

from typing import Optional
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        a = head
        l = 0
        while a:
            a = a.next
            l += 1
        n = l - n + 1
        a = head
        b = head.next
        if n == 1:
            return head.next
        ptr = 2
        while ptr < n:
            a = a.next
            b = b.next
            ptr += 1
        a.next = b.next
        return head
