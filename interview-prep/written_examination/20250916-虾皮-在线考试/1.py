
#
# Note: 类名、方法名、参数名已经指定，请勿修改
#
#
# 
# @param s string字符串  
# @return int整型
#
class Solution:
    def MinOperations(self, s) :
        # write code here
        pt,pr = 0,1
        chose = 'AB'
        r1,r2 = 0
        for c in s:
            if c != chose[pt]:
                r1 += 1
            if c != chose[pr]:
                r2 += 1
            pr,pt = pt,pr
        
        return min(r1,r2)


if __name__ == "__main__":
    s = Solution()
    print(s.MinOperations('ABAA'))