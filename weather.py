from tkinter import *
import requests
import feedparser
import traceback
from PIL import Image, ImageTk
import json
import time
import locale
import threading


from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

news_country_code = 'CA'
ui_locale = ''
date_format = '%b %d, %Y'
time_format = 12
latitude = None
longitude = None
weather_api_token = '04c1f524e4f8c698253208463c445398'
weather_unit = 'metric'  # imperial/metric. will be kelvin if empty by default
forecast_hours = 3
xlarge_text_size = 94
large_text_size = 48
medium_text_size = 28
small_text_size = 18

icon_lookup = {
    '01d': 'assets/Sun.png',
    '02d': 'assets/FewCloudSun.png',
    '03d': 'assets/CloudySun.png',
    '04d': 'assets/VeryCloudySun.png',
    '09d': 'assets/HeavyRain.png',
    '10d': 'assets/RainSun.png',
    '11d': 'assets/StormSun.png',
    '13d': 'assets/Snow.png',
    '50d': 'assets/Mist.png',
    '01n': 'assets/Moon.png',
    '02n': 'assets/FewCloudMoon.png',
    '03n': 'assets/CloudyMoon.png',
    '04n': 'assets/VeryCloudyMoon.png',
    '09n': 'assets/HeavyRain.png',
    '10n': 'assets/RainMoon.png',
    '11n': 'assets/StormMoon.png',
    '13n': 'assets/Snow.png',
    '50n': 'assets/Mist'
}


@contextmanager
def setlocale(name):
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_ALL)
        try:
            yield locale.setlocale(locale.LC_ALL, name)
        finally:
            locale.setlocale(locale.LC_ALL, saved)


class Clock(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.time1 = ''
        self.time_label = Label(self, font=('Helvetica', large_text_size), fg='white', bg='black')
        self.time_label.pack(side=TOP, anchor=E)

        self.day_of_week1 = ''
        self.day_of_week1_label = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg='white', bg='black')
        self.day_of_week1_label.pack(side=TOP, anchor=E)

        self.date1 = ''
        self.date1_label = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg='white', bg='black')
        self.date1_label.pack(side=TOP, anchor=E)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p')
            else:
                time2 = time.strftime('%H:%M')

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)

            if time2 != self.time1:
                self.time1 = time2
                self.time_label.config(text=time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.day_of_week1_label.config(text=day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.date1_label.config(text=date2)
            self.time_label.after(200, self.tick)


class Weather(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, bg='black')
        self.temperature = ''
        self.forecast = ''
        self.location = ''
        self.currently = ''
        self.icon = ''
        self.degree_frame = Frame(self, bg='black')
        self.degree_frame.pack(side=TOP, anchor=W)
        self.temperature_label = Label(self.degree_frame, font=('Helvetica', xlarge_text_size), fg='white', bg='black')
        self.temperature_label.pack(side=LEFT, anchor=N)
        self.icon_label = Label(self.degree_frame, bg='black')
        self.icon_label.pack(side=TOP, anchor=W)
        self.currently_label = Label(self, font=('Helvetica', medium_text_size), fg='white', bg='black')
        self.currently_label.pack(side=TOP, anchor=W)
        self.forecast_label = Label(self, font=('Helvetica', small_text_size), fg='white', bg='black')
        self.forecast_label.pack(side=TOP, anchor=W)
        self.location_label = Label(self, font=('Helvetica', small_text_size), fg='white', bg='black')
        self.location_label.pack(side=TOP, anchor=W)
        self.get_weather()

    @staticmethod
    def get_ip():
        try:
            ip_url = 'https://jsonip.com/'
            req = requests.get(ip_url)
            ip_json = json.loads(req.text)
            return ip_json['ip']
        except Exception as e:
            traceback.print_exc()
            return f'Error: {e}. Cannot get ip.'

    @staticmethod
    def next_weather_x_hour(data: dict, x: int):
        current_time = data['current']['dt']
        next_weather = ''
        for value in data['hourly']:
            if ((current_time + x * 3600) < value['dt']) and (value['dt'] < (current_time + (x + 1) * 3600)):
                next_weather = value['weather'][0]['description']
        return next_weather

    def get_weather(self):
        try:
            if latitude is None and longitude is None:
                location_req_url = f'https://freegeoip.app/json/{self.get_ip()}'
                r = requests.get(location_req_url)
                location_json = json.loads(r.text)

                lat = location_json['latitude']
                lon = location_json['longitude']
                location2 = f'{location_json["city"]}, {location_json["region_code"]}'

                weather_req_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,daily&appid={weather_api_token}&units={weather_unit}'
            else:
                location2 = ''
                weather_req_url = f'https://api.openweathermap.org/data/2.5/onecall?lat={latitude}&lon={longitude}&exclude=minutely,daily&appid={weather_api_token}&units={weather_unit}'

            r = requests.get(weather_req_url)
            weather_json = json.loads(r.text)

            degree_sign = u"\N{DEGREE SIGN}"
            temperature2 = f'{int(weather_json["current"]["temp"])}{degree_sign}'
            currently2 = f'{weather_json["current"]["weather"][0]["description"]}'.title()
            forecast2 = f'{self.next_weather_x_hour(weather_json, forecast_hours)}'.title() + f' in {forecast_hours} hours'

            icon_id = weather_json['current']['weather'][0]['icon']
            icon2 = None

            if icon_id in icon_lookup:
                icon2 = icon_lookup[icon_id]

            if icon2 is not None:
                if self.icon != icon2:
                    self.icon = icon2
                    image = Image.open(icon2)
                    image = image.resize((100, 100), Image.ANTIALIAS)
                    image = image.convert('RGBA')
                    image = image.convert('RGB')
                    photo = ImageTk.PhotoImage(image)

                    self.icon_label.config(image=photo)
                    self.icon_label.image = photo

            if self.temperature != temperature2:
                self.temperature = temperature2
                self.temperature_label.config(text=temperature2)
            if self.currently != currently2:
                self.currently = currently2
                self.currently_label.config(text=currently2)
            if self.forecast != forecast2:
                self.forecast = forecast2
                self.forecast_label.config(text=forecast2)
            if self.location != location2:
                if location2 == ', ':
                    self.location = 'Cannot Pinpoint Location'
                    self.location_label.config(text='Cannot Pinpoint Location')
                else:
                    self.location = location2
                    self.location_label.config(text=location2)

        except Exception as e:
            traceback.print_exc()
            return f'Error: {e}. Cannot get weather.'

        self.after(600000, self.get_weather)


class News(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.config(bg='black')
        self.title = 'News'
        self.news_label = Label(self, text=self.title, font=('Helvetica', medium_text_size), fg='white', bg='black')
        self.news_label.pack(side=TOP, anchor=W)
        self.headlines_container = Frame(self, bg='black')
        self.headlines_container.pack(side=TOP)
        self.get_headlines()

    def get_headlines(self):
        try:
            for widget in self.headlines_container.winfo_children():
                widget.destroy()
            if news_country_code == '':
                headlines_url = 'https://news.google.com/news?ned=us&output=rss'
            else:
                headlines_url = f'https://news.google.com/news?ned={news_country_code}&output=rss'
            feed = feedparser.parse(headlines_url)
            for post in feed.entries[0:5]:
                post_entries = post.title.rsplit('-', maxsplit=1)
                news_outlet = f' - {post_entries[1]}'
                headline = (post_entries[0][:100].rsplit(' ', maxsplit=1)[0]+'...') if len(post_entries[0]) > 100 else post_entries[0]

                headline = NewsHeadline(self.headlines_container, headline + news_outlet)
                headline.pack(side=TOP, anchor=W)
        except Exception as e:
            traceback.print_exc()
            print(f'Error: {e}. Cannot get news')

        self.after(600000, self.get_headlines)


class NewsHeadline(Frame):
    def __init__(self, parent, event_name=''):
        Frame.__init__(self, parent, bg='black')

        image = Image.open('assets/NewsPaper.png')
        image = image.resize((25,25), Image.ANTIALIAS)
        image = image.convert('RGB')
        photo = ImageTk.PhotoImage(image)

        self.icon_label = Label(self, bg='black', image=photo)
        self.icon_label.image = photo
        self.icon_label.pack(side=LEFT, anchor=N)

        self.event_name = event_name
        self.event_name_label = Label(self, text=self.event_name, font=('Helvetica', small_text_size), fg='white', bg='black')
        self.event_name_label.pack(side=LEFT, anchor=N)


class Fullscreen_Window:
    def __init__(self):
        self.tk = Tk()
        self.tk.title('Smart Home')
        self.tk.configure(background='black')
        self.top_frame = Frame(self.tk, background='black')
        self.top_frame.pack(side=TOP, fill=BOTH, expand=YES)
        self.bottom_frame = Frame(self.tk, background='black')
        self.bottom_frame.pack(side=BOTTOM, fill=BOTH, expand=YES)
        self.state = False
        self.tk.bind('<Return>', self.toggle_fullscreen)
        self.tk.bind('<Escape>', self.end_fullscreen)

        self.weather = Weather(self.top_frame)
        self.weather.pack(side=LEFT, anchor=N, padx=60, pady=60)

        self.clock = Clock(self.top_frame)
        self.clock.pack(side=RIGHT, anchor=N, padx=60, pady=60)

        self.news = News(self.bottom_frame)
        self.news.pack(side=LEFT, anchor=S, padx=60, pady=60)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state
        self.tk.attributes('-fullscreen', self.state)
        return 'break'

    def end_fullscreen(self, event=None):
        self.state = False
        self.tk.attributes('-fullscreen', False)
        return 'break'


if __name__ == '__main__':
    w = Fullscreen_Window()
    w.tk.mainloop()
