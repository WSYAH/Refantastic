# 给你一个字符串数组，请你将
# 字母异位词
# 组合在一起。可以按任意顺序返回结果列表。
#
#
#
# 示例
# 1:
#
# 输入: strs = ["eat", "tea", "tan", "ate", "nat", "bat"]
#
# 输出: [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]
#
# 解释：
#
# 在
# strs
# 中没有字符串可以通过重新排列来形成
# "bat"。
# 字符串
# "nat"
# 和
# "tan"
# 是字母异位词，因为它们可以重新排列以形成彼此。
# 字符串
# "ate" ，"eat"
# 和
# "tea"
# 是字母异位词，因为它们可以重新排列以形成彼此。
# 示例
# 2:
#
# 输入: strs = [""]
#
# 输出: [[""]]
#
# 示例
# 3:
#
# 输入: strs = ["a"]
#
# 输出: [["a"]]
#
# 提示：
#
# 1 <= strs.length <= 104
# 0 <= strs[i].length <= 100
# strs[i]
# 仅包含小写字母
#
from math import sqrt


class Solution(object):
    # 先说思想，采取质数唯一分解来定义字符串的指纹，将字母映射成一个数字，比如说质数，比如 a=3，b=5，那么 ab=15，aab=45，baa=45，
    # 就可以判断 baa==aab，无视字母顺序了，当然，a!=b,因为 3！=5，可以避免不同字符组合的字符串相等
    def groupAnagrams(self, strs):
        """
        :type strs: List[str]
        :rtype: List[List[str]]
        """
        map = Solution.getPrim()
        sort_list = [(s, Solution.str2int(s,map)) for s in strs]
        sort_list.sort(key=lambda x:x[1])
        result = []
        tem = []
        point = 1
        for i in range(len(sort_list)):
            if sort_list[i][1] == point:
                tem.append(sort_list[i][0])
            else:
                point = sort_list[i][1]
                if tem:
                    result.append([x for x in tem])
                tem = [sort_list[i][0]]
        if tem:
            result.append([x for x in tem])
        return result

    # 生成质数序列，只需要26个就可以了
    @staticmethod
    def getPrim():
        map = {}
        strings = 'abcdefghijklmnopqrstuvwxyz'
        prims = [2,3]
        count_prims = 2
        point_integer = 5
        while count_prims <= 26:
            flag = True
            for x in range(2, int(sqrt(point_integer))+1):
                if point_integer % x == 0:
                    flag = False
                    break
            if flag:
                prims.append(point_integer)
                count_prims += 1
            point_integer += 2

        for i,s in enumerate(strings):
            map[s] = prims[i]
        return map

    @staticmethod
    def str2int(strr, map):
        mod1 = 324161893  # 这两个质数还是挺关键的，一开始采用 10^7+7 依然会出现重复
        mod2 = 706028447
        result = 1
        for s in strr:
            result *= map[s]
            result = result % mod1
            result = result % mod2
        return result


if __name__ == '__main__':
    strs = ["eat", "tea", "tan", "ate", "nat", "bat"]
    solution = Solution()
    print(solution.groupAnagrams(strs))
    # with open("groupAnagrams.input", "r") as file:
    #     strr = eval(file.read())
    # result = solution.groupAnagrams(strr)
