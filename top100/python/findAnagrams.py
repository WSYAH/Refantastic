# 给定两个字符串 s 和 p，找到 s 中所有 p 的异位词的子串，返回这些子串的起始索引。不考虑答案输出的顺序。
#
# 示例
# 1:
#
# 输入: s = "cbaebabacd", p = "abc"
# 输出: [0, 6]
# 解释:
# 起始索引等于0的子串是 "cba", 它是
# "abc"的异位词。起始索引等于6的子串是 "bac", 它是"abc" 的异位词。
# 示例2:
#
# 输入: s = "abab", p = "ab"
# 输出: [0, 1, 2]
# 解释:
# 起始索引等于0 的子串是 "ab", 它是 "ab" 的异位词。 起始索引等于 1 的子串是 "ba", 它是 "ab" 的异位词。
# 起始索引等于2 的子串是 "ab", 它是 "ab" 的异位词。
#
#
# 提示:
#
# 1 <= s.length, p.length <= 3 * 104
# s
# 和
# p
# 仅包含小写字母
from typing import List

class Solution:
    def findAnagrams(self, s: str, p: str) -> List[int]:
        result = []
        charz: dict = dict()
        chars: dict = dict()
        for c in range(ord('a'),ord('z')+1):
            charz[chr(c)] = 0
            chars[chr(c)] = 0

        for i,c in enumerate(p):
            charz[c] = charz[c] + 1
        left = 0
        for i,c in enumerate(s):
            chars[c] += 1
            if i - left + 1 < len(p):
                continue
            flag = True
            for k in charz.keys():
                if charz[k] != chars[k]:
                    print(k,chars[k],charz[k])
                    flag = False
                    break

            if flag:
                result.append(left)

            chars[s[left]] -= 1
            left += 1

        return result

if __name__ == '__main__':
    solution = Solution()
    s = "abab"
    p = "ab"
    print(solution.findAnagrams(s,p))

