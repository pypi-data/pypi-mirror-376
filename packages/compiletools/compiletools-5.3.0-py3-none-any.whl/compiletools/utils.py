import os
import inspect
import functools
import shlex
import compiletools.wrappedos

# Module-level constant for C++ source extensions (lowercase)
_CPP_SOURCE_EXTS = (
    '.cpp', '.cxx', '.cc', '.c++', '.cp', '.mm', '.ixx'
)

_C_SOURCE_EXTS = (".c")

def is_nonstr_iter(obj):
    """ A python 3 only method for deciding if the given variable
        is a non-string iterable
    """
    if isinstance(obj, str):
        return False
    return hasattr(obj, "__iter__")

@functools.lru_cache(maxsize=None)
def cached_shlex_split(command_line):
    """Cache shlex parsing results"""
    return shlex.split(command_line)


@functools.lru_cache(maxsize=None)
def isheader(filename):
    """ Internal use.  Is filename a header file?"""
    return filename.split(".")[-1].lower() in ["h", "hpp", "hxx", "hh", "inl"]

@functools.lru_cache(maxsize=None)
def is_cpp_source(path: str) -> bool:
    """Lightweight C++ source detection by extension (case-insensitive)."""
    # Fast path: split once
    _, ext = os.path.splitext(path)
    return ext.lower() in _CPP_SOURCE_EXTS

@functools.lru_cache(maxsize=None)
def issource(filename):
    """ Internal use. Is the filename a source file?"""
    return filename.split(".")[-1].lower() in ["cpp", "cxx", "cc", "c"]


def isexecutable(filename):
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


@functools.lru_cache(maxsize=None)
def implied_source(filename):
    """ If a header file is included in a build then assume that the corresponding c or cpp file must also be build. """
    basename = os.path.splitext(filename)[0]
    extensions = [".cpp", ".cxx", ".cc", ".c", ".C", ".CC"]
    for ext in extensions:
        trialpath = basename + ext
        if compiletools.wrappedos.isfile(trialpath):
            return compiletools.wrappedos.realpath(trialpath)
    else:
        return None


@functools.lru_cache(maxsize=None)
def impliedheader(filename):
    """ Guess what the header file is corresponding to the given source file """
    basename = os.path.splitext(filename)[0]
    extensions = [".hpp", ".hxx", ".hh", ".h", ".H", ".HH"]
    for ext in extensions:
        trialpath = basename + ext
        if compiletools.wrappedos.isfile(trialpath):
            return compiletools.wrappedos.realpath(trialpath)
    else:
        return None


def clear_cache():
    cached_shlex_split.cache_clear()
    isheader.cache_clear()
    issource.cache_clear()
    implied_source.cache_clear()
    impliedheader.cache_clear()


def extractinitargs(args, classname):
    """ Extract the arguments that classname.__init__ needs out of args """
    # Build up the appropriate arguments to pass to the __init__ of the object.
    # For each argument given on the command line, check if it matches one for
    # the __init__
    kwargs = {}
    function_args = inspect.getfullargspec(classname.__init__).args
    for key, value in list(vars(args).items()):
        if key in function_args:
            kwargs[key] = value
    return kwargs


def tobool(value):
    """
    Tries to convert a wide variety of values to a boolean
    Raises an exception for unrecognised values
    """
    if str(value).lower() in ("yes", "y", "true", "t", "1", "on"):
        return True
    if str(value).lower() in ("no", "n", "false", "f", "0", "off"):
        return False

    raise ValueError("Don't know how to convert " + str(value) + " to boolean.")


def add_boolean_argument(parser, name, dest=None, default=False, help=None):
    """Add a boolean argument to an ArgumentParser instance."""
    if not dest:
        dest = name
    group = parser.add_mutually_exclusive_group()
    bool_help = help + " Use --no-" + name + " to turn the feature off."
    group.add_argument(
        "--" + name,
        metavar="",
        nargs="?",
        dest=dest,
        default=default,
        const=True,
        type=tobool,
        help=bool_help,
    )
    group.add_argument("--no-" + name, dest=dest, action="store_false")


def add_flag_argument(parser, name, dest=None, default=False, help=None):
    """ Add a flag argument to an ArgumentParser instance.
        Either the --flag is present or the --no-flag is present.
        No trying to convert boolean values like the add_boolean_argument
    """
    if not dest:
        dest = name
    group = parser.add_mutually_exclusive_group()
    bool_help = help + " Use --no-" + name + " to turn the feature off."
    group.add_argument(
        "--" + name, dest=dest, default=default, action="store_true", help=bool_help
    )
    group.add_argument(
        "--no-" + name, dest=dest, action="store_false", default=not default
    )


def removemount(absolutepath):
    """ Remove the '/' on unix and (TODO) 'C:\' on Windows """
    return absolutepath[1:]


def ordered_unique(iterable):
    """Return unique items from iterable preserving insertion order.
    
    Uses dict.fromkeys() which is guaranteed to preserve insertion 
    order in Python 3.7+. This replaces OrderedSet for most use cases.
    """
    return list(dict.fromkeys(iterable))


def ordered_union(*iterables):
    """Return union of multiple iterables preserving order.
    
    Uses dict.fromkeys() to maintain insertion order and uniqueness.
    This replaces OrderedSet union operations.
    """
    import itertools
    return list(dict.fromkeys(itertools.chain(*iterables)))


def ordered_difference(iterable, subtract):
    """Return items from iterable not in subtract, preserving order.
    
    This replaces OrderedSet difference operations.
    """
    subtract_set = set(subtract)
    return [item for item in dict.fromkeys(iterable) if item not in subtract_set]
