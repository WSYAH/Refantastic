package leetcode;

import java.util.*;

public class groupAnagrams {
    static Map<Character, Integer> charToPrim;
    static{
        charToPrim = getCharToPrim();
    }
    public List<List<String>> groupAnagrams(String[] strs) {
        int[][] sort_list = new int[strs.length][2];
        for (int i = 0; i < strs.length; i++) {
            sort_list[i][0] = stringToInt(strs[i]);
            sort_list[i][1] = i;
        }
        Arrays.sort(sort_list, Comparator.comparingInt(a->a[0]));
        List<List<String>> result = new ArrayList<>();
        List<String> temp = new ArrayList<>();
        int point = -1;
        for(int i=0;i<sort_list.length;i++){
            if (sort_list[i][0] == point){
                temp.add(strs[sort_list[i][1]]);
            }else{
                point = sort_list[i][0];
                if (!temp.isEmpty())
                    result.add(new ArrayList<>(temp));
                temp = new ArrayList<>();
                temp.add(strs[sort_list[i][1]]);
            }
        }
        if (!temp.isEmpty()){
            result.add(temp);
        }
        return result;
    }

    static Integer stringToInt(String str) {
        int mod1= 324161893, mod2 = 706028447;
        long fingernail = 1;
        for(char c: str.toCharArray()){
            fingernail *= charToPrim.get(c);
            fingernail %= mod1;
            fingernail %= mod2;
        }
        return (int)fingernail;
    }
    static Map<Character, Integer> getCharToPrim() {
        Map<Character, Integer> map = new HashMap<>();
        int[] prims = new int[26];
        prims[0] = 2;
        int index = 1, point = 3;
        while(index < 26){
            boolean isPrime = true;
            for(int i=2; i <= Math.sqrt(point); i++){
                if(point % i == 0){
                    isPrime = false;
                    break;
                }
            }
            if (isPrime){
                prims[index] = point;
                index += 1;
            }
            point += 1;
        }
        for(char c='a'; c <= 'z'; c++ ){
            map.put(c, prims[c-'a']);
        }
        return map;
    }
}
