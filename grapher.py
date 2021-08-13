import pygraphviz as pgv
import json

# # read json
# with open('imports.json') as json_data:
#     data = json.load(json_data)


def plot_graph(data: dict):
    dep = {}

    user_modules = list(data.keys())

    for i in data:
        imp = data[i]["imports"]
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
