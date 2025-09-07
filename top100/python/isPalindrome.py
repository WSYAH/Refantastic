# 给你一个单链表的头节点 head ，请你判断该链表是否为回文链表。如果是，返回 true ；否则，返回 false 。
# 输入：head = [1,2,2,1]
# 输出：true

# 输入：head = [1,2]
# 输出：false


from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        if head is None or head.next is None:
            return True
        a = head
        result = []
        while a:
            result.append(a.val)
            a = a.next
        return result == result[::-1]
