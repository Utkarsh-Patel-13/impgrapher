import pygraphviz as pgv
import json


class Grapher:
    """Class to graph the data
    """

    def __init__(self, data):
        self.import_data = data

    def plot_graph(self):
        dep = {}

        user_modules = list(self.import_data.keys())

        for i in self.import_data:
            imp = self.import_data[i]["imports"]
            imp = [i.split(".")[0] for i in imp]
            imp = list(dict.fromkeys(imp))

            if i not in dep:
                dep[i] = imp

            for x in imp:
                if x.split(".")[0] not in dep:
                    dep[x.split(".")[0]] = []

        G = pgv.AGraph(strict=False, directed=True, overlap="scale")

        for i in dep:

            if i not in user_modules:
                G.add_node(i, color="red", shape="square")
            else:
                G.add_node(i)

        for i in dep:
            for j in dep[i]:
                if j not in user_modules:
                    G.add_edge(j, i, color="lightgreen")
                else:
                    G.add_edge(j, i)

        G.layout(prog="circo")
        G.draw("grp.png")
