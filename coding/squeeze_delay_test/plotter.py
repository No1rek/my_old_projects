import bokeh.plotting as plt
import datetime
import numpy as np

class Plotter:
    def plot(self, case, bks):
        # output to static HTML file
        plt.output_file("lines.html")

        # create a new plot with a title and axis labels
        p = plt.figure(title=f"CHART", x_axis_label='x', y_axis_label='y', x_axis_type='datetime')
        colors = ["red", "green", "blue", "yellow", "pink", "purple", ]
        i = 0

        # TEMP
        xt, yt = [], []
        ys = []

        for ex_name, ex in case.items():
            # add a line renderer with legend and line thickness

            x, y = ex["x"], ex["y"]
            x = [datetime.datetime.fromtimestamp(int(i)) for i in x]
            bk_start_x = [datetime.datetime.fromtimestamp(int(bk["start"]["x"])) for bk in bks[ex_name]]
            bk_start_y = [bk["start"]["y"] for bk in bks[ex_name]]
            bk_end_x = [datetime.datetime.fromtimestamp(int(bk["end"]["x"])) for bk in bks[ex_name]]
            bk_end_y = [bk["end"]["y"] for bk in bks[ex_name]]

            ys.append(y)
            p.line(x, y, legend=ex_name, line_width=2, color=colors[i])
            p.circle(bk_start_x, bk_start_y, legend="bk start", line_width=3, color=colors[-2])
            p.circle(bk_end_x, bk_end_y, legend="bk end", line_width=3, color=colors[-1])
            i = i + 1 % len(colors)

        # show the results
        plt.show(p)

