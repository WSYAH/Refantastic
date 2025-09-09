"""你这个学期必须选修 numCourses 门课程，记为 0 到 numCourses - 1 。

在选修某些课程之前需要一些先修课程。 先修课程按数组 prerequisites 给出，其中 prerequisites[i] = [ai, bi] ，表示如果要学习课程 ai 则
必须 先学习课程  bi 。

例如，先修课程对 [0, 1] 表示：想要学习课程 0 ，你需要先完成课程 1 。
请你判断是否可能完成所有课程的学习？如果可以，返回 true ；否则，返回 false 。
示例 1：

输入：numCourses = 2, prerequisites = [[1,0]]
输出：true
解释：总共有 2 门课程。学习课程 1 之前，你需要完成课程 0 。这是可能的。
示例 2：

输入：numCourses = 2, prerequisites = [[1,0],[0,1]]
输出：false
解释：总共有 2 门课程。学习课程 1 之前，你需要先完成课程 0 ；并且学习课程 0 之前，你还应先完成课程 1 。这是不可能的。

数量级是5000
"""

from typing import List
from queue import Queue
class Solution:
    def canFinish(self, numCourses: int, prerequisites: List[List[int]]) -> bool:
        preCourse = {}
        q = Queue()
        preNum = {}
        for x,y in prerequisites:
            if y not in preCourse:
                preCourse[y] = []
            preCourse[y].append(x)
            preNum[x] = preNum.get(x, 0) + 1

        for i in range(numCourses):
            if i not in preNum:
                q.put(i)
        while not q.empty():
            course = q.get()
            if course in preCourse:
                for x in preCourse[course]:
                    preNum[x] = preNum.get(x, 0) - 1
                    if preNum[x] == 0:
                        q.put(x)
                        del preNum[x]
        if len(preNum) == 0:
            return True
        return False




