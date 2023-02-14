import sys

from .slur_detector import SlurDetector


if len(sys.argv) == 2:
    file_name: str = sys.argv[1]
else:
    file_name = input("File name: ")
slur_search = SlurDetector.from_file(file_name)
slur_search.print_results()
