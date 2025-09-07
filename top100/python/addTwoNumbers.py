# 给你两个非空的链表，表示两个非负的整数。它们每位数字都是按照逆序的方式存储的，并且每个节点只能存储一位数字。
#
# 请你将两个数相加，并以相同形式返回一个表示和的链表。
#
# 你可以假设除了数字0之外，这两个数都不会以0开头。

from typing import Optional
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        carry = 0
        head = ListNode(0)
        c = head
        a = l1
        b = l2
        while a or b:
            if a:
                carry += a.val
                a = a.next
            if b:
                carry += b.val
                b = b.next
            c.next = ListNode(carry % 10)
            carry = carry // 10
            c = c.next
        while carry > 0:
            c.next = ListNode(carry % 10)
            carry = carry // 10
            c = c.next

        return head.next


