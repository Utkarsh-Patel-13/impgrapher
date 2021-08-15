from argparse import ArgumentParser

from impgraph.walker import Walker
from impgraph.grapher import Grapher


def main():

    parser = ArgumentParser(
        description='A simple tool to graph imports of a python project or file.')

    parser.add_argument("path", help="path to project/file location")
    parser.add_argument(
        "-j", "--json", help="output json path, no json file will ouptut if not provided.")
    parser.add_argument(
        "-i", "--image", help="output image path, default 'graph.png'", default="graph.png")
    parser.add_argument(
        "-l", "--layout", help="graph layout, ['neato'|'dot'|'twopi'|'circo'|'fdp'|'nop'], default 'neato'", default="neato")
    parser.add_argument(
        "-std-lib", action="store_false", help="include standard libraries")

    args = parser.parse_args()

    walker = Walker(args.path, args.std_lib)
    walker.walk()

    if args.json:
        walker.save_as_json(args.json)

    grapher = Grapher(walker.imports, args.layout)

    grapher.plot_graph(args.image)


if __name__ == "__main__":
    main()
