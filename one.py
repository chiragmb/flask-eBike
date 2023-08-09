#!/usr/bin/env python
# coding: utf-8

# In[18]:


import folium
import pandas as pd
import requests
from geopy.geocoders import Nominatim


def get_lat_long_from_address(address):
    locator = Nominatim(user_agent='myGeocoder')
    location = locator.geocode(address)
    return location.latitude, location.longitude


# # example
# address = '400 East Ave, Kitchener, ON N2H 1Z6'
# get_lat_long_from_address(address)


# In[19]:


# In[20]:


def get_directions_response(lat1, long1, lat2, long2, mode='bicycle'):
    url = "https://route-and-directions.p.rapidapi.com/v1/routing"
    key = "dea5a77bd2msh6c14e5c2257eed9p19b6b0jsneb1ceff345f2"
    host = "route-and-directions.p.rapidapi.com"
    headers = {
        "X-RapidAPI-Key": key,
        "X-RapidAPI-Host": host
    }
    querystring = {
        "waypoints": f"{lat1},{long1}|{lat2},{long2}",
        "mode": mode
    }
    response = requests.get(url, headers=headers, params=querystring)
    return response


response = get_directions_response(48.34364, 10.87474, 48.37073, 10.90925)
print(response.text)


# In[21]:


#
address1 = '49 Frederick St, Kitchener, ON N2H 6M7'
address2 = '589 Fairway Rd S, Kitchener, ON N2C 1X4, canada'
addresses = [address1, address2]


# In[22]:


lat_lons = [get_lat_long_from_address(addr) for addr in addresses]


# In[23]:


responses = []
for n in range(len(lat_lons)-1):
    lat1, lon1, lat2, lon2 = lat_lons[n][0], lat_lons[n][1], lat_lons[n +
                                                                      1][0], lat_lons[n+1][1]
    response = get_directions_response(lat1, lon1, lat2, lon2, mode='bicycle')
    responses.append(response)


# In[24]:


def create_map(response):
    # use the response
    mls = response.json()['features'][0]['geometry']['coordinates']
    points = [(i[1], i[0]) for i in mls[0]]
    m = folium.Map()
    # add marker for the start and ending points
    for point in [points[0], points[-1]]:
        folium.Marker(point).add_to(m)
    # add the lines
    folium.PolyLine(points, weight=5, opacity=1).add_to(m)
    # create optimal zoom
    df = pd.DataFrame(mls[0]).rename(
        columns={0: 'Lon', 1: 'Lat'})[['Lat', 'Lon']]
    sw = df[['Lat', 'Lon']].min().values.tolist()
    ne = df[['Lat', 'Lon']].max().values.tolist()
    m.fit_bounds([sw, ne])
    return m


m = create_map(response)


# In[25]:


def create_map(responses, lat_lons):
    m = folium.Map()
    df = pd.DataFrame()
    # add markers for the places we visit
    for point in lat_lons:
        folium.Marker(point).add_to(m)
    # loop over the responses and plot the lines of the route
    for response in responses:
        mls = response.json()['features'][0]['geometry']['coordinates']
        points = [(i[1], i[0]) for i in mls[0]]

        # add the lines
        folium.PolyLine(points, weight=5, opacity=1).add_to(m)
        temp = pd.DataFrame(mls[0]).rename(
            columns={0: 'Lon', 1: 'Lat'})[['Lat', 'Lon']]
        df = pd.concat([df, temp])
    # create optimal zoom
    sw = df[['Lat', 'Lon']].min().values.tolist()
    sw = [sw[0]-0.0005, sw[1]-0.0005]
    ne = df[['Lat', 'Lon']].max().values.tolist()
    ne = [ne[0]+0.0005, ne[1]+0.0005]
    m.fit_bounds([sw, ne])
    return m


m = create_map(responses, lat_lons)
m.save('./route_map.html')


# In[ ]:
