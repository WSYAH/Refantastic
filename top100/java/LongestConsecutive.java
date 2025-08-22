import java.util.HashSet;
import java.util.Set;

public class LongestConsecutive {
    public int longestConsecutive(int[] nums) {
        Set<Integer> set = new HashSet<>();
        for(int num:nums){
            set.add(num);
        }
        int max = 0;
        for (int num : set) {
            if(!set.contains(num-1)){
                int cur = num + 1;
                    while(set.contains(cur)){
                        cur += 1;
                    }
                    max = Math.max(max, cur-num);
            }
        }
        return max;
    }
}
