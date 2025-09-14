#!/usr/bin/env python3

# Copyright (C) 2025 Kian-Meng, Ang
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""A console program to manipulate videos.

website: https://github.com/kianmeng/videolab
changelog: https://github.com/kianmeng/videolab/blob/master/CHANGELOG.md
issues: https://github.com/kianmeng/videolab/issues
"""

import argparse

from videolab import __version__
import videolab.commands


def main(argv=None):
    """
    Main function to setup and run the CLI.
    """
    parser = argparse.ArgumentParser(
        prog="videolab",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")

    # Discover and register subcommands
    videolab.commands.discover_and_register(subparsers)

    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
