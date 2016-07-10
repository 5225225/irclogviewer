import sys
import time
import datetime
import re
import textwrap
import hashlib
import string

INPUT_DATEFORMAT = "%Y-%m-%d %H:%M:%S"
OUTPUT_DATEFORMAT = "%H:%M:%S"
INPUT_LOGLINE_RE = "([^\t]*)\t([^\t]*)\t(.*)"
WRAP_LENGTH = 70
NICK_LEN_CAP = 16
COLOURS = [31,32,33,34,35,36,91,92,93,94,95,96]

COLOUR_OVERRIDE = {
"<<<": 31,
">>>": 32,
}

HIGHLIGHT_NICKS = [
]

IGNORE_NICKS = [
"--",
"",
"=!="
]

class IRCLogLine:
    def __init__(self, datetimestr, username, text):
        self.datetimestr = datetimestr
        self.datetime = datetime.datetime.strptime(datetimestr, INPUT_DATEFORMAT)
        self.username = username
        self.text = textwrap.wrap(text, WRAP_LENGTH)

    def __repr__(self):
        return "IRCLogLine({}, {}, {})".format(
            self.datetimestr,
            self.username,
            self.text
        )

loglines = []
seen_nicks = set()
longest_nick = 0


allowed_char_nick = set(
    string.ascii_lowercase + 
    string.ascii_uppercase + 
    string.digits + 
    "_-\\[]{}^`|~@&+<> ")

def get_possible_nicks(line):
    return "".join([x for x in line if x in allowed_char_nick]).split(" ")

x = 1
with open(sys.argv[1], "rb") as f:
    for line in f:
        try:
            line = line.decode("UTF-8")
            datetimestr, username, text = re.match(INPUT_LOGLINE_RE, line).groups()
            if not username in IGNORE_NICKS:
                if len(username) > NICK_LEN_CAP:
                    username = username[:NICK_LEN_CAP]
                    username += "\u2026"
                if len(username) >= 3:
                    username = username.strip()
                    seen_nicks.add(username)
                longest_nick = max(longest_nick, len(username))
                logline = IRCLogLine(datetimestr, username, text)
                loglines.append(logline)
                if x % 10000 == 0:
                    print(datetimestr)
                    print(x)
        except AttributeError:
            # Probably not an IRC line. Ignore it.
            pass
        except UnicodeDecodeError as e:
            # Corrupted file, maybe? Warn, but don't fail.
            sys.stderr.write("Warning: UnicodeDecodeError on line {}\n".format(x))
            sys.stderr.write(str(e) + "\n")
        x = x + 1

for line in loglines:
    toprint = "{:{}}  {:>{}}".format(line.datetime, OUTPUT_DATEFORMAT, line.username, longest_nick)
    indent_len = len(toprint)
    if len(line.text) > 1:
        toprint += " " + line.text[0] + "\n"
        for indentline in line.text[1:]:
            toprint += " "*(indent_len+1) + indentline + "\n"
    elif len(line.text) == 1:
        toprint += " " + line.text[0] + "\n"
    else:
        toprint += "  \n"

    assert isinstance(line, IRCLogLine)
    for nick in get_possible_nicks(" ".join(line.text) + " " + line.username):
        if nick in seen_nicks:
            if nick not in COLOUR_OVERRIDE:
                colour = COLOURS[int.from_bytes(
                    hashlib.md5(nick.encode("UTF-8")).digest(), byteorder="little") % len(COLOURS)]
            else:
                colour = COLOUR_OVERRIDE[nick]

            toprint = toprint.replace(" {}: ".format(nick), " \x1b[{}m{}\x1b[m: ".format(colour, nick))
            toprint = toprint.replace(" {} ".format(nick), " \x1b[{}m{}\x1b[m ".format(colour, nick))
            toprint = toprint.replace("<{}>".format(nick), "<\x1b[{}m{}\x1b[m>".format(colour, nick))

            if nick in HIGHLIGHT_NICKS:
                toprint = toprint.replace(nick, "\x1b[1m{}\x1b[m".format(nick))
    sys.stdout.write(toprint)
