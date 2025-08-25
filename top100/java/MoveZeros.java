class MoveZeros {
    public void moveZeroes(int[] nums) {
        int zero = -1;
        for(int i=0; i < nums.length; i++){
            if (nums[i] == 0 && zero == -1){
                zero = i;
                continue;
            }else if(nums[i] != 0 && zero == -1){
                continue;
            }
            if (nums[i] != 0 && i > zero){
                int _ = nums[i];
                nums[i] = nums[zero];
                nums[zero] = _;
                zero = zero + 1;
            }
        }
    }
}