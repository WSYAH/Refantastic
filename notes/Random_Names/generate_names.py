import random
import pandas as pd


def generate_names():
    firstName = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻水云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳鲍史唐费岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅卞齐康伍余元卜顾孟平"
    famale = "秀娟英华慧巧美娜静淑惠珠翠雅芝玉萍红娥玲芬芳燕彩春菊兰凤洁梅琳素云莲真环雪荣爱妹霞香月莺媛艳瑞凡佳嘉琼勤珍贞莉桂娣叶璧璐娅琦晶妍茜秋珊莎锦黛青倩婷姣婉娴瑾颖露瑶怡婵雁蓓纨仪荷丹蓉眉君琴蕊薇菁梦岚苑婕馨瑗琰韵融园艺咏卿聪澜纯毓悦昭冰爽琬茗羽希宁欣飘育滢馥筠柔竹霭凝晓欢霄枫芸菲寒伊亚宜可姬舒影荔枝思丽"
    male = "伟刚勇毅俊峰强军平保东文辉力明永健世广志义兴良海山仁波宁贵福生龙元全国胜学祥才发武新利清飞彬富顺信子杰涛昌成康星光天达安岩中茂进林有坚和彪博诚先敬震振壮会思群豪心邦承乐绍功松善厚庆磊民友裕河哲江超浩亮政谦亨奇固之轮翰朗伯宏言若鸣朋斌梁栋维启克伦翔旭鹏泽晨辰士以建家致树炎德行时泰盛雄琛钧冠策腾楠榕风航弘"

    firstname = random.choice(firstName)

    sex = random.choice([0,1])

    if sex == 0:
        name = random.choices(famale, k=random.choices([1,2], weights=[0.1,0.9])[0])
    else:
        name = random.choices(male, k=random.choices([1,2], weights=[0.1,0.9])[0])

    return firstname + ''.join(name), ['女','男'][sex]

def generate_birthday(min_age=18, max_age=60):
    import datetime

    year = datetime.datetime.now().year
    mouth = datetime.datetime.now().month
    day = datetime.datetime.now().day

    age = random.choice(range(min_age, max_age + 1))

    mouth = random.choice(range(1, 13))
    day = random.choice(range(1, 32))

    return year - age, mouth, day


def main():
    
    column1 = []
    column2 = []
    column3 = []
    column4 = []
    column5 = []

    for i in range(10000):
        name, sex = generate_names()
        year, mouth, day = generate_birthday()

        column1.append(name)
        column2.append(sex)
        column3.append(year)
        column4.append(mouth)
        column5.append('')

    data = {
        '序号': column5,
        "姓名": column1,
        "性别": column2,
        "出生年": column3,
        "出生月": column4,
    }

    df = pd.DataFrame(data)
    df.to_excel("人员信息表.xlsx", index=False)


if __name__ == '__main__':
    main()



    
    