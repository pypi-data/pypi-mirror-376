# mc_plugin_strcreator/cli.py

import argparse
from mc_plugin_strcreator.generator import create_mc_pl_src

def main():
    parser = argparse.ArgumentParser(
        prog="plugincreate",
        description="Scaffold a Minecraft plugin project structure."
    )

    parser.add_argument(
        "--name", "-n",
        required=True,
        help="The plugin name (e.g., MyPlugin)"
    )
    parser.add_argument(
        "--author", "-a",
        required=True,
        help="The plugin author (e.g., NotGamerPratham)"
    )

    args = parser.parse_args()

    # Call generator function
    create_mc_pl_src(plugin_name=args.name, author_name=args.author)

    print(f"\nPlugin structure for '{args.name}' created successfully by {args.author}!")

if __name__ == "__main__":
    main()
