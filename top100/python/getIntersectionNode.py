# 给你两个单链表的头节点 headA 和 headB ，请你找出并返回两个单链表相交的起始节点。如果两个链表不存在相交节点，返回 null 。
#
# 图示两个链表在节点 c1 开始相交：

# 输入：intersectVal = 8, listA = [4,1,8,4,5], listB = [5,6,1,8,4,5], skipA = 2, skipB = 3
# 输出：Intersected at '8'
#
# 输入：intersectVal = 2, listA = [1,9,1,2,4], listB = [3,2,4], skipA = 3, skipB = 1
# 输出：Intersected at '2'


# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, x):
#         self.val = x
#         self.next = None
class Solution:
    def getIntersectionNode(self, headA: ListNode, headB: ListNode) -> Optional[ListNode]:
        # 先判长，再判同
        a = headA
        b = headB
        na, nb = 0, 0
        while a:
            na += 1
            a = a.next
        while b:
            nb += 1
            b = b.next

        a = headA
        b = headB
        while na > nb:
            na -= 1
            a = a.next
        while nb > na:
            nb -= 1
            b = b.next

        while a:
            if a == b:
                return a
            a = a.next
            b = b.next
        return None
