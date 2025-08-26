# 给定一个字符串
# s ，请你找出其中不含有重复字符的
# 最长子串的长度。
#
# 示例
# 1:
#
# 输入: s = "abcabcbb"
# 输出: 3
# 解释: 因为无重复字符的最长子串是
# "abc"，所以其长度为
# 3。
# 示例
# 2:
#
# 输入: s = "bbbbb"
# 输出: 1
# 解释: 因为无重复字符的最长子串是
# "b"，所以其长度为
# 1。
# 示例
# 3:
#
# 输入: s = "pwwkew"
# 输出: 3
# 解释: 因为无重复字符的最长子串是
# "wke"，所以其长度为
# 3。
# 请注意，你的答案必须是
# 子串
# 的长度，"pwke"
# 是一个子序列，不是子串。
#
#
# 提示：
#
# 0 <= s.length <= 5 * 104
# s由英文字母、数字、符号和空格组成

class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        result = 0
        item_in_window = set()
        left = 0
        tem_length = 0
        for i,c in enumerate(s):
            tem_length += 1
            if c in item_in_window:
                for j in range(left,i):
                    tem_length -= 1
                    if s[j] != c:
                        item_in_window.remove(s[j])
                        continue
                    else:
                        left = j + 1
                        break
            if c not in item_in_window:
                item_in_window.add(c)

            result = max(result, tem_length)
        return result

if __name__ == "__main__":
    s = Solution()
    st = "pwwkew"
    print(s.lengthOfLongestSubstring(st))
