# 给你一个字符串 s 、一个字符串t 。返回 s中涵盖t 所有字符的最小子串。如果 s 中不存在涵盖 t 所有字符的子串，则返回空字符串"" 。
# 注意：
#
# 对于t中重复字符，我们寻找的子字符串中该字符数量必须不少于 t 中该字符数量。 如果 s 中存在这样的子串，我们保证它是唯一的答案。
# 示例
# 1：
#
# 输入：s = "ADOBECODEBANC", t = "ABC"
# 输出："BANC"
# 解释：最小覆盖子串 "BANC"包含来自字符串 t 的 'A'、'B' 和 'C'。
# 示例
# 2：
#
# 输入：s = "a", t = "a"
# 输出："a"
# 解释：整个字符串
# s
# 是最小覆盖子串。
# 示例
# 3:
#
# 输入: s = "a", t = "aa"
# 输出: ""
# 解释: t 中两个字符 'a' 均应包含在 s 的子串中，
# 因此没有符合条件的子字符串，返回空字符串。
#
#
# 提示：
#
# m == s.length
# n == t.length
# 1 <= m, n <= 105
# s 和 t由英文字母组成

class Solution:
    def minWindow(self, s: str, t: str) -> str:
        result = ""
        cc = dict()
        for i,c in enumerate(t):
            cc[c] = cc.get(c,0) + 1
        sc = dict()
        left = 0
        for i,c in enumerate(s):
            sc[c] = sc.get(c,0)+1
            flag = True
            for k in cc.keys():
                if cc[k] > sc.get(k,0):
                    flag = False
                    break

            if flag:
                while left <= i:
                    if sc[s[left]] > cc.get(s[left],0):
                        sc[s[left]] -= 1
                        left += 1
                    else:
                        break

                if result == "" or len(result) > i - left + 1:
                    result = s[left:i+1]

        return result

if __name__ == '__main__':
    solution = Solution()
    s = "ADOBECODEBANC"
    t = "ABC"
    print(solution.minWindow(s,t))
    s = 'a'
    t = 'aa'
    print(solution.minWindow(s,t))
