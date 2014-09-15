import filetypes
from filetypes.plainfile import PlainFile
from filetypes.basetest import BaseTest

MAX_STEPS = 2e20

NUM_ROWS = 25
NUM_COLS = 25

BLANK = 0           # don't change to > 0; sums depend on this
VISITED = 1
WALL = 2


def _parse_map(path):
    f = open(path, 'r')

    map_list = []
    for line in f:
        row = []
        for char in line:
            if char == '\n':
                continue
            elif char != ' ':
                row.append(WALL)
            else:
                row.append(BLANK)
        map_list.append(row)

    if len(map_list) != NUM_ROWS:
        raise ValueError("map has {} rows, but should have "
                         "{}".format(len(map_list), NUM_ROWS))

    if len(map_list) > 1 and \
       not all(map(lambda x: len(x) == NUM_COLS, map_list)):
        raise ValueError("map has at least one row not {} "
                         "columns wide".format(NUM_COLS))

    return map_list



def _parse_rules(path):
    import re

    f = open(path, 'r')
    rule_pattern = re.compile("(\d) ([\*xXnN])([\*xXeE])([\*xXwW])([\*xXsS]) "
                              "-> ([xXnNeEwWsS]) (\d)")
    rules = dict()
    i = -1

    for line in f:
        i += 1
        line = line.strip()
        if not line or line[0] == '#':
            continue

        match = re.match(rule_pattern, line)
        if not match:
            raise PicobotSyntaxError("syntax error on line {}".format(i))

        prestate = int(match.group(1))
        surr_n, surr_e = match.group(2), match.group(3)
        surr_w, surr_s = match.group(4), match.group(5)
        postdir, poststate = match.group(6), int(match.group(7))

        if prestate not in rules:
            rules[prestate] = {(n, e, w, s):None for n in [BLANK, WALL] \
                                                 for e in [BLANK, WALL] \
                                                 for w in [BLANK, WALL] \
                                                 for s in [BLANK, WALL]}

        if poststate not in rules:
            rules[poststate] = {(n, e, w, s):None for n in [BLANK, WALL] \
                                                  for e in [BLANK, WALL] \
                                                  for w in [BLANK, WALL] \
                                                  for s in [BLANK, WALL]}

        # this rule might match many concrete surroundings; we enumerate all
        # possible concrete surroundings now
        surrs = []
        if surr_n in ['x', 'X', '*']:
            surrs.append((BLANK, None, None, None))
        if surr_n in ['n', 'N', '*']:
            surrs.append((WALL, None, None, None))

        # add possible east surroundings
        if surr_e in ['x', 'X']:
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], BLANK, s[2], s[3]))
            surrs = surrs2
        elif surr_e in ['e', 'E']:
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], WALL, s[2], s[3]))
            surrs = surrs2
        elif surr_e == '*':
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], BLANK, s[2], s[3]))
                surrs2.append((s[0], WALL, s[2], s[3]))
            surrs = surrs2

        # add possible west surroundings
        if surr_w in ['x', 'X']:
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], s[1], BLANK, s[3]))
            surrs = surrs2
        elif surr_w in ['w', 'W']:
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], s[1], WALL, s[3]))
            surrs = surrs2
        elif surr_w == '*':
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], s[1], BLANK, s[3]))
                surrs2.append((s[0], s[1], WALL, s[3]))
            surrs = surrs2

        # add possible south surroundings
        if surr_s in ['x', 'X']:
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], s[1], s[2], BLANK))
            surrs = surrs2
        elif surr_s in ['s', 'S']:
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], s[1], s[2], WALL))
            surrs = surrs2
        elif surr_s == '*':
            surrs2 = []
            for s in surrs:
                surrs2.append((s[0], s[1], s[2], BLANK))
                surrs2.append((s[0], s[1], s[2], WALL))
            surrs = surrs2

        # for each concrete surroundings match, add a rule to trigger the
        # movement post-state pair
        for s in surrs:
            if rules[prestate][s]:
                raise RepeatRuleError("repeat rule")

            rules[prestate][s] = (postdir, poststate)

    f.close()
    return rules



def _print_rules(rules):
    """Debugging helper function. Given a rules dictionary, print the
    rules in a human-readable format.
    """

    for prestate in rules:
        print("while in state {}:".format(prestate))

        for surr in rules[prestate]:
            n = 'N' if surr[0] else 'X'
            e = 'E' if surr[1] else 'X'
            w = 'W' if surr[2] else 'X'
            s = 'S' if surr[3] else 'X'

            print("{}{}{}{}".format(n, e, w, s), end='')

            if rules[prestate][surr]:
                newdir = rules[prestate][surr][0]
                newstate = rules[prestate][surr][1]
                print(" -> {} {}".format(newdir, newstate))
            else:
                print(" -> (no mapping)")



def _print_map(map, r=-1, c=-1):
    """Debugging helper function. Given a map and optionally a position
    for Picobot, print the map.
    """

    i, j = 0, 0
    for line in map:
        for cell in line:
            if cell == BLANK:
                if i == r and j == c:
                    ch = 'P'
                else:
                    ch = ' '
            elif cell == WALL:
                if i == r and j == c:
                    ch = '!'
                else:
                    ch = '#'
            elif cell == VISITED:
                if i == r and j == c:
                    ch = 'P'
                else:
                    ch = '~'

            print(ch, end='')
            j += 1

        print()
        i, j = i + 1, 0



class MapTest(BaseTest):
    json_type = 'map'

    def __init__(self, description, deductions, error_deduction, map, start):
        import os
        import config

        self.description = description
        self.deductions = deductions
        self.error_deduction = error_deduction
        self.start = start

        map_path = config.static_dir + os.sep + map
        if not os.path.isfile(map_path):
            raise ValueError("Picobot map file '{}' "
                             "cannot be found".format(map))

        self.map = _parse_map(map_path)


    @staticmethod
    def from_dict(dict_obj, file_type):
        from fractions import Fraction
        import re

        args = {'description': dict_obj['description'],
                'error_deduction': dict_obj['error_deduction'],
                'map': dict_obj['map']}

        # parse starting location
        pattern = re.compile("\(?(\d+)\s*,\s*(\d+)\)?")
        result = re.search(pattern, dict_obj['start'])

        x, y = int(result.group(1)), int(result.group(2))
        args['start'] = (x, y)

        # parse deduction ratios
        args['deductions'] = dict()
        for ratio, deduction in dict_obj['deductions'].items():
            args['deductions'][Fraction(ratio)] = deduction

        return MapTest(**args)


    def run(self, path):
        """Given a path to the Picobot file containing a list of
        Picobot rules, simulate the action of Picobot on a map and return
        a deduction as necessary, dependent on Picobot's map coverage.
        """

        try:
            coverage = self.__simulate(path)

        except PicobotSyntaxError as err:
            return {'description': self.description,
                    'deduction': self.error_deduction,
                    'notes': [str(err)]}
        except RepeatRuleError as err:
            return {'description': self.description,
                    'deduction': self.error_deduction,
                    'notes': [str(err)]}
        except WallError as err:
            return {'description': self.description,
                    'deduction': self.error_deduction,
                    'notes': [str(err)]}
        except NoRuleError as err:
            return {'description': self.description,
                    'deduction': self.error_deduction,
                    'notes': [str(err)]}

        import fractions
        ratios = sorted(self.deductions.keys())

        if coverage > ratios[-1]:
            # student did better than the deduction for the
            # highest coverage
            return None
        else:
            # find the highest coverage less than the student's
            # coverage for the appropriate deduction
            deduction = self.deductions[ratios[0]]

            for ratio in ratios:
                if ratio > coverage:
                    break
                else:
                    deduction = self.deductions[ratio]

            return {'deduction': deduction,
                    'description': self.description,
                    'notes': ["Picobot coverage: {}".format(coverage)]}


    def __simulate(self, path):
        from fractions import Fraction
        from functools import reduce

        rules = _parse_rules(path)
        state = 0

        # note: (row, column) notation is used here for uniformity:
        # row 0 is the *top* row and column 0 is the *left* edge
        # this matches exactly how the map is stored in map.left
        r, c = self.start

        def blanks(row):
            return sum(map(lambda x: not x, row))

        total_blank = reduce(int.__add__, map(blanks, self.map))
        num_blank = total_blank

        def surroundings(r, c):
            n = self.map[r - 1][c]
            e = self.map[r][c + 1]
            w = self.map[r][c - 1]
            s = self.map[r + 1][c]

            # ignore visited surroundings
            n = BLANK if n == VISITED else n
            e = BLANK if e == VISITED else e
            w = BLANK if w == VISITED else w
            s = BLANK if s == VISITED else s

            return (n, e, w, s)

        def move(r, c, dir):
            if dir in ['n', 'N']: r -= 1
            if dir in ['e', 'E']: c += 1
            if dir in ['w', 'W']: c -= 1
            if dir in ['s', 'S']: r += 1

            if self.map[r][c] == WALL:
                raise WallError("cannot move into wall")

            return r, c

        # color and count initial location
        self.map[r][c] = VISITED
        num_blank -= 1

        i = 0
        while num_blank > 0 and i < MAX_STEPS:
            i += 1

            new = rules[state][surroundings(r, c)]
            if not new:
                raise NoRuleError("no rule mapping for current conditions")

            r, c = move(r, c, new[0])

            if self.map[r][c] == BLANK:
                self.map[r][c] = VISITED
                num_blank -= 1

            state = new[1]

        return 1 - Fraction(num_blank, total_blank)


    def __str__(self):
        return "'{}' test of {}".format(self.json_type, self.target)



class PicobotFile(PlainFile):
    json_type = 'picobot'
    extensions = ['txt', 'picobot']
    supported_tests = PlainFile.supported_tests.copy()
    supported_tests.append(MapTest)


    def __init__(self, path, point_value, tests=None):
        self.path = path
        self.point_value = point_value
        self.tests = tests if tests else []


    def __str__(self):
        return self.path + " (Picobot file)"


    @staticmethod
    def from_dict(dict_obj):
        args = {'path': dict_obj['path'],
                'point_value': dict_obj['point_value'],
                'tests': []}

        if 'tests' in dict_obj:
            for t in dict_obj['tests']:
                test_cls = filetypes.find_test_class(PicobotFile.json_type, t['type'])
                args['tests'].append(test_cls.from_dict(t, PicobotFile.json_type))

        return PicobotFile(**args)


    def to_dict(self):
        return {'path': self.path,
                'type': self.json_type,
                'point_value': self.point_value,
                'tests': [t.to_dict() for t in self.tests]}


    def run_tests(self):
        results = []
        for t in self.tests:
            result = t.run(self.path)
            if result is not None:
                results.append(result)

        return results



class PicobotSyntaxError(Exception):
    pass

class RepeatRuleError(Exception):
    pass

class WallError(Exception):
    pass

class NoRuleError(Exception):
    pass