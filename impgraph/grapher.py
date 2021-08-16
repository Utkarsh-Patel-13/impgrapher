import pygraphviz as pgv


class Grapher:
    """Class to graph the data"""

    def __init__(self, data, layout="neato",format):
        self.import_data = data
        self.layout = layout
        self.format = format

    def plot_graph(self, image_path):
        """Plot the graph"""
        user_modules = list(self.import_data.keys())

        G = pgv.AGraph(strict=False, directed=True, overlap="scale")

        for i in self.import_data:
            for j in self.import_data[i]["imports"]:
                G.add_edge(j, i)  # ! Hoist repeated if condition statement
        if self.layout not in ["neato", "dot", "twopi", "circo", "fdp", "nop"]:
            self.layout = "neato"

        G.layout(prog=self.layout)
        
        G.draw(image_path,format=self.format)
