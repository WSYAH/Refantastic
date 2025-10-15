//  javac -encoding UTF-8 .\StreamExample.java
//  java StreamExample

import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;

public class StreamExample {
    public static void main(String[] args) {
        String str = "Hello World";
        Character[] chars = str.chars()  //这个实际上利用了String底层的char[]数组，存储的都是ASCII码
                                .mapToObj(c ->(char)c)  //  将int类型的ASCII码转换成char
                                .toArray(Character[]::new);  //  将char[]数组转换成Character[]数组,定义一个长度为0的Char数组实际上是声明是Character类型的数组
                                // 为什么 new Character[0] 不行呢，因为这里的Stream需要一个 IntFunction<A[]>，也就是一个 "输入数组长度，输出数组对象" 的函数。
                                // 但是 new Character[0] 返回的是 Object[]，而Character[]::new 相当于size -> new Character[size]，返回的是 Character[]，可以看做一个lambda函数
        System.out.println(Arrays.toString(chars));
    }
}