import pandas as pd
from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse # Added for potential redirects
from pyecharts.charts import Page, Map3D, Pie, Line, Timeline, Radar
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ChartType
from django.contrib import auth, messages
from django.contrib.auth.models import User
import os # For joining paths for CSV
from django.conf import settings # To get BASE_DIR
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout # Added for logout_view

# Construct the path to the CSV file
# Assuming the CSV is in 'static/data/更新后的水质.csv' relative to BASE_DIR
# If dashboard_app/static/data, then it would be:
# csv_path = os.path.join(settings.BASE_DIR, 'dashboard_app', 'static', 'data', '更新后的水质.csv')
# For now, let's assume it's in project's static folder as per original settings.
csv_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'water_quality_data.csv')

# Placeholder for data loading. Actual data file will be added later.
# This will likely cause an error if the file doesn't exist yet,
# but we'll create the file in a subsequent step.
# For robust loading, check if file exists or handle FileNotFoundError.
try:
    data = pd.read_csv(csv_path)
    data = pd.DataFrame(data)
except FileNotFoundError:
    # Create an empty DataFrame with expected columns if file not found
    # This allows views to be defined without immediate error,
    # but charts will be empty or error out until data is present.
    print(f"Info: {csv_path} not found. Using empty DataFrame.")
    data = pd.DataFrame(columns=['省份', '水质类别', '实测经度', '实测纬度', '监测时间', 'pH', '海区']) # Added '海区'

def login_view(request): # Renamed to avoid conflict with django.contrib.auth.login
    if request.method == "GET":
        return render(request, "login.html")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = auth.authenticate(request, username=username, password=password) # Added request for Django > 4.0
        if user:
            auth.login(request, user)
            # Assuming 'pic_all' is the name of the url pattern for the dashboard
            return redirect(reverse('dashboard_app:pic_all'))
        else:
            messages.add_message(request, messages.WARNING, "用户名或密码错误")
            return render(request, "login.html", locals())
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect(reverse('dashboard_app:login')) # Redirect to login page after logout

fn = """
    function(params) {
        if(params.name == '其他')
            return '\n\n\n' + params.name + ' : ' + params.value + '%';
        return params.name + ' : ' + params.value + '%';
    }
"""

def new_label_opts():
    return opts.LabelOpts(formatter=JsCode(fn), position="center")

def map_pro(request):
    if data.empty or not all(col in data.columns for col in ['省份', '水质类别', '实测经度', '实测纬度']):
        return HttpResponse("Data is not available or malformed for map_pro.")
    province_counts = data.groupby('省份')['水质类别'].count().reset_index()
    province_counts['水质类别'] = province_counts['水质类别'].astype(int)
    province_coords = data.groupby('省份').first()[['实测经度', '实测纬度']].reset_index()
    merged_data = pd.merge(province_counts, province_coords, on='省份')
    converted_data = merged_data.apply(lambda row: (row['省份'], [row['实测经度'], row['实测纬度'], row['水质类别']]), axis=1).tolist()

    c = (
        Map3D(init_opts=opts.InitOpts(width="100%"))
            .add_schema(
            itemstyle_opts=opts.ItemStyleOpts(
                color="rgb(5,101,123)",
                opacity=1,
                border_width=0.8,
                border_color="rgb(62,215,213)",
            ),
            map3d_label=opts.Map3DLabelOpts(
                is_show=False,
                formatter=JsCode("function(data){return data.name + ' ' + data.value[2];}"),
            ),
            emphasis_label_opts=opts.LabelOpts(
                is_show=False,
                color="#fff",
                font_size=10,
                background_color="rgba(0,23,11,0)",
            ),
            light_opts=opts.Map3DLightOpts(
                main_color="#fff",
                main_intensity=1.2,
                main_shadow_quality="high",
                is_main_shadow=False,
                main_beta=10,
                ambient_intensity=0.3,
            ),
        )
            .add(
            series_name="质量分布情况",
            data_pair=converted_data,
            type_=ChartType.SCATTER3D, # Ensure this is a valid ChartType or string
            # bar_size=1, # bar_size might not be applicable for SCATTER3D, check pyecharts docs. Removed.
            shading="lambert",
            label_opts=opts.LabelOpts(
                is_show=False,
                formatter=JsCode("function(data){return data.name + ' ' + data.value[2];}"),
            ),
        )
            .set_global_opts(visualmap_opts=opts.VisualMapOpts(is_show=False, max_=700), #max_ should be dynamic or reviewed
                             legend_opts=opts.LegendOpts(textstyle_opts=opts.TextStyleOpts(color='#ededed')))
    )
    return HttpResponse(c.render_embed())

def pie_pro(request):
    if data.empty or '水质类别' not in data.columns:
        return HttpResponse("Data is not available or malformed for pie_pro.")
    water_type_counts = data.groupby('水质类别').size().reset_index(name='数量')

    categories = water_type_counts['水质类别'].tolist()
    counts = water_type_counts['数量'].tolist()

    pie_data1 = []
    pie_data2 = []
    pie_data3 = []

    if len(categories) > 0: pie_data1.append([categories[0], counts[0]])
    if len(categories) > 1: pie_data1.append([categories[1], counts[1]])
    if len(categories) > 2: pie_data1.append([categories[2], counts[2]])

    water_sum = sum(counts)

    category_for_pie2 = categories[4] if len(categories) > 4 else "N/A"
    count_for_pie2 = int(counts[4]) if len(counts) > 4 else 0
    pie_data2 = [[category_for_pie2, count_for_pie2], ["其他", water_sum - count_for_pie2 if water_sum > count_for_pie2 else 0 ]]

    category_for_pie3 = categories[3] if len(categories) > 3 else "N/A"
    count_for_pie3 = int(counts[3]) if len(counts) > 3 else 0
    pie_data3 = [[category_for_pie3, count_for_pie3], ["其他", water_sum - count_for_pie3 if water_sum > count_for_pie3 else 0]]

    p = (
        Pie(init_opts=opts.InitOpts(width="100%"))
            .add("", pie_data1, center=["20%", "30%"], radius=[28, 40])
            .add("", pie_data2, center=["38%", "30%"], radius=[28, 40], label_opts=new_label_opts())
            .add("", pie_data3, center=["56%", "30%"], radius=[28, 40], label_opts=new_label_opts())
            .set_global_opts(
            title_opts=opts.TitleOpts(title="水质类别占比", pos_top='20px', pos_left='20px',
                                      title_textstyle_opts=opts.TextStyleOpts(color='#FFF', font_size=16)),
            legend_opts=opts.LegendOpts(
                type_="scroll", pos_top="20%", pos_left="80%", orient="vertical", is_show=False,
                textstyle_opts=opts.TextStyleOpts(color='#FFF')
            ),
        )
            .set_series_opts(label_opts=opts.LabelOpts(color='#FFF'))
    )
    return HttpResponse(p.render_embed())

def line_pro(request):
    if data.empty or not all(col in data.columns for col in ['省份', '监测时间', '水质类别']):
        return HttpResponse("Data is not available or malformed for line_pro.")

    # Ensure '监测时间' can be converted to datetime
    data_copy = data.copy() # Work on a copy to avoid modifying the global DataFrame
    try:
        data_copy['监测时间'] = pd.to_datetime(data_copy['监测时间'])
    except Exception as e:
        print(f"Could not convert '监测时间' to datetime: {e}. Using original data for grouping.")
        # If conversion fails, group by original '监测时间' string representation or handle as error
        # For this example, we'll proceed, but this might lead to incorrect time-based grouping
        pass # Allow execution to continue, grouping will be based on string dates if conversion failed

    # Check if '监测时间' is datetime type after attempting conversion
    if pd.api.types.is_datetime64_any_dtype(data_copy['监测时间']):
        grouped_data = data_copy.groupby(['省份', data_copy['监测时间'].dt.to_period("M"), '水质类别']).size().reset_index(name='数量')
        grouped_data['年月'] = grouped_data['监测时间'].astype(str) # Convert Period to string for unique checks
    else: # Fallback if '监测时间' is not datetime (e.g. original string dates)
        grouped_data = data_copy.groupby(['省份', '监测时间', '水质类别']).size().reset_index(name='数量')
        grouped_data['年月'] = grouped_data['监测时间'] # Use original string date as '年月'

    dates = sorted(grouped_data['年月'].unique())
    timeline = Timeline(init_opts=opts.InitOpts(width='auto', height='300px'))

    for date_val in dates:
        data_by_date = grouped_data[grouped_data['年月'] == date_val]
        line_chart = Line(init_opts=opts.InitOpts(width='auto', height='250px'))

        if '省份' not in data_by_date.columns:
            continue

        water_types_to_plot = ['一类', '二类', '三类', '四类']

        # X-axis should be consistent for all series in a line chart for a given timeline step
        # Using all unique provinces for the current date_val as x-axis categories
        provinces_on_date = sorted(data_by_date['省份'].unique())
        if not provinces_on_date: # Skip if no provinces for this date
            continue
        line_chart.add_xaxis(provinces_on_date)

        for water_type_val in water_types_to_plot:
            series_data = []
            # For each province in provinces_on_date, find the count for water_type_val
            for prov in provinces_on_date:
                val = data_by_date[(data_by_date['省份'] == prov) & (data_by_date['水质类别'] == water_type_val)]['数量'].sum() # sum() to handle potential duplicates, though size() should prevent
                series_data.append(val if val else 0) # Add 0 if no data for this water_type in this prov

            if any(series_data): # Only add series if there's data
                line_chart.add_yaxis(
                    water_type_val,
                    series_data,
                    is_smooth=True,
                    linestyle_opts=opts.LineStyleOpts(width=3)
                )

        line_chart.set_global_opts(
            title_opts=opts.TitleOpts(title=f'水质类别数量 ({date_val})',
                                      title_textstyle_opts=opts.TextStyleOpts(color='#000', font_size=14),
                                      pos_left='center'),
            xaxis_opts=opts.AxisOpts(type_="category", axislabel_opts=opts.LabelOpts(is_show=True, color="black")),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                axislabel_opts=opts.LabelOpts(color='black', is_show=True),
                splitline_opts=opts.SplitLineOpts(is_show=True, linestyle_opts=opts.LineStyleOpts(type_='dashed', color='#ccc')),
                axisline_opts=opts.AxisLineOpts(linestyle_opts=opts.LineStyleOpts(color='black'))
            ),
            tooltip_opts=opts.TooltipOpts(trigger='axis', axis_pointer_type='shadow'),
            legend_opts=opts.LegendOpts(pos_top='30px', textstyle_opts=opts.TextStyleOpts(color='black'))
        )
        timeline.add(line_chart, date_val)

    timeline.add_schema(
        play_interval=1000,
        is_auto_play=True,
        is_timeline_show=True,
        pos_left='10px',
        pos_right='10px',
        is_loop_play=True
    )
    return HttpResponse(timeline.render_embed())

def table_pro(request):
    if data.empty or not all(col in data.columns for col in ['省份', '水质类别', 'pH']): # Removed '海区' for now, will add back if present
        return HttpResponse("Data is not available or malformed for table_pro (missing required columns).")

    # Check if '海区' column exists, if not, create a dummy one or handle error
    # This makes '海区' optional for the table view.
    data_copy = data.copy()
    if '海区' not in data_copy.columns:
        print("Info: '海区' column not found in data for table_pro. Proceeding without it.")
        # Option 1: Add a dummy column if '海区' is essential for grouping logic later
        # data_copy['海区'] = '未知海区'
        # Option 2: Adjust grouping if '海区' is not essential
        grouping_cols = ['省份']
    else:
        grouping_cols = ['省份', '海区']


    low_four = data_copy[data_copy['水质类别'] == '劣四类']
    if low_four.empty:
        return HttpResponse("No '劣四类' water quality data found.")

    agg_dict = {'水质类别': 'count'}
    if 'pH' in low_four.columns:
        agg_dict['pH'] = 'sum'

    # Adjust grouping based on whether '海区' is present
    low_four_sum = low_four.groupby(grouping_cols).agg(agg_dict).reset_index()
    low_four_sum = low_four_sum.sort_values(by='水质类别', ascending=False)
    low_four_sum = low_four_sum.rename(columns={'水质类别': '水质-劣四类'})

    rows = low_four_sum.values.tolist()
    headers = low_four_sum.columns.tolist()

    table = Table()
    table.add(headers=headers, rows=rows,
              attributes={
                  'align': 'left',
                  "style": "color:#3CA6DE;width:auto;height:auto;font-size:14px;padding:8px;text-align:center;border-collapse:collapse;border:1px solid #ddd;"
              })
    table.set_global_opts(
        title_opts=opts.TitleOpts(
            title='重点关注劣四类水资源',
            title_textstyle_opts=opts.TextStyleOpts(color="#000", font_size='18px')
        )
    )
    return HttpResponse(table.render_embed())

def radar_pro(request):
    if data.empty or not all(col in data.columns for col in ['省份', '监测时间']):
        return HttpResponse("Data is not available or malformed for radar_pro.")

    # Work on a copy of the data
    data_copy = data.copy()

    # Ensure '监测时间' is treated consistently (e.g. as string for grouping if not date)
    # If '监测时间' is datetime, convert to string to ensure distinct values for legend/series
    if pd.api.types.is_datetime64_any_dtype(data_copy['监测时间']):
        data_copy['监测时间'] = data_copy['监测时间'].dt.strftime('%Y-%m-%d %H:%M:%S')


    sum_time = data_copy.groupby(['省份', '监测时间']).size().reset_index(name='总数')
    if sum_time.empty:
        return HttpResponse("No data available for radar chart after grouping.")

    provinces_for_schema = sorted(sum_time['省份'].unique())
    times_for_series = sorted(sum_time['监测时间'].unique())

    schema = []
    for prov_name in provinces_for_schema:
        max_val = sum_time[sum_time['省份'] == prov_name]['总数'].max()
        if pd.isna(max_val): max_val = 0
        schema.append(opts.RadarIndicatorItem(name=prov_name, max_=int(max_val)))

    if not schema:
        return HttpResponse("Cannot generate radar chart schema (no provinces found).")

    radar = Radar(init_opts=opts.InitOpts(width='auto', height='400px'))
    radar.add_schema(schema=schema, splitarea_opt=opts.SplitAreaOpts(is_show=False))

    color_list = ['#FF4500', '#4169E1', '#32CD32', '#FFD700', '#BA55D3', '#4682B4', '#FFA07A', '#87CEEB', '#20B2AA', '#FF69B4']

    for i, time_val in enumerate(times_for_series):
        current_data_for_time = sum_time[sum_time['监测时间'] == time_val]
        province_data_values = []
        for prov_name in provinces_for_schema:
            val_series = current_data_for_time[current_data_for_time['省份'] == prov_name]['总数']
            val = val_series.sum() if not val_series.empty else 0 # Sum if multiple entries (should not happen with .size()), else 0
            province_data_values.append(val)

        if not any(province_data_values):
            continue

        radar.add(
            series_name=str(time_val),
            data=[province_data_values],
            linestyle_opts=opts.LineStyleOpts(width=2),
            areastyle_opts=opts.AreaStyleOpts(opacity=0.2),
            color=color_list[i % len(color_list)],
        )

    radar.set_global_opts(
        title_opts=opts.TitleOpts(title="水质量分布情况", title_textstyle_opts=opts.TextStyleOpts(color='#000', font_size=16)),
        legend_opts=opts.LegendOpts(pos_top='35px', textstyle_opts=opts.TextStyleOpts(color="#000"))
    )
    return HttpResponse(radar.render_embed())

@login_required
def pic_all(request):
    return render(request, 'index.html')
