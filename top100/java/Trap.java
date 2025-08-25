public class Trap {
    public int trap(int[] height) {
        int result = 0;
        int left = 0;
        int sum_height = 0;
        for(int i=0;i<=height.length-1;i++) {
            sum_height += height[i];
            if(height[i]>=height[left]){
                result += (i - left - 1) * height[left] - sum_height + height[i] + height[left];
                left = i;
                sum_height = height[i];
            }
        }
        int right = height.length-1;
        sum_height = 0;
        for (int i = height.length - 1; i >= 0; i--) {
            sum_height += height[i];
            if(height[i]>=height[right]){
                result += (right - i - 1) * height[right] - sum_height + height[i] + height[right];
                right = i;
                sum_height = height[i];
            }
        }
        if(right < left){
            for(int i=right+1; i<left; i++){
                result -= (height[left] - height[i]);
            }
        }
        return result;
    }

    public static void main(String[] args) {
        Trap trap = new Trap();
        int result = trap.trap(new int[]{4, 2, 0, 3, 2, 5});
        System.out.println(result);
    }
}
