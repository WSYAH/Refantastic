# 将两个升序链表合并为一个新的 升序 链表并返回。新链表是通过拼接给定的两个链表的所有节点组成的。
from typing import Optional
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        if list1 is None:
            return list2
        if list2 is None:
            return list1
        a = list1
        b = list2
        if list1.val < list2.val:
            head = list1
            a = a.next
        else:
            head = list2
            b = b.next
        head.next = None
        tail = head
        while a and b:
            if a.val > b.val:
                tail.next = b
                b = b.next
                tail = tail.next
            else:
                tail.next = a
                a = a.next
                tail = tail.next
            tail.next = None

        if a:
            tail.next = a
        if b:
            tail.next = b
        return head

