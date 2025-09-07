from typing import Optional
"""
给你链表的头节点 head ，每 k 个节点一组进行翻转，请你返回修改后的链表。

k 是一个正整数，它的值小于或等于链表的长度。如果节点总数不是 k 的整数倍，那么请将最后剩余的节点保持原有顺序。

你不能只是单纯的改变节点内部的值，而是需要实际进行节点交换。
"""

# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def reverseKGroup(self, head: Optional[ListNode], k: int) -> Optional[ListNode]:
        if head is None or head.next is None or k == 1:
            return head
        pre = ListNode(0)
        c = pre
        left = head

        ptr = 1
        while left:
            a = left
            b = left.next
            while ptr < k and b:
                a = a.next
                b = b.next
                ptr += 1
            if ptr < k:
                c.next = left
            elif ptr == k:
                a.next = None
                c.next = self.reverse(left)
                c = left
                ptr = 1

            left = b
        return pre.next

    def reverse(self, head: Optional[ListNode]) -> Optional[ListNode]:
        a = head
        pre = ListNode(0)
        c = pre
        while a:
            b = a.next
            a.next = c.next
            c.next = a
            a = b
            c = pre
        return pre.next


if __name__ == '__main__':
    head = ListNode(1)
    head.next = ListNode(2)
    head.next.next = ListNode(3)
    head.next.next.next = ListNode(4)
    head.next.next.next.next = ListNode(5)
    head.next.next.next.next.next = ListNode(6)
    sol = Solution()
    x = sol.reverseKGroup(head, 2)
    while x:
        print(x.val, end=' ')
        x = x.next