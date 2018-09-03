#!/usr/bin/env python3
"""Convert markdown to other formats.

Usage:

    $ markit markdown-file [outputs] [options]

The markdown-file should typically have a name ending in .md that
conforms to regular markdown syntax as understood by pandoc. The
following outputs may be generated:

  {outputs}

The following options are recognized:

-c     - continuous run, update whenever the markdown file changes.
-h     - show this help text.
-V     - verbose output

Author:
    Geir Arne Hjelle, <geirarne@gmail.com>.

"""
from configparser import ConfigParser
import os.path
import subprocess
import sys
import time

PANDOC = 'pandoc -f markdown'.split()
CONVERTERS = dict()


def main():
    """Check input and start script.
    """
    read_converters()
    arguments = [a for a in sys.argv[1:] if not a.startswith('-')]
    options = set(''.join(a for a in sys.argv[1:] if a.startswith('-')).replace('-', ''))

    for format in CONVERTERS:
        if format.startswith('_'):
            continue
        if format in arguments:
            arguments.remove(format)
        else:
            CONVERTERS[format] = None

    if len(arguments) != 1 or 'h' in options:
        print_help()
        sys.exit(0)

    if 'c' in options:
        try:
            run_continuously(arguments[0], verbose='V' in options)
        except KeyboardInterrupt:
            sys.exit(0)

    markdown_to_other(arguments[0], 'V' in options)


def markdown_to_other(filename, verbose=False):
    """Use pandoc to convert filename from markdown to other outputs.
    """
    for name, converter in CONVERTERS.items():
        if converter is None:
            continue

        stdin = None
        for command in converter.get('first', dict()):
            cmd = [s.format(infile=filename) for s in command]
            print('First running "{}" for {}'.format(' '.join(cmd), name))
            process = subprocess.run(cmd, stdout=subprocess.PIPE)
            stdin = process.stdout

        outfile = os.path.splitext(filename)[0] + '.' + converter['extension']
        cmd = PANDOC + converter['command'] + ['-o', outfile]
        if not stdin:
            cmd += [filename]
        if verbose:
            print(' '.join(cmd))
        print('Writing {} to {}'.format(name.title(), outfile))
        subprocess.run(cmd, input=stdin)

        for command in converter.get('also', dict()):
            cmd = [s.format(outfile=outfile) for s in command]
            print('Also running "{}" for {}'.format(' '.join(cmd), name))
            subprocess.run(cmd)


def run_continuously(filename, timestamp=None, verbose=False):
    if timestamp:
        print('\nWatching for updates to {}. Use Ctrl-C to stop.\n'.format(filename))

    while True:
        current_timestamp = os.path.getmtime(filename)
        if current_timestamp != timestamp:
            break
        time.sleep(0.5)

    markdown_to_other(filename, verbose=verbose)
    return run_continuously(filename, timestamp=current_timestamp, verbose=verbose)


def read_converters():
    base_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config', 'markit.conf')
    config = ConfigParser()
    config.read(config_path)

    for converter in config.sections():
        CONVERTERS.setdefault(converter, dict())
        CONVERTERS[converter]['extension'] = config[converter]['extension']
        CONVERTERS[converter]['command'] = config[converter]['command'].split()
        if 'first' in config[converter]:
            CONVERTERS[converter]['first'] = [c.split() for c in config[converter]['first'].split(';')]
        if 'also' in config[converter]:
            CONVERTERS[converter]['also'] = [c.split() for c in config[converter]['also'].split(';')]


def print_help():
    """Print help text to screen based on the module docstring.
    """
    print(__doc__.format(outputs=', '.join(sorted(CONVERTERS))))


if __name__ == '__main__':
    main()
