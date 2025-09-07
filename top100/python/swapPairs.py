from typing import Optional
# 给你一个链表，两两交换其中相邻的节点，并返回交换后链表的头节点。你必须在不修改节点内部的值的情况下完成本题（即，只能进行节点交换）。
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if head is None or head.next is None:
            return head

        a = head
        b = head.next
        pre = ListNode(0)
        c = pre

        while b:
            c.next = b
            a.next = b.next
            b.next = a
            c = a
            a = a.next
            b = None
            if a:
                b = a.next
        return pre.next
