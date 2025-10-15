import java.util.Scanner;
import java.util.Arrays;

public class AndbyBit{
    public static void main(String[] args){
        Scanner sc = new Scanner(System.in);
        int n = sc.nextInt();
        int ans = 0;
        int[] a = new int[n];
        while(n>0){
            a[n-1] = sc.nextInt();
            n -= 1;
        }
        Arrays.sort(a);
        int[] bits = new int[32];
        for(int i = 0; i<32;i++){
            bits[i] = 1 << (31 - i);
        }
        
        int left = n-1, right = 0;
        for(int i = 0;i<32;i++){
            int tem = 0;
            int tem2 = left;
            for(int j = left;j>=right;j--){
                if(a[j] & bits[i] != 0){
                    tem += 1;
                }else if(tem == 0){
                    tem2 -= 1;
                    continue;
                }else{
                    break;
                }
            }
            if(tem >= 2){
                left = tem2;
                ans += bits[i];
                right = left - tem + 1;
            }
        }
        System.out.print(ans);

    }
}