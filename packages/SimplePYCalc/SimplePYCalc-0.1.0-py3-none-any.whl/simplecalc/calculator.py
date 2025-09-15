import math

def add(numbers):
    return sum(numbers)

def subtract(numbers):
    result = numbers[0]
    for num in numbers[1:]:
        result -= num
    return result

def multiply(numbers):
    product = math.prod(numbers)
    return product

def divide(numbers):
    result = numbers[0]
    for num in numbers[1:]:
        if num == 0:
            raise ValueError("Error: Cannot divide by zero.")
        result /= num
    return result

def main():
    print('welcome to the calculator! what operation are you trying to do?')
    print('(a for addition, s for subtraction, m for multiplication, and d for division)')
    
    choose_operation = input().lower().strip()

    try:
        a = int(input('enter how many numbers you have: '))
    except ValueError:
        print("Invalid input. Please enter a whole number.")
        return

    numbers = []
    print('if you are doing division or subtraction put the number in order then put them into the calculator')
    for i in range(a):
        try:
            b = float(input(f'number {i+1}: '))
            numbers.append(b)
        except ValueError:
            print(f"Invalid input. Skipping number {i+1}.")

    if not numbers:
        print("No valid numbers were entered.")
        return

    if choose_operation == 'a':
        result = add(numbers)
        print(f"Result: {result}")
    elif choose_operation == 'm':
        result = multiply(numbers)
        print(f"Result: {result}")
    elif choose_operation == 'd':
        try:
            result = divide(numbers)
            print(f"Result: {result}")
        except ValueError as e:
            print(e)
    elif choose_operation == 's':
        result = subtract(numbers)
        print(f"Result: {result}")
    else:
        print("Invalid operation selected. Please choose 'a', 's', 'm', or 'd'.")

if __name__ == "__main__":
    main()
