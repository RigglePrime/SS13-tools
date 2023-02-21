print("Building entrypoint...")

with open("entrypoint.py", "w", encoding="utf-8") as entrypoint,\
     open("ss13_tools/__main__.py", "r", encoding="utf-8") as source:
    # What can I say?
    entrypoint.write(source.read().replace("from .", "from ss13_tools."))
