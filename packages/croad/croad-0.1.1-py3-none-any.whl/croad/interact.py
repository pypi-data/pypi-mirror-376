from enum import Enum, auto
from itertools import cycle
from matplotlib import pyplot as plt
from matplotlib.backend_bases import MouseButton, PickEvent, MouseEvent, KeyEvent, ResizeEvent
from scipy.optimize import differential_evolution, minimize
from .utils import *
from .plt import Plot, disable_plt_keys
from .spline import *

class InteractMode(Enum):
    interact = auto()
    fitting = auto()
    plot_ref = auto()
    plot_spline = auto()
    plot_ctrl_pts = auto()
    plot_ctrl_poly = auto()
    plot_k = auto()
    plot_v_k = auto()
    plot_kv = auto()
    plot_v_kv = auto()


def interact(
        bag_path: Path,
        fake_lat: float,
        fake_lon: float,
        fake_alt: float,
):
    if not isinstance(fake_lat, float) or not isinstance(fake_lon, float) or not isinstance(fake_alt, float):
        origin_llh = None
    else:
        origin_llh = (fake_lat, fake_lon, fake_alt)
    enu_array = np.empty((0, 3), dtype=np.float64)
    if bag_path is not None:
        if not bag_path.exists():
            print('bag not exist')
            exit(1)
        llh_list, _ = read_bag_nav_llh_humble(bag_path)
        if len(llh_list) == 0:
            print('no llh data in bag')
            exit(1)
        origin_llh = llh_list[0]
        enu_array = np.array(llh_to_enu(llh_list, origin_llh))
    if origin_llh is None:
        print('origin llh abnormal')
        exit(1)
    print('origin llh: {}'.format(origin_llh))

    disable_plt_keys()
    p = Plot()
    s = InteractiveSpline()

    x = s.x
    length = s.s
    k = s.k
    kv = s.kv

    it_mode = cycle(InteractMode)
    mode = next(it_mode)

    ref_path = np.empty((0, 2), dtype=np.float64)
    minimal_ref_interval = 0.

    fit_method = 'approx'
    fit_centripetal = False
    fit_minimal_interval = 0.
    fit_size = None

    fn_near = False
    fn_resize = True

    domain_near = None
    pick_ctrl_pts_index: int | None = None

    k_bound = 0.1
    kv_bound = 0.1
    max_v = 20.
    max_lat_a = 2.0

    callback_set = set()

    def update_fit():
        if len(ref_path) > s.curve.degree:
            fit = fit_spline(fit_method, ref_path, fit_minimal_interval, s.curve.degree, fit_centripetal, fit_size)
            update_spline_from_fit(s, fit)

    def update_plot_ref():
        nonlocal ref_path
        if len(enu_array) == 0:
            return
        if abs(minimal_ref_interval) < 1e-9:
            ref_path = enu_array[:, :2]
        else:
            points = [enu_array[0, :2]]
            interval2 = minimal_ref_interval ** 2
            for point in enu_array:
                if np.sum((points[-1] - point[:2]) ** 2) >= interval2:
                    points.append(point[:2])
            ref_path = np.array(points)
        p.plot_ref.set_color('C{}'.format(p.ref_color_index))
        p.plot_ref.set_data(ref_path[:, 0], ref_path[:, 1])

    def update_plot_ctrl_pts():
        color = ['C{}'.format(p.ctrl_pts_color_index)] * len(s.ctrl_pts)
        if pick_ctrl_pts_index is not None:
            color[pick_ctrl_pts_index] = 'C{}'.format((p.ctrl_pts_color_index + 3) % 9)
        p.plot_ctrl_pts.set_color(color)
        p.plot_ctrl_pts.set_offsets(s.ctrl_pts)

    def update_plot_ctrl_poly():
        if len(s.ctrl_pts) < 2:
            p.plot_ctrl_poly.set_data([], [])
            return
        p.plot_ctrl_poly.set_color('C{}'.format(p.ctrl_poly_color_index))
        p.plot_ctrl_poly.set_data(s.ctrl_pts[:, 0], s.ctrl_pts[:, 1])

    def update_spline_data():
        s.prepare_curve()
        nonlocal x, length, k, kv
        x = s.x
        length = s.s
        k = s.k
        kv= s.kv

    def update_plot_spline():
        if not s.valid:
            p.spline_lc.set_segments(np.empty((0, 2, 2), dtype=float))
            return
        points = s.points.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        p.spline_lc.set_segments(segments)
        k_abs = np.abs(k)
        p.spline_lc.set_array((k_abs[:-1] + k_abs[1:]) / 2)
        p.spline_lc.norm.vmin = 0.
        p.spline_lc.norm.vmax = k_bound
        p.spline_cbar.update_normal(p.spline_lc)

    def update_plot_k():
        if not s.valid:
            return
        p.plot_k.set_color('C{}'.format(p.k_color_index))
        p.plot_k.set_data(length, k)
        p.ax_k.relim()
        p.ax_k.autoscale_view(scalex=False, scaley=True)
        if len(length) > 1:
            p.ax_k.set_xlim(length[0], length[-1])

    def update_plot_kv():
        if not s.valid:
            return
        p.plot_kv.set_color('C{}'.format(p.kv_color_index))
        p.plot_kv.set_data(x, kv)
        p.ax_kv.relim()
        p.ax_kv.autoscale_view(scalex=False, scaley=True)
        if len(x) > 1:
            p.ax_kv.set_xlim(x[0], x[-1])

    def update_plot_v_k():
        if not s.valid:
            return
        p.plot_v_k.set_color('C{}'.format(p.v_k_color_index))
        p.plot_v_k.set_data(length, np.minimum(np.sqrt(max_lat_a / np.maximum(np.abs(k), 1e-9)), max_v))
        p.ax_v_k.relim()
        p.ax_v_k.autoscale_view(scalex=False, scaley=True)
        if len(length) > 1:
            p.ax_v_k.set_xlim(length[0], length[-1])

    def update_plot_v_kv():
        if not s.valid:
            return
        kv_for_calculate = np.abs(kv).clip(max(1e-9, kv_bound / max(max_v, 1e-9)))
        p.plot_v_kv.set_color('C{}'.format(p.v_kv_color_index))
        p.plot_v_kv.set_data(x, kv_bound / kv_for_calculate)
        p.ax_v_kv.relim()
        p.ax_v_kv.autoscale_view(scalex=False, scaley=True)
        if len(x) > 1:
            p.ax_v_kv.set_xlim(x[0], x[-1])

    def update_plot_near():
        if domain_near is None:
            return
        p.plot_spline_near.set_offsets(s.curve.evaluate_single(domain_near))

    def resize_fig_spline():
        if not fn_resize:
            return
        if not hasattr(resize_fig_spline, '_init'):
            resize_fig_spline.e_min, resize_fig_spline.e_max = 0., 0.
            resize_fig_spline.n_min, resize_fig_spline.n_max = 0., 0.
            if len(enu_array) > 0:
                resize_fig_spline.e_min = np.min(enu_array[:, 0])
                resize_fig_spline.e_max = np.max(enu_array[:, 0])
                resize_fig_spline.n_min = np.min(enu_array[:, 1])
                resize_fig_spline.n_max = np.max(enu_array[:, 1])
            resize_fig_spline._init = True
        x_min = resize_fig_spline.e_min
        x_max = resize_fig_spline.e_max
        y_min = resize_fig_spline.n_min
        y_max = resize_fig_spline.n_max
        if len(s.ctrl_pts) > 0:
            xx, yy = zip(*s.ctrl_pts)
            x_min = min(x_min, min(xx))
            x_max = max(x_max, max(xx))
            y_min = min(y_min, min(yy))
            y_max = max(y_max, max(yy))
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        x_range = max(x_max - x_min, 5) * 1.2
        y_range = max(y_max - y_min, 5) * 1.2
        height = p.ax_spline.get_window_extent().height
        width = p.ax_spline.get_window_extent().width
        if height is None or height <= 0 or width is None or width <= 0:
            aspect = y_range / x_range
        else:
            aspect = height / width
        if y_range / x_range > aspect:
            x_range = y_range / aspect
        else:
            y_range = x_range * aspect
        p.ax_spline.set_xlim(x_center - x_range * 0.5, x_center + x_range * 0.5)
        p.ax_spline.set_ylim(y_center - y_range * 0.5, y_center + y_range * 0.5)

    def update_spline_title():
        title = f'mode: {mode.name}  '
        if mode == InteractMode.interact:
            title += (
                f'save/s  '
                f'near: {fn_near}  '
                f'resize: {fn_resize}  '
                f'clamped: {s.clamped}  '
                f'loop: {s.loop}  '
                f'sample size: {s.sample_size}  '
            )
            if domain_near is not None:
                title += (
                    f'near: {domain_near}  '
                )
        if mode in (
            InteractMode.plot_ref,
            InteractMode.plot_ctrl_pts,
            InteractMode.plot_ctrl_poly,
            InteractMode.plot_spline,
            InteractMode.plot_k,
            InteractMode.plot_kv,
            InteractMode.plot_v_k,
            InteractMode.plot_v_kv,
        ):
            if mode != InteractMode.plot_spline:
                title += 'C/change color  '
            title += (
                'V/visible  '
                'B/line style  '
                'UP/size up  '
                'DOWN/size down  '
            )
        if mode == InteractMode.plot_ref:
            title += ('ref interval/w s x/{}  '.format(minimal_ref_interval))
        if mode == InteractMode.fitting:
            title += (
                f'method/q: {fit_method}  '
                f'centripetal/c: {fit_centripetal}  '
                f'interval/<-->: {fit_minimal_interval}  '
                f'size/up down r: {fit_size}  '
            )
        p.fig_spline.canvas.manager.set_window_title(title)

    def on_pick(event: PickEvent):
        nonlocal pick_ctrl_pts_index
        if event.artist == p.plot_ctrl_pts:
            if hasattr(event, 'ind'):
                if len(event.ind) > 0:
                    pick_ctrl_pts_index = event.ind[0]
                    callback_set.update({
                        update_plot_ctrl_pts,
                        update_spline_title,
                    })

    def on_mouse_press(event: MouseEvent):
        if event.button == MouseButton.RIGHT and event.xdata is not None and event.ydata is not None:
            s.ctrl_pts = np.vstack([s.ctrl_pts, [event.xdata, event.ydata]])
            callback_set.update({
                update_plot_ctrl_pts,
                update_plot_ctrl_poly,
                update_spline_data,
                update_plot_spline,
                update_plot_k,
                update_plot_kv,
                update_plot_v_k,
                update_plot_v_kv,
                update_plot_near,
                resize_fig_spline,
            })

    def on_mouse_release(event: MouseEvent):
        nonlocal pick_ctrl_pts_index
        pick_ctrl_pts_index = None
        callback_set.update({
            update_plot_ctrl_pts,
            update_spline_title,
        })

    def on_mouse_move(event: MouseEvent):
        nonlocal domain_near
        if event.xdata is None or event.ydata is None:
            return
        mouse = np.array([event.xdata, event.ydata])
        if pick_ctrl_pts_index is not None:
            s.ctrl_pts[pick_ctrl_pts_index] = mouse
            callback_set.update({
                update_plot_ctrl_pts,
                update_plot_ctrl_poly,
                update_spline_data,
                update_plot_spline,
                update_plot_k,
                update_plot_kv,
                update_plot_v_k,
                update_plot_v_kv,
                update_plot_near,
                resize_fig_spline,
            })
            return
        if fn_near and s.valid:
            # closet = differential_evolution(
            #     func=lambda u: np.sum((np.array(s.curve.evaluate_single(u[0])) - mouse) ** 2),
            #     bounds=[(s.curve.domain[0], s.curve.domain[1])],
            # )
            closet = minimize(
                fun=lambda u: np.sum((np.array(s.curve.evaluate_single(u[0])) - mouse) ** 2),
                x0=[s.x[np.argmin(np.sum((s.points - mouse) ** 2, axis=1))]],
                bounds=[(s.curve.domain[0], s.curve.domain[1])],
                method='L-BFGS-B',
            )
            if closet.success:
                domain_near = closet.x[0]
                callback_set.add(update_plot_near)
                return
        else:
            domain_near = None

    def on_key_press(event: KeyEvent):
        nonlocal fn_near, fn_resize
        nonlocal pick_ctrl_pts_index
        nonlocal mode
        nonlocal minimal_ref_interval
        nonlocal fit_method, fit_centripetal, fit_minimal_interval, fit_size
        if event.key == 'm':
            mode = next(it_mode)
            callback_set.add(update_spline_title)
            return
        if event.key == 'i':
            mode = InteractMode.interact
            callback_set.add(update_spline_title)
            return

        if event.key == 'c' and mode not in (
                InteractMode.interact,
                InteractMode.fitting,
        ):
            match mode:
                case InteractMode.plot_ref:
                    p.ref_color_index = p.next_color_index(p.ref_color_index)
                    callback_set.add(update_plot_ref)
                    return
                case InteractMode.plot_ctrl_pts:
                    p.ctrl_pts_color_index = p.next_color_index(p.ctrl_pts_color_index)
                    callback_set.add(update_plot_ctrl_pts)
                    return
                case InteractMode.plot_ctrl_poly:
                    p.ctrl_poly_color_index = p.next_color_index(p.ctrl_poly_color_index)
                    callback_set.add(update_plot_ctrl_poly)
                    return
                case InteractMode.plot_k:
                    p.k_color_index = p.next_color_index(p.k_color_index)
                    callback_set.add(update_plot_k)
                    return
                case InteractMode.plot_v_k:
                    p.v_k_color_index = p.next_color_index(p.v_k_color_index)
                    callback_set.add(update_plot_v_k)
                    return
                case InteractMode.plot_kv:
                    p.kv_color_index = p.next_color_index(p.kv_color_index)
                    callback_set.add(update_plot_kv)
                    return
                case InteractMode.plot_v_kv:
                    p.v_kv_color_index = p.next_color_index(p.v_kv_color_index)
                    callback_set.add(update_plot_v_kv)
                    return

        if event.key in ('v', 'b', 'up', 'down') and mode not in (
            InteractMode.interact,
            InteractMode.fitting,
        ):
            target_plot = None
            match mode:
                case InteractMode.plot_ref:
                    target_plot = p.plot_ref
                case InteractMode.plot_spline:
                    target_plot = p.spline_lc
                case InteractMode.plot_ctrl_pts:
                    target_plot = p.plot_ctrl_pts
                case InteractMode.plot_ctrl_poly:
                    target_plot = p.plot_ctrl_poly
                case InteractMode.plot_k:
                    target_plot = p.plot_k
                case InteractMode.plot_v_k:
                    target_plot = p.plot_v_k
                case InteractMode.plot_kv:
                    target_plot = p.plot_kv
                case InteractMode.plot_v_kv:
                    target_plot = p.plot_v_kv
            if target_plot is None:
                return
            match event.key:
                case 'v':
                    target_plot.set_visible(not target_plot.get_visible())
                case 'b':
                    p.change_plot_style(target_plot)
                case 'up':
                    p.size_up(target_plot)
                case 'down':
                    p.size_down(target_plot)
            match mode:
                case InteractMode.plot_ref:
                    callback_set.add(update_plot_ref)
                    return
                case InteractMode.plot_spline:
                    callback_set.add(update_plot_spline)
                    return
                case InteractMode.plot_ctrl_pts:
                    callback_set.add(update_plot_ctrl_pts)
                    return
                case InteractMode.plot_ctrl_poly:
                    callback_set.add(update_plot_ctrl_poly)
                    return
                case InteractMode.plot_k:
                    callback_set.add(update_plot_k)
                    return
                case InteractMode.plot_v_k:
                    callback_set.add(update_plot_v_k)
                    return
                case InteractMode.plot_kv:
                    callback_set.add(update_plot_kv)
                    return
                case InteractMode.plot_v_kv:
                    callback_set.add(update_plot_v_kv)
                    return

        if mode == InteractMode.plot_ref:
            match event.key:
                case 'w':
                    minimal_ref_interval = min(minimal_ref_interval + 0.01, 2.)
                    callback_set.update({
                        update_plot_ref,
                        update_plot_spline,
                    })
                    return
                case 's':
                    minimal_ref_interval = max(minimal_ref_interval - 0.01, 0.)
                    callback_set.update({
                        update_plot_ref,
                        update_plot_spline,
                    })
                    return
                case 'x':
                    minimal_ref_interval = 0.
                    callback_set.update({
                        update_plot_ref,
                        update_plot_spline,
                    })
                    return

        if mode == InteractMode.fitting:
            def update_for_fit():
                callback_set.update({
                    update_fit,
                    update_plot_ctrl_pts,
                    update_plot_ctrl_poly,
                    update_spline_data,
                    update_plot_spline,
                    update_plot_k,
                    update_plot_kv,
                    update_plot_v_k,
                    update_plot_v_kv,
                    update_plot_near,
                    resize_fig_spline,
                    update_spline_title,
                })
            match event.key:
                case 'q':
                    if fit_method == 'approx':
                        fit_method = 'interp'
                    else:
                        fit_method = 'approx'
                    update_for_fit()
                    return
                case 'c':
                    fit_centripetal = not fit_centripetal
                    update_for_fit()
                    return
                case 'w':
                    fit_minimal_interval = max(fit_minimal_interval - 0.1, 0.)
                    update_for_fit()
                    return
                case 's':
                    fit_minimal_interval = min(fit_minimal_interval + 0.1, 10.)
                    update_for_fit()
                    return
                case 'x':
                    fit_minimal_interval = 0.
                    update_for_fit()
                    return
                case 'up':
                    if fit_size is None:
                        fit_size = s.curve.degree + 1
                    else:
                        fit_size = min(fit_size + 5, len(ref_path) - 1)
                    update_for_fit()
                    return
                case 'down':
                    if fit_size is None:
                        fit_size = len(ref_path) - 1
                    else:
                        fit_size = max(fit_size - 5, s.curve.degree + 1)
                    update_for_fit()
                    return
                case 'r':
                    fit_size = None
                    update_for_fit()
                    return
                case 'f':
                    update_for_fit()
                    return

        match event.key:
            case 'n':
                fn_near = not fn_near
                callback_set.update({
                    update_plot_near,
                    update_spline_title,
                })
            case 'r':
                fn_resize = not fn_resize
                callback_set.update({
                    resize_fig_spline,
                    update_spline_title,
                })
            case 'c':
                s.clamped = not s.clamped
                callback_set.update({
                    update_spline_data,
                    update_plot_spline,
                    update_plot_k,
                    update_plot_kv,
                    update_plot_v_k,
                    update_plot_v_kv,
                    update_plot_near,
                    update_spline_title,
                })
            case 'l':
                s.loop = not s.loop
                callback_set.update({
                    update_spline_data,
                    update_plot_spline,
                    update_plot_k,
                    update_plot_kv,
                    update_plot_v_k,
                    update_plot_v_kv,
                    update_plot_near,
                    update_spline_title,
                })
            case 'up':
                s.sample_size = min(s.sample_size + 10, 2000)
                callback_set.update({
                    update_spline_data,
                    update_plot_spline,
                    update_plot_k,
                    update_plot_kv,
                    update_plot_v_k,
                    update_plot_v_kv,
                    update_plot_near,
                    update_spline_title,
                })
            case 'down':
                s.sample_size = max(s.sample_size - 10, 10)
                callback_set.update({
                    update_spline_data,
                    update_plot_spline,
                    update_plot_k,
                    update_plot_kv,
                    update_plot_v_k,
                    update_plot_v_kv,
                    update_plot_near,
                    update_spline_title,
                })
            case 'backspace' | 'delete':
                if pick_ctrl_pts_index is not None:
                    s.ctrl_pts = np.delete(s.ctrl_pts, [pick_ctrl_pts_index], 0)
                    pick_ctrl_pts_index = None
                else:
                    s.ctrl_pts = s.ctrl_pts[:-1]
                callback_set.update({
                    update_plot_ctrl_pts,
                    update_plot_ctrl_poly,
                    update_spline_data,
                    update_plot_spline,
                    update_plot_k,
                    update_plot_kv,
                    update_plot_v_k,
                    update_plot_v_kv,
                    update_plot_near,
                    update_spline_title,
                })
            case 'a':
                if event.xdata is not None and event.ydata is not None:
                    mouse = np.array([event.xdata, event.ydata])
                    point_p = s.ctrl_pts[:-1]
                    point_q = s.ctrl_pts[1:]
                    line_pq = point_q - point_p
                    line_pm = mouse - point_p
                    t = np.sum(line_pq * line_pm, axis=1) / np.sum(line_pq * line_pq, axis=1)
                    point_o = point_p + line_pq * t[:, np.newaxis]
                    d = np.sum((point_o - mouse) ** 2, axis=1)
                    condition = (t >= 0) & (t <= 1)
                    indexes = np.where(condition)[0]
                    if len(indexes) > 0:
                        distances = d[condition]
                        closed_index = indexes[np.argmin(distances)]
                        s.ctrl_pts = np.insert(s.ctrl_pts, closed_index + 1, mouse, axis=0)
                        callback_set.update({
                            update_plot_ctrl_pts,
                            update_plot_ctrl_poly,
                            update_spline_data,
                            update_plot_spline,
                            update_plot_k,
                            update_plot_kv,
                            update_plot_v_k,
                            update_plot_v_kv,
                            update_plot_near,
                            update_spline_title,
                        })
            case 's':
                if s.valid:
                    save_nav_points_to_bag(s.points, origin_llh)
                    print('Saved spline points to bag')

    def on_key_release(event: KeyEvent):
        pass

    def on_resize(event: ResizeEvent):
        callback_set.add(resize_fig_spline)

    function_list = [
        update_plot_ref,
        update_fit,
        update_plot_ctrl_pts,
        update_plot_ctrl_poly,
        update_spline_data,
        update_plot_spline,
        update_plot_k,
        update_plot_kv,
        update_plot_v_k,
        update_plot_v_kv,
        update_plot_near,
        resize_fig_spline,
        update_spline_title,
    ]
    callback_set.update(function_list)
    callback_set.remove(update_fit)

    def timer_callback():
        for func in function_list:
            if func in callback_set:
                func()
        if len(callback_set) > 0:
            p.fig_spline.canvas.draw()
            p.fig_k.canvas.draw_idle()
        callback_set.clear()

    p.timer.add_callback(timer_callback)
    p.timer.start()

    p.fig_spline.canvas.mpl_connect('pick_event', on_pick)
    p.fig_spline.canvas.mpl_connect('button_press_event', on_mouse_press)
    p.fig_spline.canvas.mpl_connect('button_release_event', on_mouse_release)
    p.fig_spline.canvas.mpl_connect('motion_notify_event', on_mouse_move)
    p.fig_spline.canvas.mpl_connect('key_press_event', on_key_press)
    p.fig_spline.canvas.mpl_connect('key_release_event', on_key_release)
    p.fig_spline.canvas.mpl_connect('resize_event', on_resize)

    plt.show()
