"""
给你链表的头结点 head ，请将其按 升序 排列并返回 排序后的链表 。
"""
from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    # 适合链表排序的算法就是归并排序
    def sortList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if head is None or head.next is None:
            return head
        left = head
        right = head.next
        while right and right.next:
            left = left.next
            right = right.next.next
        right = left.next
        left.next = None

        left_list = self.sortList(head)
        right_list = self.sortList(right)

        return self.merge(left_list, right_list)

    def merge(self, leftNode: ListNode, rightNode: ListNode) -> ListNode:
        pre = ListNode()
        ptr = pre
        while leftNode and rightNode:
            if leftNode.val <= rightNode.val:
                ptr.next = leftNode
                leftNode = leftNode.next
                ptr = ptr.next
            else:
                ptr.next = rightNode
                rightNode = rightNode.next
                ptr = ptr.next
        while leftNode:
            ptr.next = leftNode
            leftNode = leftNode.next
            ptr = ptr.next
        while rightNode:
            ptr.next = rightNode
            rightNode = rightNode.next
            ptr = ptr.next
        return pre.next

if __name__ == '__main__':
    head = ListNode(-1)
    head.next = ListNode(5)
    head.next.next = ListNode(3)
    head.next.next.next = ListNode(4)
    head.next.next.next.next = ListNode(0)
    head.next.next.next.next.next = ListNode(6)
    sol = Solution()
    x = sol.sortList(head)
    while x:
        print(x.val, end=' ')
        x = x.next