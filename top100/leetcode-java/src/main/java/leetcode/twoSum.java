package leetcode;

import java.util.Arrays;
import java.util.Comparator;


public class twoSum {
    public int[] twoSum(int[] nums, int target) {
        int[][] indexedNums = new int[nums.length][2];
        for (int i = 0; i < nums.length; i++) {
            indexedNums[i][1] = nums[i];
            indexedNums[i][0] = i;
        }
        // 需要按照第一个比较值进行排序
        Arrays.sort(indexedNums, Comparator.comparingInt(a -> a[1]));
        // 双指针法进行查找处理
        int left = 0, right = indexedNums.length - 1;
        int [] result = new int[2];
        while(left < right){
            if (indexedNums[left][1] + indexedNums[right][1] < target){
                left += 1;
            }
            else if(indexedNums[left][1] + indexedNums[right][1] > target){
                right -= 1;
            }
            else{
                result[0] = indexedNums[left][0];
                result[1] = indexedNums[right][0];
                return result;
            }
        }
        return result;
    }
    public static void main(String[] args) {
        System.out.println(Arrays.toString( new twoSum().twoSum(new int[]{2, 7, 11, 15}, 9)));
    }
}


