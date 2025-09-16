
#
# Note: 类名、方法名、参数名已经指定，请勿修改
#
#
# 
# @param s string字符串  
# @return string字符串
#
class Solution:
    def getLongest(self, s):
        # write code here
        if len(s) == 0:
            return s
        dp = [1 for i in range(len(s))]
        stack = [i for i in range(len(s))]
        maxl = 1
        for l in range(3,len(s)+1,2):
            stack2 = []
            while stack:
                x = stack[-1]
                if x + l - 1 > len(s):
                    stack.pop()
                    continue
                if x - 1 < 0:
                    stack.pop()
                    continue
                if s[x-1] == s[x+l-2]:
                    dp[x-1] = l
                    maxl = l
                    stack2.append(x-1)
                stack.pop()
            stack = [x for x in stack2]
            print(stack,l)
        for i in range(len(s)):
            if dp[i] == maxl:
                return s[i:i+maxl]
        return s[0]
        
        


if __name__ == "__main__":
    s = Solution()
    print(s.getLongest("abcdcba"))


        
