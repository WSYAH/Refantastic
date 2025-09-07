# 给定一个链表的头节点  head ，返回链表开始入环的第一个节点。 如果链表无环，则返回 null。
#
# 如果链表中有某个节点，可以通过连续跟踪 next 指针再次到达，则链表中存在环。 为了表示给定链表中的环，评测系统内部使用整数 pos 来表示链表尾、
# 连接到链表中的位置（索引从 0 开始）。如果 pos 是 -1，则在该链表中没有环。注意：pos 不作为参数进行传递，仅仅是为了标识链表的实际情况。
#
# 不允许修改 链表。

# 先判断有无环，并且记录最初相遇的位置x，一个从x处继续走，一个从head开始走，相遇处就是环入口。
class Solution:
    def detectCycle(self, head: Optional[ListNode]) -> Optional[ListNode]:
        A = head
        if head is None or head.next is None:
            return None
        B = head.next
        while True:
            if B is None or B.next is None:
                return None
            B = B.next.next
            A = A.next
            if A == B:
                break
        B = head
        A = A.next
        while A != B:
            A = A.next
            B = B.next
        return A