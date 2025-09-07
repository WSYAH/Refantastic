
"""请你设计并实现一个满足  LRU (最近最少使用) 缓存 约束的数据结构。
实现 LRUCache 类：
LRUCache(int capacity) 以 正整数 作为容量 capacity 初始化 LRU 缓存
int get(int key) 如果关键字 key 存在于缓存中，则返回关键字的值，否则返回 -1 。
void put(int key, int value) 如果关键字 key 已经存在，则变更其数据值 value ；如果不存在，则向缓存中插入该组 key-value 。如果插入操作
导致关键字数量超过 capacity ，则应该 逐出 最久未使用的关键字。
函数 get 和 put 必须以 O(1) 的平均时间复杂度运行。
"""
# 可以使用双向链表和 哈希表来维护
class DLinkNode:
    def __init__(self, key=0, value=None):
        self.key = key
        self.value = value
        self.next: DLinkNode = None
        self.prev: DLinkNode = None

class LRUCache:

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.head = DLinkNode()
        self.tail = DLinkNode()
        self.head.next = self.tail
        self.tail.prev = self.head

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self.move_to_front(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.move_to_front(self.cache[key])
            self.cache[key].value = value
        else:
            self.cache[key] = DLinkNode(key, value)
            node = self.cache[key]
            node.prev = self.head
            node.next = self.head.next
            self.head.next.prev = node
            self.head.next = node
            if len(self.cache) > self.capacity:
                rm_node = self.tail.prev
                self.cache.pop(rm_node.key)
                self.tail.prev = rm_node.prev
                rm_node.prev.next = self.tail


    def move_to_front(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
        self.head.next.prev = node
        node.next = self.head.next
        self.head.next = node
        node.prev = self.head

# Your LRUCache object will be instantiated and called as such:
# obj = LRUCache(capacity)
# param_1 = obj.get(key)
# obj.put(key,value)