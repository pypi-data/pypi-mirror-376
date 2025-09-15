import sys
import os
from io import open
import compiletools.utils
import compiletools.namer
import compiletools.configutils
import compiletools.apptools


def add_arguments(cap):
    """ Add the command line arguments that the HeaderDeps classes require """
    compiletools.namer.Namer.add_arguments(cap)
    cap.add(
        "--exemarkers",
        action="append",
        help='String that identifies a file as being an executable source.  e.g., "main ("',
    )
    cap.add(
        "--testmarkers",
        action="append",
        help='String that identifies a file as being an test source.  e.g., "unit_test.hpp"',
    )

    compiletools.utils.add_flag_argument(
        parser=cap,
        name="auto",
        default=False,
        help="Search the filesystem from the current working directory to find all the C/C++ files with main functions and unit tests",
    )

    compiletools.utils.add_flag_argument(
        parser=cap,
        name="disable-tests",
        default=False,
        dest="disable_tests",
        help="When --auto is specified, add --disable-tests to stop automatic building and running of tests",
    )

    compiletools.utils.add_flag_argument(
        parser=cap,
        name="disable-exes",
        default=False,
        dest="disable_exes",
        help="When --auto is specified, add --disable-exes to stop automatic building of exes. (Useful for automatically building tests)",
    )

    # Figure out what style classes are available and add them to the command
    # line options
    styles = [st[:-5].lower() for st in dict(globals()) if st.endswith("Style")]
    cap.add("--style", choices=styles, default="indent", help="Output formatting style")

    compiletools.utils.add_flag_argument(
        parser=cap,
        name="filenametestmatch",
        default=True,
        help="Identify tests based on filename in addition to testmarkers",
    )


class NullStyle(object):
    def __call__(self, executabletargets, testtargets):
        print(executabletargets)
        print(testtargets)


class FlatStyle(object):
    def __call__(self, executabletargets, testtargets):
        print(" ".join(executabletargets + testtargets))


class IndentStyle(object):
    def __call__(self, executabletargets, testtargets):
        print("Executable Targets:")
        if executabletargets:
            for target in executabletargets:
                print("\t{}".format(target))
        else:
            print("\tNone found")

        print("Test Targets:")
        if testtargets:
            for target in testtargets:
                print("\t{}".format(target))
        else:
            print("\tNone found")


class ArgsStyle(object):
    def __call__(self, executabletargets, testtargets):
        if executabletargets:
            for target in executabletargets:
                sys.stdout.write(" {}".format(target))

        if testtargets:
            sys.stdout.write(" --tests")
            for target in testtargets:
                sys.stdout.write(" {}".format(target))


class FindTargets(object):

    """ Search the filesystem from the current working directory to find
        all the C/C++ files with main functions and unit tests.
    """

    def __init__(self, args, argv=None, variant=None, exedir=None):
        self._args = args
        self.namer = compiletools.namer.Namer(
            self._args, argv=argv, variant=variant, exedir=exedir
        )

    def process(self, args, path=None):
        """ Put the output of __call__ into the args """
        executabletargets, testtargets = self(path)
        args.filename += executabletargets
        if testtargets:
            if not args.tests:
                args.tests = []
            args.tests += testtargets

        if args.verbose >= 2:
            styleobj = compiletools.findtargets.IndentStyle()
            styleobj(executabletargets, testtargets)

    def __call__(self, path=None):
        """ Do the file system search and
            return the tuple ([executabletargets], [testtargets])
        """
        if self._args.exemarkers is None:
            variant = getattr(self._args, 'variant', 'unknown')
            config_file = getattr(self._args, 'config', None)
            
            print("Error: No exemarkers configured.", file=sys.stderr)
            print(f"  Variant: {variant}", file=sys.stderr)
            if config_file:
                print(f"  Config file: {config_file}", file=sys.stderr)
            print(f"  exemarkers value: {self._args.exemarkers}", file=sys.stderr)
            print("", file=sys.stderr)
            print("This is unexpected and hints at other issues. Potential solutions:", file=sys.stderr)
            print(f"  1. Configure exemarkers in your {variant}.conf file", file=sys.stderr)
            print("  2. Specify exemarkers on command line: --exemarkers='main('", file=sys.stderr)
            sys.exit(1)
            
        if path is None:
            path = "."
        executabletargets = []
        testtargets = []
        bindir = self.namer.topbindir()
        for root, dirs, files in os.walk(path):
            if bindir in root or self._args.objdir in root:
                continue
            for filename in files:
                pathname = os.path.join(root, filename)
                if not compiletools.utils.is_source(pathname):
                    continue
                with open(pathname, encoding="utf-8", errors="ignore") as ff:
                    for line in ff:
                        if any(marker in line for marker in self._args.exemarkers):
                            # A file starting with test....cpp will be interpreted
                            # As a test even though it satisfied the exemarker
                            if (
                                filename.startswith("test")
                                and self._args.filenametestmatch
                            ):
                                testtargets.append(pathname)
                                if self._args.verbose >= 3:
                                    print("Found a test: " + pathname)
                            else:
                                executabletargets.append(pathname)
                                if self._args.verbose >= 3:
                                    print("Found an executable source: " + pathname)
                            break
                        if any(marker in line for marker in self._args.testmarkers):
                            testtargets.append(pathname)
                            if self._args.verbose >= 3:
                                print("Found a test: " + pathname)
                            break
        if self._args.disable_tests:
            testtargets = []
        if self._args.disable_exes:
            executabletargets = []
        return executabletargets, testtargets


def main(argv=None):
    cap = compiletools.apptools.create_parser(
        "Find C/C++ files with main functions and unit tests", argv=argv
    )
    compiletools.findtargets.add_arguments(cap)

    args = compiletools.apptools.parseargs(cap, argv)
    findtargets = FindTargets(args)

    styleclass = globals()[args.style.title() + "Style"]
    styleobj = styleclass()
    executabletargets, testtargets = findtargets()
    styleobj(executabletargets, testtargets)

    return 0
