import math
import os
import sys
import time
from os import PathLike
from pathlib import PurePath
from random import choices as get_random
from types import FunctionType
from typing import Callable

from numpy import ndarray
from skimage.metrics import mean_squared_error

import chromatic as cm


class FunctionNamespace:

    def register[**P, R](self, __func: Callable[P, R] | FunctionType) -> Callable[P, R]:
        setattr(self, __func.__name__.casefold(), __func)
        return __func


DEMO_FUNCS = FunctionNamespace()


@DEMO_FUNCS.register
def escher_dragon_ascii():
    """Displays the image-to-ASCII transform of 'Dragon' by M.C. Escher."""
    input_img = cm.data.escher()
    font = cm.userfont['vga437']
    char_set = r"  ._-~+<vX♦'^Vx>|πΦ0Ω#$║╫"
    ascii_str = cm.img2ascii(
        input_img, font, factor=240, char_set=char_set, sort_glyphs=True
    )
    ascii_img = cm.ascii2img(ascii_str, font, font_size=16, fg='white', bg='black')
    ascii_img.show()


@DEMO_FUNCS.register
def escher_dragon_256color():
    """Displays the image-to-ANSI transform of 'Dragon' by M.C. Escher in 8-bit color."""
    input_img = cm.data.escher()
    font = cm.userfont['vga437']
    ansi_array = cm.img2ansi(input_img, font, factor=240, ansi_type='8b', equalize=True)
    ansi_img = cm.ansi2img(ansi_array, font, font_size=16)
    ansi_img.show()


@DEMO_FUNCS.register
def butterfly_16color():
    """Displays image-to-ANSI transform of 'Spider Lily & Papilio xuthus' in 4-bit color.

    Good ol' C-x M-c M-butterfly...
    """
    input_img = cm.data.butterfly()
    font = cm.data.userfont['vga437']
    char_set = r"'·,•-_→+<>ⁿ*%⌂7√Iï∞πbz£9yîU{}1αHSw♥æ?GX╕╒éà⌡MF╝╩ΘûÇƒQ½☻Å¶┤▄╪║▒█"
    ansi_array = cm.img2ansi(
        input_img,
        font,
        factor=200,
        char_set=char_set,
        equalize=True,
        ansi_type=cm.ansicolor4Bit,
    )
    ansi_img = cm.ansi2img(ansi_array, font, font_size=16)
    ansi_img.show()


@DEMO_FUNCS.register
def butterfly_truecolor():
    """Displays the image-to-ANSI transform of 'Spider Lily & Papilio xuthus' in 24-bit color."""
    input_img = cm.data.butterfly()
    font = cm.userfont['vga437']
    ansi_array = cm.img2ansi(
        input_img, font, factor=200, ansi_type='24b', equalize='white_point'
    )
    ansi_img = cm.ansi2img(ansi_array, font, font_size=16)
    ansi_img.show()


@DEMO_FUNCS.register
def butterfly_randcolor():
    input_img = cm.data.butterfly()
    font = cm.userfont['vga437']
    ansi_array = cm.img2ansi(
        input_img, font, factor=200, ansi_type='8b', equalize='white_point'
    )
    for row in range(len(ansi_array)):
        for idx, cs in enumerate(ansi_array[row]):
            if (fg := cs.fg) is not None:
                _, _, v = cm.color.rgb2hsv(fg.rgb)
                h, s, _ = cm.color.rgb2hsv(cm.color.randcolor().rgb)
                ansi_array[row][idx] = cs.recolor(
                    fg=cm.Color.from_rgb(cm.color.hsv2rgb((h, s, v)))
                )
    ansi_img = cm.ansi2img(ansi_array, font, font_size=16)
    ansi_img.show()


@DEMO_FUNCS.register
def goblin_virus_truecolor():
    """`G-O-B-L-I-N VIRUS <https://imgur.com/n0Mng2P>`__"""
    input_img = cm.data.goblin_virus()
    font = cm.userfont['vga437']
    char_set = r'  .-|_⌐¬^:()═+<>v≥≤«*»x└┘π╛╘┴┐┌┬╧╚╙X╒╜╨#0╓╝╩╤╥│╔┤├╞╗╦┼╪║╟╠╫╣╬░▒▓█▄▌▐▀'
    ansi_array = cm.img2ansi(
        input_img, font, factor=200, char_set=char_set, ansi_type='24b', equalize=False
    )
    ansi_img = cm.ansi2img(ansi_array, font, font_size=16)
    ansi_img.show()


@DEMO_FUNCS.register
def named_colors():
    print("{0.__module__}.{0.__name__}:".format(cm.ColorNamespace))
    named = cm.color.palette.named_color_idents()
    whites = [0]
    for idx, n in enumerate(named):
        hsv = cm.color.rgb2hsv(n.fg.rgb)
        if all(
            map(lambda i, x: math.isclose(hsv[i], x, abs_tol=0.16), (-1, 1), (1, 0))
        ):
            if idx - whites[-1] < 4:
                whites.pop()
            whites.append(idx)
    whites.append(-1)
    for start, stop in zip(whites, whites[1:]):
        xs = sorted(
            named[start + 1 if start else None : stop + 1 if ~stop else None],
            key=lambda x: cm.color.rgb2lab(x.fg.rgb),
        )
        print(' | '.join(xs))


@DEMO_FUNCS.register
def color_cube():
    """Print the ANSI256 6x6x6 color cube"""
    fmt_code = lambda n: cm.ColorStr(f"\x1b[48;5;{n}m{n: >4}", reset=False)
    ansi_256_codes = iter(range(0x100))
    for i in range(0x10):
        if i and i % 8 == 0:
            print("\x1b[m")
        print(fmt_code(next(ansi_256_codes)), end='')
    else:
        print("\x1b[m")
    for i in range(6**3):
        if i and i % 6**2 == 0:
            print("\x1b[m")
        print(fmt_code(next(ansi_256_codes)), end='')
    else:
        print("\x1b[m")
    for x in ansi_256_codes:
        print(fmt_code(x), end='')
    else:
        print("\x1b[m")


@DEMO_FUNCS.register
def color_table():
    """Print foreground / background combinations in each ANSI format.

    A handful of stylistic SGR parameters are displayed as well.
    """

    ansi_types = [cm.ansicolor4Bit, cm.ansicolor8Bit, cm.ansicolor24Bit]

    colors: dict[str, cm.Color] = {
        name.title(): getattr(cm.ColorNamespace, name)
        for name in [
            'BLACK',
            'WHITE',
            'RED',
            'ORANGE',
            'YELLOW',
            'GREEN',
            'BLUE',
            'INDIGO',
            'PURPLE',
        ]
    }
    spacing = max(map(len, colors)) + 1
    fg_colors = [
        cm.ColorStr(f"{name: ^{spacing}}", fg=color, ansi_type=cm.ansicolor24Bit)
        for name, color in colors.items()
    ]
    bg_colors = [cm.ColorStr().recolor(bg=None)] + [
        c.recolor(fg=None, bg=c.fg) for c in fg_colors
    ]
    print(
        '|'.join(
            f"{'%dbit' % n: {'>' if n == 24 else '^'}{spacing - 1}}" for n in (4, 8, 24)
        )
    )
    for row in fg_colors:
        for col in bg_colors:
            for typ in ansi_types:
                print(row.as_ansi_type(typ).recolor(bg=col.bg), end='\x1b[0m')
        print()
    print('\nstyles:', end='\t')
    style_params = [
        cm.SgrParameter.BOLD,
        cm.SgrParameter.ITALICS,
        cm.SgrParameter.CROSSED_OUT,
        cm.SgrParameter.ENCIRCLED,
        cm.SgrParameter.SINGLE_UNDERLINE,
        cm.SgrParameter.DOUBLE_UNDERLINE,
        cm.SgrParameter.NEGATIVE,
    ]
    for style in style_params:
        print(
            cm.ColorStr(f"{cm.SgrParameter.__qualname__}.{style.name}").add_sgr_param(
                style
            ),
            end=('\n' if style is style_params[-1] else "\x1b[0m".ljust(8)),
        )


def glyph_comparisons(__output_dir: str | PathLike[str] = None):

    def _find_best_matches(
        glyph_masks1: dict[str, ndarray], glyph_masks2: dict[str, ndarray]
    ) -> dict[str, str]:
        best_matches = {}
        for char1, mask1 in glyph_masks1.items():
            best_char = None
            best_score = float('inf')
            for char2, mask2 in glyph_masks2.items():
                score = mean_squared_error(mask1, mask2)
                if score < best_score:
                    best_score = score
                    best_char = char2
            best_matches[char1] = best_char
        return best_matches

    if __output_dir and not os.path.isdir(__output_dir):
        raise NotADirectoryError(__output_dir)
    user_fonts = [pair := (cm.userfont['vga437'], cm.userfont['consolas']), pair[::-1]]
    trans_table = str.maketrans({']': None, '0': ' ', '[': ' '})
    char_set = cm.cp437_printable()
    separator = '#' * 100
    for font1, font2 in user_fonts:
        glyph_masks_1 = cm.get_glyph_masks(font1, char_set, dist_transform=True)
        glyph_masks_2 = cm.get_glyph_masks(font2, char_set, dist_transform=True)
        best_matches_ = _find_best_matches(glyph_masks_1, glyph_masks_2)
        txt = ''.join(
            '->'.center(32, ' ')
            .join(['{}'] * 2)
            .format(
                f"{font1.name}"
                f"[{input_char!r}, {input_char.encode('unicode_escape').decode()!r}]",
                f"{font2.name}"
                f"[{matched_char!r}, {matched_char.encode('unicode_escape').decode()!r}]",
            )
            .center(100, ' ')
            + '\n\n'
            + '\n'.join(
                ''.join(z).translate(trans_table)
                for z in zip(
                    f'{glyph_masks_1[input_char].astype(int)}\n'.splitlines(),
                    f'{glyph_masks_2[matched_char].astype(int)}\n'.splitlines()[1:],
                )
            )
            + separator.join(['\n'] * 2)
            for input_char, matched_char in best_matches_.items()
        )
        if __output_dir is not None:
            fname = (
                PurePath(__output_dir)
                / f"{'_to_'.join(font.name.lower() for font in (font1, font2))}.txt"
            )
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(txt)
        else:
            for glyph in get_random(txt.split(separator), k=len(char_set) // 2):
                print(separator + glyph)


class _time_wrapper[**P, R]:

    def __init__(self, func: Callable[P, R] | FunctionType | type = None):
        self.func = func

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> tuple[R, float, str]:
        start = time.perf_counter()
        result = self.func(*args, **kwargs)
        stop = time.perf_counter()
        delta, fmt = self._delta(start, stop)
        return result, delta, fmt

    @staticmethod
    def _delta(start: float, stop: float) -> tuple[float, str]:
        delta = stop - start
        mag, fmt = min(
            [(1, 's'), (1e-3, 'ms'), (1e-6, 'μs'), (1e-9, 'ns'), (1e-12, 'ps')],
            key=lambda x: abs(math.log10(x[0]) - math.log10(delta)),
        )
        delta *= 1 / mag
        return round(delta, 3), fmt


def print_help(ns: dict[str, FunctionType], choices: dict[int, str]):
    from textwrap import wrap
    from shutil import get_terminal_size

    columns = get_terminal_size().columns
    print("runs a demo function\n")
    print("options:")
    indent = max(map(len, (f"\t{k}".expandtabs() for k in choices.values())))
    print(f"{'\t-h, --help': <{indent}}\t\tprint this message and exit")
    for idx, k in choices.items():
        head = f"\t{idx}, {k}"
        desc = '\n'.join(
            wrap(
                ns[k].__doc__ or '',
                columns,
                initial_indent='\t\t',
                subsequent_indent='\t\t',
            )
        )
        print(f"{head: <{indent}}{desc}")
    print()


def main():
    ns: dict[str, FunctionType] = vars(DEMO_FUNCS)
    choices = dict(enumerate(sorted(ns)))

    def get_choice(__s: str):
        if __s.isdigit() and int(__s) in choices.keys():
            return ns[choices[int(__s)]]
        elif __s.casefold() in ns.keys():
            return ns[__s.casefold()]
        raise KeyError(__s)

    choice: FunctionType | None = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.casefold() in {'-h', '--help'}:
            return print_help(ns, choices)
        elif len(sys.argv) != 2:
            print(
                f"unexpected arguments: " + f"{sys.argv[1:]}".strip('[]'),
                file=sys.stderr,
            )
            return 1
        else:
            try:
                choice = get_choice(arg.strip())
            except KeyError as e:
                print(f"unexpected argument: {e}", file=sys.stderr)
                return 1
    else:
        for idx, k in choices.items():
            print(f"{idx} {k!r}")
        while True:
            try:
                from_user = input("select a demo function> ").strip()
                if not from_user:
                    continue
                if from_user == 'exit':
                    return
                choice = get_choice(from_user)
                break
            except KeyError as e:
                print(f"invalid option: {e}", file=sys.stderr)
                time.sleep(0.1)
            except KeyboardInterrupt:
                print(f"\n{KeyboardInterrupt.__name__}", file=sys.stderr)
                return
    if choice is not None:
        print(f"running {choice.__name__!r}...", end='\n\n')
        _, delta, fmt = _time_wrapper(choice)()
        print(f"\ntotal execution time: {delta} {fmt}")
        return


if __name__ == '__main__':
    sys.exit(main())
