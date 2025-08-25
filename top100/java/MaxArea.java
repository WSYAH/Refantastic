public class MaxArea {
    public int maxArea(int[] height) {
        int maxArea = 0;
        int left = 0, right = height.length - 1;
        int high,width;
        while(left < right){
            width = right - left;
            if(height[left] < height[right]){
                high = height[left];
                left++;
            }else{
                high = height[right];
                right --;
            }
            maxArea = Math.max(maxArea, width * high);

        }
        return maxArea;
    }
}
