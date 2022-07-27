#!/env/python3

from candy_stalker import interactive
from slur_detector import SlurDetector

choice = input("""Welcome to trainer suite! What would you like to do?

1. Download someone's say history
2. Run slur detection
3. All of the above
""")

try:
    if choice == "1":
        interactive()
    elif choice == "2":
        SlurDetector.from_file(input("Which file? ")).print_results()
    elif choice == "3":
        ckey, number_of_rounds, output_path, only_played = interactive()
        print()
        slurs = SlurDetector.from_file(output_path)
        slurs.print_results()
    else:
        print("Invalid choice")

finally:
    input("Press return to exit...")
