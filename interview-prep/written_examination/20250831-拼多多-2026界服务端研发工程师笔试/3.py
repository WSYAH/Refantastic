# 提供A，B两个字符串，仅有a,b两种字符组成，lenA=n, lenB=m,组成一个n*m的矩形。
# 比如 A = aba, B=aaaa,那么就会形成一个矩形C ：
# aaaa
# bbbb
# aaaa
# Cij = Ai and Bj(这里设a=True，b=False） 输入n,m,k(k为子矩形n'*m'的大小,1<=n,m<=10^6）
# 然后再输入两行分别为A和B
# 想要求子矩阵中全是a 的子矩阵的个数，子矩阵覆盖的字符数为k。
# 比如上面的k=4的话，A=aba，B=aaaa，那么答案就是2，如果k=2，那么答案就是6，k=3那么答案就是4
