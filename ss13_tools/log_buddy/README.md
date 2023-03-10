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

<font size="4">[**Click me and get started immediately**](#quick-start)</font>

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

Remember, if you ever screw an input up, try pressing the up arrow. The commands below have `%` in front
of them, but you don't always have to use it. Instead of `%dl` try typing `dl`. If you get an invalid
syntax error, try doing it with `%`.

As said [below](#how-it-works-for-nerds), this is an IPython shell. If you need to calculate something,
just input it. For example try typing in `5 + 3` and you'll see the result. If you know some Python I
will encourage you to read the aforementioned section, as you can run arbitrary Python code and customise
everything.

As everything is happening in the console you can't CTRL+C to copy. Instead select what you want to copy
with your mouse, and just right click anywhere. To paste, make sure nothing is selected and right click.
You can browse your command history with the up and down key, tab shows suggestions and autocompletes,
holding control will advance the position by a word instead of a letter. If you see greyed out suggestions,
pressing the right arrow (or CTRL+→) will automatically enter new characters.

### Quick start (for real this time)

So you've got an annoying appeal with a lot of investigation? You've come to the right place! I'm hoping
that at the end of this short section you'll know how to use LogBuddy pretty effectively.

<font size="4">[**Click me for guides based on real world scenarios**](../../logbuddy_guides/README.md)</font>

After starting it, the first thing you need to do is download some logs.

`%dl 198563`

And that's it! Look at [this section](#available-commands-cheat-sheet) for more ways to download logs.
You can input several rounds, or even a range. If you want to load them from an already existing file,
use `%load_logs`

Now let's filter them. Let's say our friend `lootgoblin614` got into a fight. They claim to have been
insulted by someone, so it would be useful to see who they spoke with.

`%heard lootgoblin614` should display only logs they heard. `%p` to print the logs, `%s` to save or
`%clip` to copy to clipboard and we're done! If you make a mistake just `%undo`. Doesn't work?
First, let's reset the filter with `%reset`. If we know they fought in the bar, we can try
`%location Bar` (use full location names), and printing that out. We could also just filter for
ckeys with `%ckey lootgoblin614 barenjoyer999` to get logs from only those two. For the full list
of commands, see [available commands](#available-commands-cheat-sheet)

**Caution:** before using ckey search, verify nothing broke by typing `logs.who`. If you see strange
ckeys, something probably broke and this might be unreliable. You can still use it normally if your
target's ckey is only shown once (or if you input all of their different ckeys shown there).
if not, use the `%string` search instead.

When you're done just type `%s` to save to a file, and you're all done. Good luck with the appeal!

### Available commands (cheat sheet)

All commands here start with `%`
([IPython magics](https://ipython.readthedocs.io/en/stable/interactive/magics.html)),
but you can skip it (automagic is on).

- `%download` (alias `%dl`)
  - Options:
    - c: force the program to interpret your input as a ckey
    - p: only get the round the person played in? (applies only for ckeys)
    - r: the amount of rounds to download (applies only for ckeys)
    - f: pre-emptively delete all logs without our target ckey (applies only for ckeys)
  - `%download 198563`: download round 198563
  - `%dl 198563`: same as above
  - `%download 199563-199999`: download rounds 199500 to 199600 (inclusive). Be careful with this,
  as downloading and loading more than 100 rounds may slow down your computer by a lot.
  - `%download 198563 198565 198569 198570`: download rounds 198563, 198565, 198569 and 198570.
  You can run this command with as many rounds as you want.
  - `%download -p coolckey123` downloads 50 (default) rounds that `coolckey123` played in
  - `%download -r10 coolckey123` downloads 10 rounds that `coolckey123` played in
  - `%download -f coolckey123` downloads the default amout of rounds `coolckey123` was present in,
and pre-emptively delete all logs without `coolckey123` in them. This is uesful for when you want a
lot of rounds downloaded and analised, since it reduces processing time. Please be aware that the
excluded rounds can't be recovered, you will have to download them again.
  - `%download -fp coolckey123` downloads the default amount of rounds `coolckey123` played in, and
filters them, as mentioned earlier
  - `%download -c 123123123` this option is useful, as `dl` would interpret numbers as a round ID.
  `-c` forces it to interpret it as a ckey
  - `%download -c -r=10 123123123` you can have more than one switch! The `=` is optional
  - `%download -cr=10 123123123` you can group options like this! The `=` is optional. Just remember
to have the number right next to the character (r). Doing `-rc10` would assign 10 to c (error)
- `%load_logs`: loads logs from a file, and adds it to the current log set
  - `%load_logs logs.log`
- `%save_logs` (alias `%s`): saves logs to a file. This will **overwrite** your files, be careful
  - `%save_logs` (saves it to the default location, `logs.log`)
  - `%save_logs some_other_file.log`
  - `%save_logs WindowSmasher appeal.txt`
  - `%s`
  - `%s cool_file.txt`
- `%length` (alias `%l`): prints the amount of log lines we loaded into memory
  - `%length`
  - `%l`
- `%search_ckey` (alias `%ckey`): searches the logs for the ckeys. This is almost the same
as CTRL+F, but it tries to be smart about it. Remember to use ckeys and not keys! Ckeys
are the ones without spaces or special symbols, the ones you see in TGDB and such.
  - `%ckey WindowSmasher86` (only logs `WindowSmasher86` was included in)
  - `%search_ckey WindowSmasher86` (same as above)
  - `%search_ckey ckey1 ckey2` (union, or better known as logs from both people)
  - `%search_ckey ckey1 ckey2 ckey3`
  - `%search_ckey ckey1, ckey2, ckey3`
  - You can have as many as you want
- `%search_string` (alias `%string`): literally just CTRL+F, case insensitive. If you need to look for something
that has spaces, either use `-r` (raw mode), or add quotation marks (`'`). If your desired input has quotation marks,
use `\'` to escape them.
  - Options:
    - a: append mode. Take from the unfiltered logs and append the results to the current work set
    - c: case sensitive mode
    - r: raw mode. Do not parse any strings, ignore quotation marks
  - `%string 'help maint'`
  - `%string -r help maint`
  - `%string security`
  - `%string 'thank you very much!'`
  - `%string -a 'string to add'`: instead of filtering the current filtered logs, append the results (union)
    - Running these would produce the same result: `%string string1 string2` or `%string string1`, `%string -a string2`
  - `%string -c 'Case Sensitive'`: enable case sensitive mode
  - `%string -ar Case Sensitive`: same as above (you can group options)
- `%heard`: tries to exclude the logs that the people provided couldn't have heard. Just like conversation but it's a union
  - `%heard WindowSmasher86`
  - `%heard ckey1 ckey2`
- `%conversation`: tries to reconstruct a "conversation". Like heard but an intersection instead
  - `%conversation ckey`
  - `%conversation ckey1 ckey2`
  - You can do similar things as with `%search_ckey`
- `%reset`: removes all filters
  - `%reset`
- `%location` (alias `%loc`): filters by location. For example, you can get all logs that happened
in the bar.
  - Options:
    - e: exact mode (name must match exactly)
  - `%location Bar`
  - `%location -e Medbay Central` (you must provide the whole name)
  - `%location Medbay`
- `%list_locations`: lists all of the different possible locations in our current filtered logs
  - `%list_locations`
- `%who`: lists all connected ckeys, recognised by the logs
  - `%who`
- `%radius`: sorts the logs by time. You don't need to call this as they're automatically sorted
  - `%radius 50 62 2 10` (x=50, y=60, z=2, radius=10)
- `%type`: filters by log type. To get all types, type `LogType.list()`. `%` mandatory
  - `%type SAY ATTACK` (inclusion)
  - `%type !SILICON` (exclusion, just append `!`)
- `%print_logs` (alias `%p`): prints the logs. If there are more than 200 lines, opens a pager. To move in the pager press enter or space to advance a screen, or q to quit.
  - `%print_logs`
  - `%p`
- `%clip`: copy current logs to clipboard
- `%head`: prints the first few logs
  - `%head`
  - `%head 20` (print 20 instead of the default)
- `%tail`: same as head, but from the other side
  - `%tail`
  - `%tail 20`
- `%undo`: undoes your last command
  - `%undo`
  - `%undo 2`: undoes your last TWO commands, how fancy!
- `%cls`: build in command that clears the screen
  - `%cls`
- `%clear`: USE WITH CAUTION: **deletes** currently stored logs. After using this, there's no
going back.
- `%sort`: sorts the logs by time. You don't need to call this as they're automatically sorted
  - `%sort`
- `%lsmagic`: list all commands available. A lot are built in, so be careful!
- `%alias`: depending on your system, some commands will get an alias. For example, `%dir` will
be available on Windows system (list directory), while `%cat` is avaiable on POSIX systems. This
command will print out all your current aliases (and can be used to set new ones)

<font size="5">**You can stop reading now. Below is some information for nerds and developers.**</font>
<hr />
<br />
<br />

## How it works (for nerds)

Before starting going forward you should look at how the application looks. Oddly familiar, right? It's
because it's exactly what you think it is, an embedded [IPython](https://ipython.org/) shell. It's a Python
shell but better! The same thing Jupyter notebooks use. What this means is you can run arbitrary Python code!
You can interact with all available modules and create custom code.

The above commands are called IPython magics. They integrate pretty well with the shell. For more info
see [this file](log_magics.py)

When starting the application with command line parameters (if you don't know what those are skip this),
a variable called `logs` is created, which contains all lines from all log files provided, sorted by time.
Any function called accesses and modifies the `logs` attribute of your `logs` variable (confusing, I know),
so you may chain multiple functions. To reset the work set and remove all filters, call `logs.reset_work_set()`.

IPython magics use **the same variable** for all their functionality. If you `del logs` you will suddenly
get errors when calling magics.

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

As an alternative you can use `logs = LogFile.from_round_id(180150)`
This will automatically download all available log files.

You can also use `LogFile.from_round_range`, or `LogFile.from_round_collection`. Looking at the docstrings
should help you understand how they operate.

To load the whole folder (and save the result to a variable), we use `logs = LogFile.from_folder("logs")`.
If your logs folder is somewhere else, just type out the whole absolute or relative paths (for example, `../logs/`).
To load just one file, use `logs = LogFile.from_file("game.txt")` (assuming you want to load game.txt).
You can later add another file by doing `another_log = LogFile.from_file("attack.txt")`. To combine them use
`logs.collate(another_log)`. This will modify `logs` to incorporate the other log object's logs.

The variable name completely depends on you, you can pick any name you want (usually all lowercase with
underscores instead of spaces). Just don't forget to replace `logs` with your name.

When loading logs you may see some errors. It's usually fine to ignore them, unless there's many of them.
Sometimes there are strange and uncommon ways to log things, and it's hard to account for all of them.

Before getting started you may want to see some stats. To see the amount of log lines loaded, run
`len(logs)`. To see the list of all players that connected during that round, you can run
`logs.who`, or `len(logs.who)` for the number of players that have connected.

Now that we have a log file ready, let's filter it. We want to find out if someone has been running
around and destroying windows. Firstly, let's filter out only their ckey like so
`logs.filter_ckeys("WindowSmasher32")` (sidenote: notice the s in ckeys. This means you can filter
for multiple: `logs.filter_ckeys("WindowSmasher32", "FireaxeLover2", "CoolCkey53")`. We can view
the result by calling `logs.print_working()`. We're not done yet, we can go further than this. Let's
filter out everything (in the result), that doesn't contain a window. To do this, we can call
`logs.filter_strings("window")`. This works a lot like CTRL + F. To write our result to a file, we
can use `logs.write_working_to_file("logs.txt")`, which will write our working set to `logs.txt`.

But why not just use a text editor for this? Here's why. Let's say someone's been lying, and you want to
know if they heard someone say something. You could either go searching by hand, or call
`logs.filter_heard("Liar54")`. It doesn't work perfectly, but it's better than not having it, right?
To reduce our work set further, we can call the same functions as before.

This is only the surface of what you can do. Python knowledge comes in handy here. Since this is a
Python interpreter running in the background, you can do anything you would in Python. Run a file,
write a custom sort function, the world's your oyster!

### Cheat sheet (for nerds)

- `logs = LogFile.from_file("game.log")`: import game.log and save to `logs`
- `logs = LogFile.from_folder("logs")`: open folder logs, import all log files and save to `logs`
- `logs = LogFile.from_logs_link("https://tgstation13.org/parsed-logs/terry/data/logs/2022/03/01/round-179256/")`:
open link, get all known files, parse them and save them to `logs`
- `logs.filter_conversation("ckey1", "ckey2")`: get instances where ckey1 and ckey2 probably interacted
- `logs.filter_by_location_name("Pharmacy")`: only logs that happened in pharmacy
- `logs.filter_by_radius((32, 41, 2), 5)`: logs that happened 5 or less tiles away from (32, 41, 2)
- `logs.filter_ckeys("ckey1", "ckey2")`: actions that ckey2 or ckey2 performed (can be as many ckeys as you want)
- `logs.filter_heard("ckey")`: removes logs that ckey couldn't have heard or seen
- `logs.filter_strings("injected", "ckey1")`: works like CTRL+F but with multiple strings (as many as you want)
- `logs.filter_strings("injected", "ckey1", case_sensitive=True)`: same as above but case sensitive
- `logs.filter_strings_case_sensitive("injected", "ckey1")`: same as above
- `logs.reset_work_set()`: remove all filters
- `logs.head()` or `logs.head(10)`: prints the first 10 log entries
- `logs.tail()` or `logs.tail(10)`: prints the last 10 log entries
- `logs.sort()`: sorts the logs (usually called automatically, sorted by time)
- `logs.write_working_to_file("file.log")`: writes filtered logs to `file.log`
- `logs.print_working()`: prints all filtered logs

## Running

Download [this executable](https://github.com/RigglePrime/LogBuddy/releases/latest) OR

Quick tip: the colours on your terminal might not look that great, especially if you're using Windows.
I strongly suggest running it with Windows Terminal, as it has MUCH nicer colours. Simply download it
(I'm sure you can figure out how to do that), open the Terminal (try right clicking near the executable,
you may get an option to "open in Windows Terminal", if not use "`cd <directory>`, or `cd ..` to go back),
and run the executable from there (type the name out).

Using pip:

- `pip install ss13-tools`
- `logbuddy`

If the above doesn't work, you might not have the scripts folder in your path. Try:

- `python -m ss13_tools.log_buddy`

Optionally:

- `logbuddy logs`, where `./logs/` is a folder that contains logs (all will
be parsed)

I recommend creating a virtual environment, but it's not necessary. If you don't
know how to do it, you probably don't need to worry about it. If you run into
strange issues, start worrying about it.

Optionally, you can provide a log file, or folder with multiple log files.
The script will automatically load those in. You also manually do it later.
