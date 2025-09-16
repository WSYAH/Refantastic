def main():
    import sys
    n = int(sys.stdin.readline().strip())
    A = list(map(int, sys.stdin.readline().strip().split()))
    B = list(map(int, sys.stdin.readline().strip().split()))

    sequences = []

    def generate_sequences(op1_count, op2_count, seq, sequences):
        if op1_count == n and op2_count == n:
            sequences.append(seq[:])
            return
        if op1_count < n:
            generate_sequences(op1_count + 1, op2_count, seq + [0], sequences)
        if op2_count < op1_count:
            generate_sequences(op1_count, op2_count + 1, seq + [1], sequences)

    generate_sequences(0, 0, [], sequences)

    total_profit = 0
    for seq in sequences:
        stack = []
        current_index = 0
        profit = 0
        for op in seq:
            if op == 0:
                stack.append(A[current_index])
                current_index += 1
            else:
                x = len(stack)
                y = stack.pop()
                profit += y * B[x - 1]
        total_profit += profit

    print(total_profit)


if __name__ == "__main__":
    main()