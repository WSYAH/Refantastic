package sout;

import leetcode.groupAnagrams;

import java.io.InputStream;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.Files;
import java.util.List;
import java.util.Scanner;


public class showGroupAnagram {
    public static void main(String[] args) {
        groupAnagrams g = new groupAnagrams();
        try{
            InputStream input = showGroupAnagram.class.getClassLoader()
                    .getResourceAsStream("groupAnagrams.input");

            if (input == null) {
                System.out.println("inputStream is null");
                throw new RuntimeException("inputStream is null");
            }

            String content;
            try (Scanner scanner = new Scanner(input)) {
                content = scanner.hasNext() ? scanner.next() : "";
            }

            // 因为 groupAnagrams.input 文件中的内容是["abc","bcd","cba","cbd"]这种格式的
            // 所以按照 JSON 格式的方式去处理
            content = content.trim().replaceAll("^\\[\"|\"\\]$", "");
            String[] strs = content.split("\",\"");
            System.out.println(strs.length);
            System.out.println(strs[0]);
            List<List<String>> result = g.groupAnagrams(strs);
            Path resourceDir = Paths.get(
                    showGroupAnagram.class.getClassLoader()
                    .getResource("").toURI()
                    );
            Path outPath = resourceDir.resolve("groupAnagrams.output");

            Files.write(outPath, result.toString().getBytes());

        }catch(Exception e){
            System.out.println(e);
        }

    }
}
