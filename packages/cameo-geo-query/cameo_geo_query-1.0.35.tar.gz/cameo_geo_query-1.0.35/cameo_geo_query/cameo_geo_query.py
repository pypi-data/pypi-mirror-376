import pandas as pd
from geopy.distance import geodesic
from datetime import datetime, timedelta
import plotly.express as px
from zoneinfo import ZoneInfo
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
import plotly.graph_objects as go
from dotenv import load_dotenv
from cameo_botrun_prompt_tools import print_button, print_link


load_dotenv()
AIOT_EPA_STATION_API = os.getenv("AIOT_EPA_STATION_API")


def calculate_distance(lat, lon, df_deviceid_file_path, distance, row_lat='lat', row_lon='lon', deviceid='device_id', type=None):
    # Read the device data from the CSV file
    df_deviceid = pd.read_csv(df_deviceid_file_path)
    
    # Drop rows with missing lat or lon values
    df_deviceid = df_deviceid.dropna(subset=[row_lat, row_lon], how='all')
    if type == 'air':
        df_deviceid = df_deviceid[df_deviceid['sensor'].str.contains('pm2_5', na=False)].reset_index(drop=True)
        
    # Ensure latitude and longitude values are within valid ranges
    min_lat = -90
    max_lat = 90
    min_lon = -180
    max_lon = 180
    df_deviceid[row_lat] = df_deviceid[row_lat].apply(lambda x: min(max(min_lat, x), max_lat))
    df_deviceid[row_lon] = df_deviceid[row_lon].apply(lambda x: min(max(min_lon, x), max_lon))

    # Create a function to calculate the distance
    def calculate_distance_row(row):
        device_location = (row[row_lat], row[row_lon])
        target_location = (lat, lon)
        distance = geodesic(device_location, target_location).kilometers
        return distance

    # Add a column to store the distances
    df_deviceid['distance_km'] = df_deviceid.apply(calculate_distance_row, axis=1)

    # Filter out data within one kilometer
    filtered_df = df_deviceid[df_deviceid['distance_km'] <= distance]

    # Get the list of device IDs
    lst_device_id = filtered_df[deviceid].to_list()

    return lst_device_id

def filter_data_for_device(result_lst_device_id, time, df_device_file_path, row_time='localTime', row_deviceid='deviceId', sensor='pm2_5', ten_minutes_before_after=4):
    def get_date_hour_min(time_diff, base_time):
        # 計算新時間
        new_time = base_time + timedelta(minutes=time_diff)

        # 格式化日期和時間
        str_date = new_time.strftime("%Y-%m-%d")
        str_hour = new_time.strftime("%H")
        str_minute = new_time.strftime("%M")[0]

        return str_date, str_hour, str_minute

    def filter_time(df, time, ten_minutes_before_after):
        user_input_time = pd.to_datetime(time)
        offset_minutes = ten_minutes_before_after * 10
        start_time = user_input_time - pd.DateOffset(minutes=offset_minutes)
        end_time = user_input_time + pd.DateOffset(minutes=offset_minutes)
        df[row_time] = pd.to_datetime(df[row_time])
        filtered_data = df[(df[row_time] >= start_time) & (df[row_time] <= end_time)].reset_index(drop=True)
        return filtered_data

    def filter_deviceid(df, result_lst_device_id):
        df = df[df[row_deviceid].isin(result_lst_device_id)].reset_index(drop=True)
        return df

    df_all = pd.DataFrame()
    base_time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

    for i in range(-10 * ten_minutes_before_after, 10 * ten_minutes_before_after, 10):
        str_date, str_hour, str_minute = get_date_hour_min(i, base_time)
        str_url = f'{df_device_file_path}/{str_date}/10mins_{str_date}_{str_hour}_{str_minute}.csv.gz'
        try:
            df = pd.read_csv(str_url, compression='gzip')
            df_all = pd.concat([df_all, df], ignore_index=True)
        except:
            pass
    df_all = filter_time(df_all, time, ten_minutes_before_after)
    df_all = filter_deviceid(df_all, result_lst_device_id)
    df_all = df_all[df_all['sensorId'] == sensor].reset_index(drop=True)
    return df_all
    

def create_custom_color_scale(color_dict):
    scale = []
    max_value = max(item['v'] for item in color_dict)  # 獲取最大數值
    for item in color_dict:
        # 將每個色彩值對應到其數值範圍（從0到1之間），並反轉色彩順序
        scale.append([item['v'] / max_value, item['color']])
    return scale[::-1]  # 反轉色彩尺度列表


def find_color_for_value(value, color_dict):
    for color_info in sorted(color_dict, key=lambda x: x['v']):
        if value <= color_info['v']:
            return color_info['color']
    return '#FFFFFF'  # 如果沒有合適的顏色，使用白色作為預設值


def create_pm25_map(df, lat, lon, file_path, row_value='value', row_deviceId='deviceId', row_lat='lat', row_lon='lon',
                    row_time='localTime', labeled_center_lat_lon=True, plot_animation=False):
    df[row_value] = df[row_value].astype(float)
    # Filter data
    if not plot_animation:
        df = df.loc[df.groupby(row_deviceId)[row_value].idxmax()]

    pm2_5_color_dict = [
        {"v": 500.4, "color": "#000000"},
        {"v": 450.5, "color": "#301E12"},
        {"v": 400.5, "color": "#3C230F"},
        {"v": 350.5, "color": "#49280D"},
        {"v": 300.5, "color": "#552E0A"},
        {"v": 250.5, "color": "#623307"},
        {"v": 230.5, "color": "#682c1f"},
        {"v": 210.5, "color": "#6d2537"},
        {"v": 190.5, "color": "#731d4e"},
        {"v": 170.5, "color": "#781666"},
        {"v": 150.5, "color": "#7e0f7e"},
        {"v": 131.3, "color": "#970f6a"},
        {"v": 112.1, "color": "#b10f56"},
        {"v": 92.9, "color": "#ca0e43"},
        {"v": 73.7, "color": "#e30e30"},
        {"v": 54.5, "color": "#fc0e1c"},
        {"v": 50.7, "color": "#fc241d"},
        {"v": 46.9, "color": "#fc3b1f"},
        {"v": 43.1, "color": "#fd5220"},
        {"v": 39.3, "color": "#fd6822"},
        {"v": 35.5, "color": "#fd7e23"},
        {"v": 31.5, "color": "#fd9827"},
        {"v": 27.5, "color": "#feb12b"},
        {"v": 23.5, "color": "#fecb30"},
        {"v": 19.5, "color": "#ffe534"},
        {"v": 15.5, "color": "#fffd38"},
        {"v": 12.4, "color": "#d4fd36"},
        {"v": 9.3, "color": "#a9fd34"},
        {"v": 6.2, "color": "#7EFD32"},
        {"v": 3.1, "color": "#53FD30"},
        {"v": 0, "color": "#29fd2e"}
    ]
    custom_color_scale = create_custom_color_scale(pm2_5_color_dict)

    df = df.sort_values(by=['localTime']).reset_index(drop=True)
    start_time = df['localTime'].min()
    end_time = df['localTime'].max()
    title_text = f"地圖展示自 {start_time} 到 {end_time} 間各監測站點PM2.5濃度的最高值及發生時間，中間以藍框標記的點位為你所關注的地點"

    # Create scatter mapbox
    if not plot_animation:
        fig = px.scatter_mapbox(df, lat=row_lat, lon=row_lon, color=row_value, range_color=(0, 500.4),
                                hover_data=[row_time, row_deviceId, row_value], zoom=7, size=[15] * len(df[row_lat]),
                                size_max=15, color_continuous_scale=custom_color_scale, title=f'此靜態{title_text}')
    else:
        fig = px.scatter_mapbox(df, lat=row_lat, lon=row_lon, color=row_value, range_color=(0, 500.4),
                                hover_data=[row_time, row_deviceId, row_value], zoom=7, size=[15] * len(df[row_lat]),
                                size_max=15, color_continuous_scale=custom_color_scale, title=f'此動態{title_text.replace("的最高","")}', animation_frame='localTime')

    fig.update_layout(mapbox_style='open-street-map')  # carto-positron

    if labeled_center_lat_lon:
        # Extract color for the specific point
        specific_point = df.query(f"{row_lat} == {lat} & {row_lon} == {lon}")
        if not specific_point.empty:
            specific_value = specific_point[row_value].iloc[0]
            specific_color = find_color_for_value(specific_value, pm2_5_color_dict)
        else:
            specific_color = '#FFFFFF'  # Default to white if no data

        # Add a blue border around the marker
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=24,  # Slightly larger to create a border effect
                color='blue'  # Blue border
            )
        ))

        # Add the original data point on top of the border
        fig.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=20,  # Original size
                color=specific_color  # Original or default color
            )
        ))

    initial_center = {"lat": lat, "lon": lon}  # Example coordinates
    initial_zoom = 14  # Example zoom level
    fig.update_layout(mapbox_center=initial_center, mapbox_zoom=initial_zoom)
    fig.update_layout(margin={'r': 0, 'l': 0, 'b': 0})
    # Save to html
    fig.write_html(file_path, include_plotlyjs=True)

    return file_path

def clean_data(data_dict, start_time, end_time):
    # 這裡確保傳入的是字典中的資料列表
    data_list = data_dict['data']

    # 過濾資料
    cleaned_data_list = [item for item in data_list if
                         start_time <= datetime.strptime(item['time'], "%Y-%m-%d %H:%M:%S") <= end_time]
    # 更新字典
    cleaned_data_dict = {
        'count': len(cleaned_data_list),
        'data': cleaned_data_list
    }

    return cleaned_data_dict

def get_cwb_wind_data(int_lat, int_lon, str_datetime):
    event_loc = (int_lat, int_lon)
    event_time = datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S")

    # 建立一個特定時間點用於判斷
    time_threshold = datetime.strptime("2023-11-15 13:00:00", "%Y-%m-%d %H:%M:%S")

    time_clean_start_threshold = datetime.strptime("2023-11-15 00:00:00", "%Y-%m-%d %H:%M:%S")
    time_clean_end_threshold = datetime.strptime("2023-11-16 00:00:00", "%Y-%m-%d %H:%M:%S")

    t = (event_time + timedelta(minutes=-event_time.minute, seconds=-event_time.second))
    str_result = "無氣象署測站資料"
    for _ in range(3):
        start_time, end_time = t, (t + timedelta(hours=1))
        print('start_time', start_time)

        # 如果 start_time 或 end_time 大於設定的時間點，則減少 8 小時
        if start_time > time_threshold and end_time > time_threshold:
            start_time -= timedelta(hours=8)
            end_time -= timedelta(hours=8)

        formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

        t = t - timedelta(hours=1)
        cwb_api = f'{AIOT_EPA_STATION_API}/wind?fields=wind_direct%2Cwind_speed&sources=中央氣象局&min_lat=-90&max_lat=90&min_lon=-180&max_lon=180&start_time={formatted_start_time}&end_time={formatted_end_time}'
        response = requests.get(cwb_api, verify=False, timeout=10)
        j = response.json()

        try:
            if event_time > time_clean_start_threshold and event_time < time_clean_end_threshold:
                j = clean_data(j, t, (t + timedelta(hours=2)))
        except:
            pass

        if len(j['data']) != 0:
            nearest_site, nearest_dist = None, None
            for i in range(len(j['data'])):
                site_loc = (j['data'][i]['lat'], j['data'][i]['lon'])
                dist = geodesic(event_loc, site_loc).km
                if nearest_dist is None or dist < nearest_dist:
                    nearest_site, nearest_dist = j['data'][i], dist
            str_result = f"以下為距離最近的氣象署測站資料:\n測站: {nearest_site['name']}(距離{nearest_dist:.2f}公里)\n資料時間: {nearest_site['time']}\n風向: {nearest_site['wind_direct']}\n風速: {nearest_site['wind_speed']}"
            break
        else:
            continue
    return str_result


def get_national_station_air_quality_data(start_time, end_time, area, fields='aqi,pm2_5,pm10,so2,co,no2,o3'):
	start_time = start_time.replace(" ", "%20")
	end_time = end_time.replace(" ", "%20")
	area = area.replace("縣", "").replace("市", "").replace("臺", "台")
	api_url = f"{AIOT_EPA_STATION_API}/rawdata?fields={fields}&start_time={start_time}&end_time={end_time}&area={area}"
	response = requests.get(api_url, verify=False, timeout=10)

	return response.json()


def get_iot_air_quality_info(
    location, lat, lon, time, distance, time_range_in_hour,
    df_deviceid_file_path, df_device_file_path, file_folder, file_url
):
    # 為檔名移除空格與冒號，避免網址無效
    safe_time = time.replace(" ", "_").replace(":", "-")
    file_path_map = f'{file_folder}/iot_peaks_map_{location}_{safe_time}.html'
    file_path_map_animation = f'{file_folder}/iot_peaks_map_animation_{location}_{safe_time}.html'
    file_path_ts = f'{file_folder}/iot_peaks_ts_{location}_{safe_time}.html'
    ten_minutes_before_after = int(time_range_in_hour * 60 / 10)

    result_lst_device_id = calculate_distance(lat, lon, df_deviceid_file_path, distance, type='air')
    if len(result_lst_device_id)>0:
        try:
            df_all = filter_data_for_device(
                result_lst_device_id, time, df_device_file_path,
                ten_minutes_before_after=ten_minutes_before_after
            )
            # 如果取得的資料為空，直接結束避免繪圖錯誤
            if df_all.empty:
                print(f"抱歉, {time} 前後{time_range_in_hour}小時內，鄰近{distance}公里感測器無資料")
                return
            df_all.to_csv(f'{file_folder}/exported_df_{location}_{safe_time}.csv', index=False)
            print_link(
                f"{file_url}/exported_df_{location}_{safe_time}.csv",
                f"點我下載{time}前後{time_range_in_hour}小時感測器資料csv"
            )
        except KeyError:
            print("取得感測器資料失敗, 近七天以外的時間點可能沒有資料")
            print("若確定時間為近七天, 或確定該日期有資料, 請聯繫開發人員")
            exit()

        # 對 df_all 的 'value' 欄位進行降序排序
        df_all['value'] = pd.to_numeric(df_all['value'])
        df_sorted = df_all.sort_values(by='value', ascending=False)

        # 取得排序後的前20筆資料
        df_top10 = df_sorted.head(20)

        # 如果您需要將這個 DataFrame 轉換成 string
        df_top10_str = df_top10.to_string()

        print(f"這段時間鄰近{distance}公里內的感測器空品數據如下：（依照監測值高到低顯示前20筆資料）")
        print('空品:'+df_top10_str)

        # 地圖
        map_url = create_pm25_map(
            df_all, lat, lon, file_path_map, row_value='value',
            row_deviceId='deviceId', row_lat='lat', row_lon='lon', row_time='localTime'
        )
        map_animation_url = create_pm25_map(
            df_all, lat, lon, file_path_map_animation, row_value='value',
            row_deviceId='deviceId', row_lat='lat', row_lon='lon', row_time='localTime', plot_animation=True
        )

        # 時序圖
        def generate_time_series_chart(df, file_path_ts):
            df = df.sort_values(by='localTime')
            fig = px.line(df, x='localTime', y='value', color='deviceId', title='各感測器的PM2.5時間序列圖')
            fig.update_xaxes(title_text='時間')
            fig.update_yaxes(title_text='PM2.5(μg/m³)')
            fig.write_html(file_path_ts, include_plotlyjs=True)
            return file_path_ts
        ts_url = generate_time_series_chart(df_all, file_path_ts)

        # 提供地圖及時序圖的連結
        print_link(
            f"{file_url}/iot_peaks_map_{location}_{safe_time}.html",
            f"該地點附近 {time} 前後{time_range_in_hour}小時感測器最大值靜態地圖"
        )
        print_link(
            f"{file_url}/iot_peaks_map_animation_{location}_{safe_time}.html",
            f"該地點附近 {time} 前後{time_range_in_hour}小時感測器最大值動態地圖"
        )
        print_link(
            f"{file_url}/iot_peaks_ts_{location}_{safe_time}.html",
            f"該地點附近 {time} 前後{time_range_in_hour}小時感測器最大值時序圖"
        )

        # 提示使用者想要進一步了解什麼資訊
        print_button("分析洞見", "請幫忙解讀IOT 空品數據洞見")
        print_button("草擬FB貼文", "草擬FB貼文")

    else:
        print(f"抱歉, {location} 鄰近{distance}公里區域內沒有感測器")


def deg_to_label(deg):
    """Convert wind direction in degrees to 16-point compass label."""
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ]
    try:
        index = int((float(deg) + 11.25) / 22.5) % 16
    except Exception:
        # Fallback for bad values; default to 'N'
        index = 0
    return directions[index]


def prepare_wind_data(df):
    """Return a processed copy of wind data with parsed time and wind_dir_label.

    - Parses 'time' to datetime (coerce errors) and drops invalid times
    - Adds 'wind_dir_label' from 'wind_direct' when available
    - Sorts by 'time' if present
    """
    if df is None:
        return pd.DataFrame()
    data = df.copy()
    if 'time' in data.columns:
        data['time'] = pd.to_datetime(data['time'], errors='coerce')
        data = data.dropna(subset=['time'])
        if not data.empty:
            data = data.sort_values(by=['time']).reset_index(drop=True)
    # Add wind_dir_label if wind_direct exists
    if 'wind_direct' in data.columns and 'wind_dir_label' not in data.columns:
        data['wind_dir_label'] = data['wind_direct'].apply(deg_to_label)
    return data


def plot_wind_rose(wind_data, filepath):
    # 資料前處理（不改動傳入物件）
    wind_data = prepare_wind_data(wind_data)

    # 若資料為空或缺少 time 欄位，直接略過
    if wind_data.empty or 'time' not in wind_data.columns:
        print("風場資料為空，無法產生風花圖")
        return
    # 若無有效時間戳
    if wind_data.empty:
        print("風場資料沒有有效時間戳，無法產生風花圖")
        return
    # 確保有風向標籤
    if 'wind_dir_label' not in wind_data.columns:
        print("風場資料缺少風向資訊，無法產生風花圖")
        return
    
    # 16 方位順序，供圖上顯示順序用
    categories = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    
    # 依 (方位, 風速) 計算出現次數
    agg = wind_data.groupby(["wind_dir_label", "wind_speed"]).size().reset_index(name="count")
    
    # 依據 time 欄位計算時間範圍，並取得測站名稱
    start_time = wind_data["time"].min().strftime("%Y-%m-%d %H:%M")
    end_time = wind_data["time"].max().strftime("%Y-%m-%d %H:%M")
    station_name = wind_data["name"].iloc[0]
    title_text = f"{start_time} ~ {end_time} {station_name} 風花圖"

    # 使用 bar_polar 時，改用類別欄位當作 theta（而不是手動轉成數字角度）
    # 並指定 category_orders 來保證顯示順序是 N -> NNE -> NE -> ... -> NNW
    fig = px.bar_polar(
        agg,
        r="count",                  # 徑向代表該 (風向, 風速) 的次數
        theta="wind_dir_label",     # 直接用離散的風向欄位
        color="wind_speed",         # 顏色對應原始風速數值
        template="plotly_white",
        color_continuous_scale=px.colors.sequential.Plasma,
        category_orders={"wind_dir_label": categories}, 
        hover_data={"count": True, "wind_speed": True},
        start_angle=90,            # 讓 N (index=0) 對準圖頂
        direction="clockwise",     # 風玫瑰常見順時鐘顯示
    )

    # 更新整體排版
    fig.update_layout(
        title=title_text,
        polar=dict(
            radialaxis=dict(showticklabels=True),  # 看需求是否顯示徑向刻度
            angularaxis=dict(showticklabels=True)  # 角度刻度預設就會顯示
        )
    )

    # 更新 color bar 的標題
    fig.update_coloraxes(colorbar_title="風速 (m/s)")

    fig.write_html(filepath)


def get_wind_data_by_national_station_name_list(start_time, end_time, station_name_list):
    cwb_api = f'{AIOT_EPA_STATION_API}/wind?fields=wind_direct%2Cwind_speed&sources=國家測站&min_lat=-90&max_lat=90&min_lon=-180&max_lon=180&start_time={start_time}&end_time={end_time}'
    response = requests.get(cwb_api, verify=False, timeout=10)
    j = response.json()
    df = pd.DataFrame(j['data'])
    wind_data = df[df['name'].isin(station_name_list)]

    return wind_data


def get_national_station_air_quality_report_around_event(start_time, end_time, area, file_folder, file_url):
    data_around_event = get_national_station_air_quality_data(start_time, end_time, area)
    now_start = (datetime.now(ZoneInfo("Asia/Taipei")) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    now_end = (datetime.now(ZoneInfo("Asia/Taipei")) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    data_now = get_national_station_air_quality_data(now_start, now_end, area)
    data_around_event = pd.DataFrame(data_around_event['data'])
    data_now = pd.DataFrame(data_now['data'])
    data_all = pd.concat([data_around_event, data_now], ignore_index=True)
    data_all = data_all[['name','time', 'pm2_5', 'pm10', 'aqi', 'so2', 'co', 'no2', 'o3']]
    data_all['time'] = pd.to_datetime(data_all['time']) + timedelta(hours=1)
    data_all = data_all.sort_values(by=['name', 'time']).reset_index(drop=True)
    grouped = data_all.groupby('name')
    station_name_list = list(data_all['name'].unique())
    wind_data_all_station = get_wind_data_by_national_station_name_list(start_time, end_time, station_name_list)

    def plot_station_sensor_ts(data, y_columns, title, filepath):
        if len(y_columns) == 1:
            y_column = y_columns[0]
            fig = px.line(data, x='time', y=y_column, color='name', markers=True, title=title, labels={'time': '時間', y_column: y_column})
        else:
            df_melt = data.melt(id_vars=['time'], value_vars=y_columns, var_name='測項', value_name='數值')
            fig = px.line(df_melt, x='time', y='數值', color='測項', markers=True, title=title, labels={'time': '時間', '數值': '數值'})
        fig.update_layout(xaxis_title="時間", yaxis_title="數值")
        fig.write_html(filepath)

    for station_name, df_station in grouped:
        print(f"======== 單一測站圖表：{station_name} ========")
        fig_title = f"{station_name}的多測項時序圖"
        fig_filename = f"{station_name}_sensor_ts.html"
        plot_station_sensor_ts(df_station, ["pm2_5", "pm10", "so2", "co", "no2", "o3"], fig_title, f"{file_folder}/{fig_filename}")
        print_link(f"{file_url}/{fig_filename}", fig_title)
        print(df_station)

        wind_data = wind_data_all_station[wind_data_all_station['name'] == station_name]
        # 原始資料時間 +1 小時，再進行整體前處理
        wind_data = wind_data.copy()
        if 'time' in wind_data.columns:
            wind_data.loc[:, "time"] = pd.to_datetime(wind_data["time"]) + pd.Timedelta(hours=1)
        wind_data_prepared = prepare_wind_data(wind_data)
        wind_rose_filename = f"{station_name}_wind_rose.html"
        plot_wind_rose(wind_data_prepared, f"{file_folder}/{wind_rose_filename}")
        print_link(f"{file_url}/{wind_rose_filename}", f"{station_name}的風花圖")
        # 安全列印欄位
        cols = [c for c in ['time', 'wind_direct', 'wind_speed', 'wind_dir_label'] if c in wind_data_prepared.columns]
        if cols:
            print(wind_data_prepared[cols])
        else:
            print("風場資料缺少可列印欄位")

    pm25_ts_filename = f'pm25_ts.html'
    co_ts_filename = f'co_ts.html'
    print(f"======== 所有測站圖表 ========")
    plot_station_sensor_ts(data_all, ['pm2_5'], "所有測站的 PM2.5 時序變化", f"{file_folder}/{pm25_ts_filename}")
    plot_station_sensor_ts(data_all, ['co'], "所有測站的 CO 時序變化", f"{file_folder}/{co_ts_filename}")
    print_link(f"{file_url}/{pm25_ts_filename}", f"所有測站的PM2.5時序圖")
    print_link(f"{file_url}/{co_ts_filename}", f"所有測站的CO時序圖")


if __name__ == '__main__':
    # Example of calculate_distance usage:
    lon = 121.3208
    lat = 25.046
    df_deviceid_file_path = '/Users/apple/Desktop/project_device_table_20231017.csv'
    result_lst_device_id = calculate_distance(lat, lon, df_deviceid_file_path, 1, type='air')
    print(result_lst_device_id)
    
    # Example of filter_data_for_device_time usage:
    df_device_file_path = '/Users/apple/Desktop/iot_data'
    time = '2023-11-15 08:35:00'
    df = filter_data_for_device(result_lst_device_id, time,df_device_file_path)
    print(df.localTime.min())
    print(df.localTime.max())
    print(df.columns)
    
    file_path = '/Users/apple/Desktop/test.html'
    url = create_pm25_map(df,lat, lon, file_path, row_value='value', row_deviceId='deviceId', row_lat='lat', row_lon='lon', row_time='localTime')
    print(url)
    
    str_wind_result = get_cwb_wind_data(lat, lon, time)
    print(str_wind_result)
