import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class ThreeSum {
    public List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        Arrays.sort(nums);
        int n = nums.length;
        if (nums[0] * nums[n-1] > 0) return result;
        for (int i = 0; i < n-2; i++) {
            if (i > 0 && nums[i] == nums[i - 1]) continue;
            if (nums[i] + nums[i + 1] + nums[i + 2] > 0) break;
            int j=i+1, k=n-1;
            while(j < k){
                int sum = nums[i] + nums[j] + nums[k];
                if (sum < 0) {
                    j  += 1;
                }else if (sum > 0) {
                    k -= 1;
                }else{
                    result.add(Arrays.asList(nums[i], nums[j], nums[k]));
                    int tem;
                    tem = nums[j];
                    while(j < k && nums[j] == tem) j += 1;
                    tem = nums[k];
                    while(j < k && nums[k] == tem) k -= 1;
                }
            }
        }
        return result;
    }

    public static void main(String[] args) {
        int[] nums = {1,-1,-1,0};
        ThreeSum threeSum = new ThreeSum();
        System.out.println(threeSum.threeSum(nums));
    }
}
