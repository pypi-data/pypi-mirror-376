import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.colors import Normalize
from matplotlib.widgets import Cursor
from .spline import *

def disable_plt_keys():
    plt.rcParams['keymap.back'] = []
    plt.rcParams['keymap.forward'] = []
    plt.rcParams['keymap.home'] = []
    plt.rcParams['keymap.pan'] = []
    plt.rcParams['keymap.xscale'] = []
    plt.rcParams['keymap.yscale'] = []
    plt.rcParams['keymap.fullscreen'] = []
    plt.rcParams['keymap.save'] = []

def get_predefined_colors():
    return plt.rcParams['axes.prop_cycle'].by_key()['color']

class Plot:
    def __init__(self):
        self.fig_k, (self.ax_k, self.ax_kv) = plt.subplots(2, 1)
        self.fig_spline, self.ax_spline = plt.subplots()

        self.timer = self.fig_spline.canvas.new_timer(interval=80)

        self.ax_v_k = self.ax_k.twinx()
        self.ax_v_kv = self.ax_kv.twinx()

        self.fig_k.canvas.manager.set_window_title('Curvature Plot')
        self.fig_spline.canvas.manager.set_window_title('Spline Plot')

        self.fig_spline.subplots_adjust(
            left=0.09, right=1., bottom=0.06, top=0.995
        )
        self.fig_k.subplots_adjust(
            hspace=0.3
        )

        self.ax_spline.set_aspect('equal', adjustable='datalim')

        self.ax_kv.xaxis.set_ticks_position('top')
        self.ax_kv.xaxis.set_label_position('top')

        self.ax_k.grid(True)
        self.ax_kv.grid(True)

        self.cursor_k = Cursor(self.ax_k, useblit=True)
        self.cursor_kv = Cursor(self.ax_kv, useblit=True)

        self.ref_color_index = 1
        self.ctrl_pts_color_index = 0
        self.ctrl_poly_color_index = 0
        self.k_color_index = 0
        self.kv_color_index = 0
        self.v_k_color_index = 0
        self.v_kv_color_index = 0

        self._style_index = 0

        self.plot_ref, = self.ax_spline.plot([], [], color='C{}'.format(self.ref_color_index), linestyle='-', linewidth=0.5, label='Collected Points')
        self.plot_ctrl_pts = self.ax_spline.scatter([], [], color='C{}'.format(self.ctrl_pts_color_index), s=60, label='Control Points', picker=True, pickradius=5)
        self.plot_ctrl_poly, = self.ax_spline.plot([], [], color='C{}'.format(self.ctrl_poly_color_index), linestyle='--', linewidth=0.5, label='Control Polygon')

        spline_segments = np.empty((0, 2, 2), dtype=float)
        self.spline_lc = LineCollection(spline_segments, label='BSpline')
        spline_cmap = plt.get_cmap('cividis')
        spline_cmap.set_over(color='red')
        self.spline_lc.set_cmap(spline_cmap)
        self.spline_lc.set_norm(Normalize(vmin=0, vmax=1))
        self.ax_spline.add_collection(self.spline_lc)
        self.spline_cbar = plt.colorbar(self.spline_lc, ax=self.ax_spline, extend='max')

        self.plot_k, = self.ax_k.plot([], [], color='C{}'.format(self.k_color_index), linestyle='-', linewidth=2)
        self.plot_kv, = self.ax_kv.plot([], [], color='C{}'.format(self.kv_color_index), linestyle='-', linewidth=2)
        self.plot_v_k, = self.ax_v_k.plot([], [], color='C{}'.format(self.v_k_color_index), linestyle='-', linewidth=2)
        self.plot_v_kv, = self.ax_v_kv.plot([], [], color='C{}'.format(self.v_kv_color_index), linestyle='-', linewidth=2)

        self.plot_spline_near = self.ax_spline.scatter([], [], color='red', s=80, marker='h')
        self.plot_k_near = self.ax_k.axvline(color='red', visible=False)
        self.plot_kv_near = self.ax_kv.axvline(color='red', visible=False)

    @staticmethod
    def next_color_index(current_index: int) -> int:
        index = current_index + 1
        if index > 9:
            index = 0
        print('Color index:', index)
        return index

    @staticmethod
    def size_up(plot_object):
        new_size = None
        if isinstance(plot_object, Line2D) or isinstance(plot_object, LineCollection):
            lw = plot_object.get_linewidth()
            new_size = min(lw + 0.1, 10.)
            plot_object.set_linewidth(new_size)
        elif isinstance(plot_object, PathCollection):
            sizes = plot_object.get_sizes()
            if len(sizes) > 0:
                new_size = min(sizes[0] + 1, 200)
                plot_object.set_sizes([new_size])
        if new_size is not None:
            print('New size:', new_size)

    @staticmethod
    def size_down(plot_object):
        new_size = None
        if isinstance(plot_object, Line2D) or isinstance(plot_object, LineCollection):
            lw = plot_object.get_linewidth()
            new_size = max(lw - 0.1, 0.1)
            plot_object.set_linewidth(new_size)
        elif isinstance(plot_object, PathCollection):
            sizes = plot_object.get_sizes()
            if len(sizes) > 0:
                new_size = max(sizes[0] - 1, 1)
                plot_object.set_sizes([new_size])
        if new_size is not None:
            print('New size:', new_size)

    def change_plot_style(self, plot_object):
        if isinstance(plot_object, Line2D) or isinstance(plot_object, LineCollection):
            styles = ['-', '--', '-.', ':']
            self._style_index += 1
            if self._style_index >= len(styles):
                self._style_index = 0
            plot_object.set_linestyle(styles[self._style_index])
            print('Change style to:', styles[self._style_index])
