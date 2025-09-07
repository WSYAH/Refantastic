# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
from typing import Optional, List
"""给你一个链表数组，每个链表都已经按升序排列。

请你将所有链表合并到一个升序链表中，返回合并后的链表。"""
class Solution:

    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        n = len(lists)
        if n == 0:
            return None
        if n == 1:
            return lists[0]
        if n == 2:
            return self.merge(lists[0], lists[1])

        left = self.mergeKLists(lists[:n//2])
        right = self.mergeKLists(lists[n//2:])
        return self.merge(left, right)



    def merge(self, head1: Optional[ListNode], head2: Optional[ListNode]) -> Optional[ListNode]:
        pre = ListNode(0)
        ptr = pre
        while head1 and head2:
            if head1.val < head2.val:
                ptr.next = head1
                head1 = head1.next
            else:
                ptr.next = head2
                head2 = head2.next
            ptr = ptr.next

        ptr.next = head1 if head1 else head2

        return pre.next


if __name__ == '__main__':
    head1 = ListNode(1)
    head1.next = ListNode(4)
    head1.next.next = ListNode(5)
    head2 = ListNode(1)
    head2.next = ListNode(3)
    head2.next.next = ListNode(4)
    head3 = ListNode(2)
    head3.next = ListNode(5)
    sol = Solution()
    x = sol.mergeKLists([head1,head2,head3])
    while x:
        print(x.val, end=' ')
        x = x.next