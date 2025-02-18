import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import webbrowser
import pandas as pd
import requests
from pandas import json_normalize
from sklearn.cluster import KMeans
import folium
from opencage.geocoder import OpenCageGeocode
import os

# Define API keys
api_key = 'dfcff1167dde40a4b522e486ee87bfd9'
here_api_key = 'lRK9iydRZwutZaGGXq88tdcqVZUssRZwUohcP7LTI5Y'

# Ensure 'api-data' directory exists
if not os.path.exists('api-data'):
    os.makedirs('api-data')

# Function to get latitude and longitude from a user-entered location
def get_lat_lon(location, api_key):
    geocoder = OpenCageGeocode(api_key)
    result = geocoder.geocode(location)
    if result and len(result):
        return result[0]['geometry']['lat'], result[0]['geometry']['lng']
    else:
        return None, None

def fetch_and_process_data(location):
    global d2
    latitude, longitude = get_lat_lon(location, api_key)
    if latitude is None or longitude is None:
        messagebox.showerror("Error", "Unable to geocode the provided location.")
        return

    url = f'https://discover.search.hereapi.com/v1/discover?in=circle:{latitude},{longitude};r=10000000&q=pg&apiKey={here_api_key}'
    data = requests.get(url).json()
    d = json_normalize(data['items'])
    d.to_csv('api-data/dsdata1.csv')

    columns_to_keep = ['title', 'address.label', 'distance', 'position.lat', 'position.lng', 'id']
    if 'access' in d.columns:
        columns_to_keep.append('access')
    if 'address.postalCode' in d.columns:
        columns_to_keep.append('address.postalCode')

    d2 = d[columns_to_keep]
    d2.to_csv('api-data/dsdata.csv')

    df_final = d2[['position.lat', 'position.lng']]

    CafeList = []
    ResList = []
    GymList = []
    latitudes = list(d2['position.lat'])
    longitudes = list(d2['position.lng'])
    for lat, lng in zip(latitudes, longitudes):    
        radius = '1000'
        
        search_query = 'cafe'
        url = f'https://discover.search.hereapi.com/v1/discover?in=circle:{lat},{lng};r={radius}&q={search_query}&apiKey={here_api_key}'
        results = requests.get(url).json()
        venues = json_normalize(results['items'])
        CafeList.append(venues['title'].count())
        
        search_query = 'gym'
        url = f'https://discover.search.hereapi.com/v1/discover?in=circle:{lat},{lng};r={radius}&q={search_query}&apiKey={here_api_key}'
        results = requests.get(url).json()
        venues = json_normalize(results['items'])
        GymList.append(venues['title'].count())

        search_query = 'restaurant'
        url = f'https://discover.search.hereapi.com/v1/discover?in=circle:{lat},{lng};r={radius}&q={search_query}&apiKey={here_api_key}'
        results = requests.get(url).json()
        venues = json_normalize(results['items'])
        ResList.append(venues['title'].count())

    df_final['Cafes'] = CafeList
    df_final['Restaurants'] = ResList
    df_final['Gyms'] = GymList

    kclusters = 3
    kmeans = KMeans(n_clusters=kclusters, random_state=0).fit(df_final[['Cafes', 'Restaurants', 'Gyms']])
    df_final['Cluster'] = kmeans.labels_
    df_final['Cluster'] = df_final['Cluster'].apply(str)

    map_user_location = folium.Map(location=[latitude, longitude], zoom_start=12)

    def color_producer(cluster):
        if cluster == '0':
            return 'green'
        elif cluster == '1':
            return 'orange'
        else:
            return 'red'

    latitudes = list(df_final['position.lat'])
    longitudes = list(df_final['position.lng'])
    labels = list(df_final['Cluster'])
    names = list(d2['title'])
    for lat, lng, label, name in zip(latitudes, longitudes, labels, names):
        folium.CircleMarker(
                [lat, lng],
                fill=True,
                fill_opacity=1,
                popup=folium.Popup(name, max_width=300),
                radius=5,
                color=color_producer(label)
            ).add_to(map_user_location)

    folium.Marker([latitude, longitude], popup=location).add_to(map_user_location)
    map_user_location.save("UserLocationMap.html")

def on_search():
    location = location_entry.get()
    fetch_and_process_data(location)
    
    if 'title' in d2.columns:
        listbox.delete(0, tk.END)  # Clear previous results
        # Add all titles except the last one
        titles_to_add = d2['title'][:-1]  # Exclude the last item
        for title in titles_to_add:
            listbox.insert(tk.END, title)
    else:
        messagebox.showerror("Error", "Data not available or 'title' column missing")

def on_show_map():
    webbrowser.open("UserLocationMap.html")

# Function to toggle full screen
def toggle_fullscreen(event=None):
    global fullscreen
    fullscreen = not fullscreen
    root.attributes("-fullscreen", fullscreen)

def end_fullscreen(event=None):
    global fullscreen
    fullscreen = False
    root.attributes("-fullscreen", False)

# Create main window
root = tk.Tk()
root.title("PG Accommodation")

# Set background color
root.configure(bg='#FFA500')  # Orange background

# Create and place widgets
title_label = tk.Label(root, text="PG Accommodation", font=("Helvetica", 24, "bold"), bg='#FFA500', fg='black')
title_label.grid(row=0, column=0, columnspan=3, pady=20)

tk.Label(root, text="Enter Location:", font=("Helvetica", 14), bg='#FFA500', fg='black').grid(row=1, column=0, padx=10, pady=10, sticky='e')
location_entry = tk.Entry(root, width=50, font=("Helvetica", 14))
location_entry.grid(row=1, column=1, padx=10, pady=10, sticky='w')

search_button = tk.Button(root, text="Search", font=("Helvetica", 14), command=on_search, bg='black', fg='#FFA500', width=15)
search_button.grid(row=2, column=0, columnspan=2, pady=10)

show_map_button = tk.Button(root, text="Show Map", font=("Helvetica", 14), command=on_show_map, bg='black', fg='#FFA500', width=15)
show_map_button.grid(row=3, column=0, columnspan=2, pady=10)

listbox = tk.Listbox(root, width=80, height=20, font=("Helvetica", 12), bg='white', fg='black')
listbox.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

# Load and display the image
img = Image.open("pg_accommodation1.jpg")  # Replace with the path to your image
img = img.resize((460, 460), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS
img = ImageTk.PhotoImage(img)
image_label = tk.Label(root, image=img, bg='#FFA500')
image_label.grid(row=1, column=2, rowspan=4, padx=(50, 20), pady=10, sticky='n')

# Bind F11 to toggle full screen and Escape to end full screen
root.bind("<F11>", toggle_fullscreen)
root.bind("<Escape>", end_fullscreen)

# Set the window to full screen initially
fullscreen = True
root.attributes("-fullscreen", True)

# Run the Tkinter event loop
root.mainloop()
