import sys

from walker import Walker
from grapher import Grapher


def main():

    path = sys.argv[1]

    walker = Walker(path)

    walker.walk()

    walker.save_as_json()

    grapher = Grapher(walker.imports)

    grapher.plot_graph()


if __name__ == "__main__":
    main()
