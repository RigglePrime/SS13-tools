# LogBuddy

- [LogBuddy](#logbuddy)
  - [Currently supported log files](#currently-supported-log-files)
  - [Quick start](#quick-start)
    - [Quick start (for real this time)](#quick-start-for-real-this-time)
    - [Available commands (cheat sheet)](#available-commands-cheat-sheet)
  - [How it works (for nerds)](#how-it-works-for-nerds)
    - [Example](#example)
    - [Cheat sheet (for nerds)](#cheat-sheet-for-nerds)
  - [Running](#running)

This tool is "actively" being developed! Make sure to check for updates from time to time, they might add a cool feature!

LogBuddy is a helper tool for reading log files. It has features to:

- combine multiple log files
- sort them however you want
- filter out logs by who performed the action, where it happened
- filter out logs that a person couldn't have heard or seen
- work with multiple filters (filter the filtered output)
- write the resulting set to a file

## Currently supported log files

- game.txt
- attack.txt
- pda.txt
- silicon.txt
- virus.txt
- paper.txt
- mecha.txt
- telecomms.txt
- uplink.txt
- shuttle.txt

## Quick start

Remember, if you ever screw an input up try pressing the up arrow. The commands below have `%` in front
of them, but you don't have to use it. Instead of `%dl` try typing `dl`.

As said [below](#how-it-works-for-nerds) this is an IPython shell. If you need to calculate something,
just input it. For example try typing in `5 + 3` and you'll see the result. If you know some Python I
will encourage you to read the aforementioned section, as you can run arbitrary Python code and customise
everything.

As everything is happening in the console you can't CTRL+C to copy. Instead select what you want to copy
with your mouse, and just right click anywhere. To paste, make sure nothing is selected and right click.

### Quick start (for real this time)

So you've got an annoying appeal with a lot of investigation? You've come to the right place! I'm hoping
that at the end of this short section you'll know how to use LogBuddy pretty effectively.

After starting it, the first thing you need to do is download some logs.

`%dl 198563`

And that's it! Look at [this section](#available-commands-cheat-sheet) for more ways to download logs.
You can input several rounds, or even a range. If you want to load them from an already existing file,
use `%load_file`

Now let's filter them. Let's say our friend `lootgoblin614` got into a fight. They claim to have been
insulted by someone, so it would be useful to see who they spoke with.

`%heard lootgoblin614` should display only logs they heard. `%p` to print the logs, `%s` to save and
we're done! Doens't work? First, let's reset the filter with `%reset`. If we know they fought in
the bar, we can try `%location Bar` (use full location names), and printing that out. We could also
just filter for ckeys with `%ckey lootgoblin614 barenjoyer999` to get logs from only those two.
For the full list of commands, see [available commands](#available-commands-cheat-sheet)

When you're done just type `%s` to save to a file, and you're all done. Good luck with the appeal!

### Available commands (cheat sheet)

All commands here start with `%`
([IPython magics](https://ipython.readthedocs.io/en/stable/interactive/magics.html)),
but you can skip it (automagic is on).

- `%download` (alias `%dl`)
  - `%download 198563`: download round 198563
  - `%dl 198563`: same as above
  - `%download 199563-199999`: download rounds 199500 to 199600 (inclusive). Be careful with this,
  as downloading and loading more than 100 rounds may slow down your computer by a lot.
  - `%download 198563 198565 198569 198570`: download rounds 198563, 198565, 198569 and 198570.
  You can run this command with as many rounds as you want.
  - `%download 198563, 198565, 198569, 198570` same as before (you can use commas too!)
- `%load_file`: loads logs from a file
  - `%load_file logs.log`
- `%save` (alias `%s`): saves logs to a file. This will **overwrite** your files, be careful
  - `%save` (saves it to the default location, `logs.log`)
  - `%save some_other_file.log`
  - `%save WindowSmasher appeal.txt`
  - `%s`
  - `%s cool_file.txt`
- `%length` (alias `%l`): prints the amount of log lines we loaded into memory
  - `%length`
  - `%l`
- `%search_ckey` (alias `%ckey`): searches the logs for the ckeys. This is not the same
as CTRL+F, as it looks at who commited the action
  - `%ckey WindowSmasher86` (only logs `WindowSmasher86` was included in)
  - `%search_ckey WindowSmasher86` (same as above)
  - `%search_ckey ckey1 ckey2` (union, or better known as logs from both people)
  - `%search_ckey ckey1 ckey2 ckey3`
  - `%search_ckey ckey1, ckey2, ckey3`
  - You can have as many as you want
- `%search_string` (alias `%string`): literally just CTRL+F, case insensitive
  - `%string help maint`
  - `%string security`
  - `%string thank you very much!`
- `%heard`: tries to exclude the logs that the person provided couldn't have heard
  - `%heard WindowSmasher86`
- `%conversation`: tries to reconstruct a "conversation". It's like heard but for multiple people
  - `%conversation ckey`
  - `%conversation ckey1 ckey2`
  - Same as `%search_ckey`
- `%reset`: removes all filters
  - `%reset`
- `%location` (alias `%loc`): filters by location. For example, you can get all logs that happened
in the bar.
  - `%location Bar`
  - `%location Medbay Central` (you must provide the whole name)
- `%radius`: sorts the logs by time. You don't need to call this as they're automatically sorted
  - `%radius 50 62 2 10` (x=50, y=60, z=2, radius=10)
- `%type`: filters by log type. To get all types, type `LogType.list()`
  - `%type GAME ATTACK` (inclusion)
  - `%type !SILICON` (exclusion, just append `!`)
- `%print_logs` (alias `%p`): prints the logs
  - `%print_logs`
  - `%p`
- `%head`: pritns the first few logs
  - `%head`
  - `%head 20` (print 20 instead of the default)
- `%tail`: same as head, but from the other side
  - `%tail`
  - `%tail 20`
- `%clear`: USE WITH CAUTION: **deletes** currently stored logs. After using this, there's no
going back.
- `%sort`: sorts the logs by time. You don't need to call this as they're automatically sorted
  - `%sort`
- `%lsmagic`: list all commands available. A lot are built in, so be careful!

## How it works (for nerds)

Before starting going forward you should look at how the application looks. Oddly familiar, right? It's
because it's exactly what you think it is, an embedded [IPython](https://ipython.org/) shell. It's a Python
shell but better! The same thing Jupyter notebooks use. What this means is you can run arbitrary Python code!
You can interact with all available modules and create custom code.

The above commands are called IPython magics. They integrate pretty well with the shell. For more info
see [this file](log_magics.py)

When starting the application with command line parameters (if you don't know what those are skip this),
a variable called `logs` is created, which contains all lines from all log files provided, sorted by time.
Any function called accesses and modifies the `logs` variable of your `logs` (confusing, I know), so you
may chain multiple functions. To reset the work set and remove all filters, call `logs.reset_work_set()`.

### Example

In this example it's assumed you ran the application with no command line arguments (double clicking
on the executable). To copy something, select it and right click. Topaste it, right click with nothing
selected. This can unfortunately not be changed as it's a Windows quirk. For different functionality,
run this from a different command prompt like Windows Terminal.

At any point feel free to type `help` for general help, or `help(thing)` for help with that specific
thing (for example `help(LogFile)`).

First, we download (there is an easier alternative, keep reading) our logs to a folder. Let's name the
folder `logs`. The folder will be in the same parent folder as the executable (or script), so we don't
have as much to type. For this example feel free to download as many (or just one!) supported log files
as you'd like. The list of supported files is just above.

As an alternative you can use `my_logs = LogFile.from_round_id(180150)`
This will automatically download all available log files.

You can also use `LogFile.from_round_range`, or `LogFile.from_round_collection`. Looking at the docstrings
should help you understand how they operate.

To load the whole folder (and save the result to a variable), we use `my_logs = LogFile.from_folder("logs")`.
If your logs folder is somewhere else, just type out the whole absolute or relative paths (for example, `../logs/`).
To load just one file, use `my_logs = LogFile.from_file("game.txt")` (assuming you want to load game.txt).
You can later add another file by doing `another_log = LogFile.from_file("attack.txt")`. To combine them use
`my_logs.collate(another_log)`. This will modify `my_logs` to incorporate the other log object's logs.

The variable name completely depends on you, you can pick any name you want (usually all lowercase with
underscores instead of spaces). Just don't forget to replace `my_logs` with your name.

When loading logs you may see some errors. It's usually fine to ignore them, unless there's many of them.
Sometimes there are strange and uncommon ways to log things, and it's hard to account for all of them.

Before getting started you may want to see some stats. To see the amount of log lines loaded, run
`len(my_logs)` (or `logs` if you're using the default variable). To see the list of all
players that connected during that round, you can run `my_logs.who`, or `len(my_logs.who)` for the
number of players that have connected.

Now that we have a log file ready, let's filter it. We want to find out if someone has been running
around and destroying windows. Firstly, let's filter out only their ckey like so
`my_logs.filter_ckeys("WindowSmasher32")` (sidenote: notice the s in ckeys. This means you can filter
for multiple: `my_logs.filter_ckeys("WindowSmasher32", "FireaxeLover2", "CoolCkey53")`. We can view
the result by calling `my_logs.print_working()`. We're not done yet, we can go further than this. Let's
filter out everything (in the result), that doesn't contain a window. To do this, we can call
`my_logs.filter_strings("window")`. This works a lot like CTRL + F. To write our result to a file, we
can use `my_logs.write_working_to_file("logs.txt")`, which will write our working set to `logs.txt`.

But why not just use a text editor for this? Here's why. Let's say someone's been lying, and you want to
know if they heard someone say something. You could either go searching by hand, or call
`my_logs.filter_heard("Liar54")`. It doesn't work perfectly, but it's better than not having it, right?
To reduce our work set further, we can call the same functions as before.

This is only the surface of what you can do. Python knowledge comes in handy here. Since this is a
Python interpreter running in the background, you can do anything you would in Python. Run a file,
write a custom sort function, the world's your oyster!

### Cheat sheet (for nerds)

- `my_logs = LogFile.from_file("game.log")`: import game.log and save to `my_logs`
- `my_logs = LogFile.from_folder("logs")`: open folder logs, import all log files and save to `my_logs`
- `my_logs = LogFile.from_logs_link("https://tgstation13.org/parsed-logs/terry/data/logs/2022/03/01/round-179256/")`:
open link, get all known files, parse them and save them to `my_logs`
- `my_logs.filter_conversation("ckey1", "ckey2")`: get instances where ckey1 and ckey2 probably interacted
- `my_logs.filter_by_location_name("Pharmacy")`: only logs that happened in pharmacy
- `my_logs.filter_by_radius((32, 41, 2), 5)`: logs that happened 5 or less tiles away from (32, 41, 2)
- `my_logs.filter_ckeys("ckey1", "ckey2")`: actions that ckey2 or ckey2 performed (can be as many ckeys as you want)
- `my_logs.filter_heard("ckey")`: removes logs that ckey couldn't have heard or seen
- `my_logs.filter_strings("injected", "ckey1")`: works like CTRL+F but with multiple strings (as many as you want)
- `my_logs.filter_strings("injected", "ckey1", case_sensitive=True)`: same as above but case sensitive
- `my_logs.filter_strings_case_sensitive("injected", "ckey1")`: same as above
- `my_logs.reset_work_set()`: remove all filters
- `my_logs.head()` or `my_logs.head(10)`: prints the first 10 log entries
- `my_logs.tail()` or `my_logs.tail(10)`: prints the last 10 log entries
- `my_logs.sort()`: sorts the logs (usually called automatically, sorted by time)
- `my_logs.write_working_to_file("file.log")`: writes filtered logs to `file.log`
- `my_logs.print_working()`: prints all filtered logs

## Running

Download [this executable](https://github.com/RigglePrime/LogBuddy/releases/latest) OR

Quick tip: the colours on your terminal might not look that great, especially if you're using Windows.
I strongly suggest running it with Windows Terminal, as it has MUCH nicer colours. Simply download it
(I'm sure you can figure out how to do that), open the Terminal (try right clicking near the executable,
you may get an option to "open in Windows Terminal", if not use "`cd <directory>`, or `cd ..` to go back),
and run the executable from there (type the name out).

Using Python Poetry:

- `poetry install`
- `python -m ss13_tools.log_buddy`

Optionally:

- `python -m ss13_tools.log_buddy logs`, where `./logs/` is a folder that contains logs (all will
be parsed)

I recommend creating a virtual environment, but it's not necessary. If you don't
know how to do it, you probably don't need to worry about it. If you run into
strange issues, start worrying about it.

Optionally, you can provide a log file, or folder with multiple log files.
The script will automatically load those in. You also manually do it later.
