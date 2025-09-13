import time
import sys
print("""# WAP to enter a number from 1 to 7 and display the name of the day. For ex. 1 - Monday, 2 - Tuesday....
num = input("Enter a number from 1 to 7: ")
day = {
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
    "7": "Sunday"
}
# using day dictionary to get the valid result 
if num in day:
    print(day[num])
else:
    print("Invalid input! Please enter a number between 1 and 7.")
""")


print("""# Write a program in Python to calculate the number of digits, alphabets, uppercase and lowercase alphabets and display it.
# Program to count digits, alphabets, uppercase and lowercase alphabets

text = input("Enter a string: ")

digits = 0
alphabets = 0
uppercase = 0
lowercase = 0
symbols = 0

for ch in text:
    if ch.isdigit():
        digits += 1
    elif ch.isalpha():
        alphabets += 1
        if ch.isupper():
            uppercase += 1
        else:
            lowercase += 1
    else:
        symbols += 1

print("Total Alphabets:", alphabets)
print("Uppercase Alphabets:", uppercase)
print("Lowercase Alphabets:", lowercase)
print("Digits:", digits)
print("Symbols:", symbols)
# Example usage:
# Input: "Hello World 123"
# Output:
# Total Alphabets: 10
# Uppercase Alphabets: 2
# Lowercase Alphabets: 8
# Digits: 3""")
def GAY(text, delay=0.0001, pause_after=None, pause_time=0.8):
    line = ""
    for i, char in enumerate(text):
        line += char
        for _ in range(2):  # blink twice per char
            sys.stdout.write("\r" + line + "|")  # with cursor
            sys.stdout.flush()
            time.sleep(0.03)
            sys.stdout.write("\r" + line + " ")  # cursor off
            sys.stdout.flush()
            time.sleep(0.03)

        # pause when reaching the checkpoint
        if pause_after and line == pause_after:
            time.sleep(pause_time)

    sys.stdout.write("\r" + line + " \n")  # finish with clean line

def GAY2():
    while True:
        GAY("Sumit is Gay and Zade is transgender",
                    delay=0.0001,
                    pause_after="Sumit is Gay",
                    pause_time=0.8)
        time.sleep(1)

GAY2()
