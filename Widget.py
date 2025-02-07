import tkinter as tk
from tkinter import Toplevel, colorchooser
import requests
from datetime import datetime, timedelta
import math
from geopy.geocoders import Nominatim
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import threading
import ctypes
from tkinter import messagebox
from timezonefinder import TimezoneFinder
import pytz
import random
import sys
import os
_ = lambda s: s

sun_color = "white"
text_color = "white"
line_color = "white"
label_color = "white"
icon = None
info_window = None

API_URL = "https://api.sunrise-sunset.org/json"

def get_geolocation():
    try:
        response = requests.get("https://ipinfo.io", timeout=5)
        data = response.json()
        location = data["loc"].split(",")
        city = data["city"]
        return float(location[0]), float(location[1]), city
    except Exception as e:
        print(f"{_('Geolocation error')}: {e}")
        return 50.4501, 30.5234, _("Kyiv")

def get_timezone(lat, lng):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=lng, lat=lat)
    if timezone_str:
        return pytz.timezone(timezone_str)
    else:
        return None

def fetch_sun_data(lat, lng):
    timezone = get_timezone(lat, lng)
    params = {"lat": lat, "lng": lng, "formatted": 0}
    response = requests.get(API_URL, params=params)
    if response.status_code == 200 and timezone:
        data = response.json()["results"]

        sunrise = datetime.fromisoformat(data["sunrise"]).astimezone(timezone)
        sunset = datetime.fromisoformat(data["sunset"]).astimezone(timezone)
        solar_noon = datetime.fromisoformat(data["solar_noon"]).astimezone(timezone)
        day_length = int(data["day_length"])

        civil_twilight_begin = datetime.fromisoformat(data["civil_twilight_begin"]).astimezone(timezone)
        civil_twilight_end = datetime.fromisoformat(data["civil_twilight_end"]).astimezone(timezone)
        nautical_twilight_begin = datetime.fromisoformat(data["nautical_twilight_begin"]).astimezone(timezone)
        nautical_twilight_end = datetime.fromisoformat(data["nautical_twilight_end"]).astimezone(timezone)
        astronomical_twilight_begin = datetime.fromisoformat(data["astronomical_twilight_begin"]).astimezone(timezone)
        astronomical_twilight_end = datetime.fromisoformat(data["astronomical_twilight_end"]).astimezone(timezone)

        return (sunrise, sunset, solar_noon, day_length,
                civil_twilight_begin, civil_twilight_end,
                nautical_twilight_begin, nautical_twilight_end,
                astronomical_twilight_begin, astronomical_twilight_end)
    else:
        return (None,) * 10

def update_widget():
    global latitude, longitude, city_name, sunrise_time, sunset_time
    global solar_noon, day_length, civil_twilight_begin, civil_twilight_end
    global nautical_twilight_begin, nautical_twilight_end
    global astronomical_twilight_begin, astronomical_twilight_end
    global timezone

    latitude, longitude, city_name = get_geolocation()
    timezone = get_timezone(latitude, longitude)
    (sunrise_time, sunset_time, solar_noon, day_length,
     civil_twilight_begin, civil_twilight_end,
     nautical_twilight_begin, nautical_twilight_end,
     astronomical_twilight_begin, astronomical_twilight_end) = fetch_sun_data(latitude, longitude)

    city_label.config(text=city_name)
    date_label.config(text=datetime.now(timezone).strftime("%d.%m"))
    if sunrise_time and sunset_time:
        sunrise_label.config(text=f"↑ {sunrise_time.strftime('%H:%M')}")
        sunset_label.config(text=f"↓ {sunset_time.strftime('%H:%M')}")
        solar_noon_label.config(text=_("Solar noon: ") + solar_noon.strftime('%H:%M'))
        day_length_label.config(text=_("Day length: ") + f"{day_length // 3600} " + _("hrs") + f" {day_length % 3600 // 60} " + _("mins"))
    else:
        sunrise_label.config(text="↑ --:--")
        sunset_label.config(text="↓ --:--")
        solar_noon_label.config(text=_("Solar noon: --:--"))
        day_length_label.config(text=_("Day length: -- hrs -- mins"))

    update_time()

def change_color():
    global sun_color, text_color, line_color, label_color

    color_code = colorchooser.askcolor(parent=root, title=_("Choose a color"))[1]

    root.update_idletasks()
    root.attributes('-topmost', False)
    root.lower()

    if color_code:
        sun_color = color_code
        text_color = color_code
        line_color = color_code
        label_color = color_code
        city_label.config(fg=text_color)
        date_label.config(fg=text_color)
        time_label.config(fg=text_color)
        sunrise_label.config(fg=text_color)
        sunset_label.config(fg=text_color)
        solar_noon_label.config(fg=text_color)
        day_length_label.config(fg=text_color)
        draw_sun_graph(canvas, sunrise_time, sunset_time, datetime.now().time(), sun_color)
    root.update_idletasks()
    root.attributes('-topmost', False)
    root.lower()

def draw_sun_graph(canvas, sunrise, sunset, now, sun_color):
    canvas.delete("all")
    width, height = 400, 120
    center_y = height // 2
    canvas.create_line(0, center_y, width, center_y, fill=sun_color, width=3)

    if sunrise and sunset:
        day_duration = (sunset - sunrise).total_seconds()
        night_duration = 24 * 3600 - day_duration

        day_proportion = day_duration / (24 * 3600)
        night_proportion = night_duration / (24 * 3600)
        night_proportion_half = night_proportion / 2

        night_end_1 = night_proportion_half
        day_start = night_end_1
        day_end = night_end_1 + day_proportion
        night_start_2 = day_end

        sunrise_x = width * night_end_1
        sunset_x = width * day_end

        full_day_seconds = 24 * 3600
        sunrise_seconds = (sunrise - sunrise.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        sunset_seconds = (sunset - sunset.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        now_seconds = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

        full_progress = now_seconds / full_day_seconds

        if full_progress < night_end_1:
            night_progress = full_progress / night_end_1
            current_x = 0 + sunrise_x * night_progress
            current_y = center_y + 50 * math.sin(night_progress * math.pi)

        elif full_progress < day_end:
            day_progress = (full_progress - day_start) / (day_end - day_start)
            current_x = sunrise_x + (sunset_x - sunrise_x) * day_progress
            current_y = center_y - 50 * math.sin(day_progress * math.pi)

        else:
            night_progress = (full_progress - day_end) / (1 - day_end)
            current_x = sunset_x + (width - sunset_x) * night_progress
            current_y = center_y + 50 * math.sin(night_progress * math.pi)

        points_upper = []
        points_lower = []

        for t in range(int(width * night_end_1) + 1):
            p = t / (width * night_end_1)
            x = 0 + sunrise_x * p
            y = center_y + 50 * math.sin(p * math.pi)
            points_lower.append((x, y))

        for t in range(int(width * day_proportion) + 1):
            p = t / (width * day_proportion)
            x = sunrise_x + (sunset_x - sunrise_x) * p
            y = center_y - 50 * math.sin(p * math.pi)
            points_upper.append((x, y))

        for t in range(int(width * night_proportion_half) + 1):
            p = t / (width * night_proportion_half)
            x = sunset_x + (width - sunset_x) * p
            y = center_y + 50 * math.sin(p * math.pi)
            points_lower.append((x, y))

        for i in range(len(points_lower) - 1):
            canvas.create_line(points_lower[i][0], points_lower[i][1],
                               points_lower[i + 1][0], points_lower[i + 1][1],
                               fill=sun_color, width=1)

        for i in range(len(points_upper) - 1):
            canvas.create_line(points_upper[i][0], points_upper[i][1],
                               points_upper[i + 1][0], points_upper[i + 1][1],
                               fill=sun_color, width=2)

        if sunrise and sunset:
            total_day_seconds = (sunset - sunrise).total_seconds()
            time_since_sunrise = (now - sunrise).total_seconds()
            sun_elevation = max(0, min(1, time_since_sunrise / total_day_seconds))
        else:
            sun_elevation = 0

        max_radius = 15
        min_radius = 10
        current_radius = min_radius + (max_radius - min_radius) * math.sin(sun_elevation * math.pi)

        canvas.create_oval(current_x - current_radius, current_y - current_radius,
                           current_x + current_radius, current_y + current_radius, fill="yellow", outline="")

def update_time():
    now = datetime.now(timezone)
    time_label.config(text=now.strftime("%H:%M"))
    draw_sun_graph(canvas, sunrise_time, sunset_time, now, sun_color)
    root.after(1000, update_time)

def disable_window(window):
    x = window.winfo_rootx()
    y = window.winfo_rooty()
    width = window.winfo_width()
    height = window.winfo_height()
    
    overlay = tk.Toplevel(window)
    overlay.overrideredirect(True)
    overlay.geometry(f"{width}x{height}+{x}+{y}")
    overlay.attributes('-alpha', 0.0)
    overlay.lift(window)
    overlay.grab_set()
    window.overlay = overlay

def enable_window(window):
    if hasattr(window, 'overlay'):
        window.overlay.destroy()
        del window.overlay

def configure_widget():
    hwnd = ctypes.windll.user32.FindWindowW(None, "Sunrise-Sunset Widget")
    if hwnd:
        hProgMan = ctypes.windll.user32.FindWindowW("Progman", None)
        if hProgMan:
            ctypes.windll.user32.SetParent(hwnd, hProgMan)

        HWND_BOTTOM = 1
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOACTIVATE = 0x0010
        SWP_SHOWWINDOW = 0x0040

        ctypes.windll.user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                                          SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)

    root.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")

def create_image():
    image = Image.open("widget-icon-512x512-km18qrtt.png")
    return image

def enable_move_mode(icon, item):
    enable_window(root)
    if hasattr(root, 'move_square') and root.move_square.winfo_exists():
        return

    move_square = tk.Label(root, bg="gray", width=2, height=1)
    move_square.place(x=window_width - 35, y=10)

    def start_move(event):
        root.x = event.x_root
        root.y = event.y_root

    def do_move(event):
        delta_x = event.x_root - root.x
        delta_y = event.y_root - root.y
        new_x = root.winfo_x() + delta_x
        new_y = root.winfo_y() + delta_y
        root.geometry(f"+{new_x}+{new_y}")
        root.x = event.x_root
        root.y = event.y_root

    def stop_move(event):
        move_square.destroy()
        disable_window(root)
    
    def on_enter(event):
        move_square['bg'] = 'lightgray'

    def on_leave(event):
        move_square['bg'] = 'gray'

    move_square.bind('<Enter>', on_enter)
    move_square.bind('<Leave>', on_leave)
    move_square.bind("<ButtonPress-1>", start_move)
    move_square.bind("<B1-Motion>", do_move)
    move_square.bind("<ButtonRelease-1>", stop_move)
    move_square.configure(cursor="fleur")

def close_widget():
    if icon is not None:
        icon.visible = False
        icon.stop()
    root.destroy()
    
def on_quit(icon, item):
    """Закриття програми через трей."""
    if icon is not None:
        icon.visible = False
        icon.stop()
    if root is not None:
        root.destroy()
    sys.exit()

def open_extended_info():
    global latitude, longitude, info_window, info_label

    enable_window(root)

    if info_window is not None and info_window.winfo_exists():
        return

    (sunrise_time, sunset_time, solar_noon, day_length,
     civil_twilight_begin, civil_twilight_end,
     nautical_twilight_begin, nautical_twilight_end,
     astronomical_twilight_begin, astronomical_twilight_end) = fetch_sun_data(latitude, longitude)

    info_window = tk.Toplevel(root)
    info_window.geometry("350x300")
    info_window.configure(bg="#94B6BA")
    info_window.overrideredirect(True)
    info_window.attributes('-transparentcolor', '#94B6BA')

    def close_info_window(event=None):
        global info_window
        if info_window is not None:
            info_window.destroy()
            info_window = None
            disable_window(root)

    content_frame = tk.Frame(info_window, bg="#94B6BA")
    content_frame.pack(fill=tk.BOTH, expand=True)

    close_button = tk.Button(content_frame, text="✖", command=close_info_window, bg="#94B6BA", fg="white", bd=0, font=("Arial", 16))
    close_button.place(x=320, y=5)
    close_button.lift()

    drag_area = tk.Label(content_frame, bg="gray", width=2, height=1)
    drag_area.place(x=290, y=5)
    def start_move(event):
        info_window.x = event.x_root
        info_window.y = event.y_root
    def do_move(event):
        delta_x = event.x_root - info_window.x
        delta_y = event.y_root - info_window.y
        x = info_window.winfo_x() + delta_x
        y = info_window.winfo_y() + delta_y
        info_window.geometry(f"+{x}+{y}")
        info_window.x = event.x_root
        info_window.y = event.y_root
    drag_area.bind("<Button-1>", start_move)
    drag_area.bind("<B1-Motion>", do_move)
    drag_area.configure(cursor="fleur")

    info_text = (
        _("Solar noon: ") + solar_noon.strftime('%H:%M:%S') + "\n" +
        _("Day length: ") + f"{day_length // 3600} " + _("hrs") + f" {day_length % 3600 // 60} " + _("mins") + "\n\n" +
        _("Civil twilight begin: ") + civil_twilight_begin.strftime('%H:%M:%S') + "\n" +
        _("Civil twilight end: ") + civil_twilight_end.strftime('%H:%M:%S') + "\n\n" +
        _("Nautical twilight begin: ") + nautical_twilight_begin.strftime('%H:%M:%S') + "\n" +
        _("Nautical twilight end: ") + nautical_twilight_end.strftime('%H:%M:%S') + "\n\n" +
        _("Astronomical twilight begin: ") + astronomical_twilight_begin.strftime('%H:%M:%S') + "\n" +
        _("Astronomical twilight end: ") + astronomical_twilight_end.strftime('%H:%M:%S')
    )
    info_label = tk.Label(content_frame, text=info_text, justify=tk.LEFT, font=("Arial", 12), 
                      bg="#94B6BA", fg="white", highlightthickness=0)

    info_label.pack(padx=20, pady=40)

def setup_tray():
    global icon
    image = create_image()

    tray_menu = Menu(
        MenuItem(_("Move"), enable_move_mode),
        MenuItem(_("Change color"), change_color),
        MenuItem(_("Extended info"), open_extended_info),
        MenuItem(_("Quit"), on_quit)
    )

    icon = Icon("SunWidget", image, menu=tray_menu)
    icon.run_detached()

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", False)
disable_window(root)
root.lower()
root.title("Sunrise-Sunset Widget")

transparent_color = "#94B6BA"
root.configure(bg=transparent_color)
root.wm_attributes("-transparentcolor", transparent_color)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.3)
window_height = int(screen_height * 0.3)
position_left = (screen_width - window_width) // 2
position_top = int(screen_height * 0.2) - window_height // 2
root.geometry(f"{window_width}x{window_height}+{position_left}+{position_top}")

city_label = tk.Label(root, text="--", font=("Arial", 24), fg="white", bg="#94B6BA")
city_label.pack()

date_label = tk.Label(root, text="--.--", font=("Arial", 24), fg="white", bg="#94B6BA")
date_label.pack()

time_label = tk.Label(root, text=datetime.now().strftime("%H:%M"), font=("Arial", 32), fg="white", bg="#94B6BA")
time_label.pack()

solar_noon_label = tk.Label(root, text=_("Solar noon: --:--"), font=("Arial", 16), fg="white", bg="#94B6BA")
solar_noon_label.pack()

day_length_label = tk.Label(root, text=_("Day length: -- hrs -- mins"), font=("Arial", 16), fg="white", bg="#94B6BA")
day_length_label.pack()

sunrise_label = tk.Label(root, text="↑ --:--", font=("Arial", 24), fg="white", bg="#94B6BA")
sunrise_label.pack()

sunset_label = tk.Label(root, text="↓ --:--", font=("Arial", 24), fg="white", bg="#94B6BA")
sunset_label.pack()

canvas = tk.Canvas(root, width=400, height=150, bg="#94B6BA", highlightthickness=0)
canvas.pack()

setup_tray()
update_widget()
root.mainloop()
