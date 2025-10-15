import java.util.Arrays;
import java.util.Scanner;

public class StablePartition {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        String line = sc.nextLine();
        Character[] chars = line.chars()
                        .mapToObj(c -> (char)c)
                        .toArray(Character[]::new);
        System.out.println(Arrays.toString(chars));

    }
    public String partition(String s) {
        if (s == null || s.length() == 0) {
            return "";
        }
        char[] arr = s.toCharArray();
        return Arrays.toString(arr);
        
    }
    public void testStream() {
        Scanner sc = new Scanner(System.in);
        String line = sc.nextLine();
        String[] arr = line.split(" ");
        Integer[] arrInt = Arrays.stream(arr).map(Integer::parseInt).toArray(Integer[]::new);
        System.out.println(Arrays.toString(arrInt));
    }

}