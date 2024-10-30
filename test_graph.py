import pandas as pd
import os
import sys
import plotly.graph_objects as go

fileToCheck = {}
logs = []
# Загрузка данных из файлов

nameFile = sys.argv[1]  # for example 'test.ubx'
nameFile_int, nameFile_ext = os.path.splitext(nameFile)
file_path = 'Result_CSV'

files = {
    "BeiDou_L1": os.path.join(file_path, f'{nameFile_int}_BeiDou_B1I_L1_SNR.csv'),
    "BeiDou_L2": os.path.join(file_path, f'{nameFile_int}_BeiDou_L2_SNR.csv'),
    "GPS_L1": os.path.join(file_path, f'{nameFile_int}_GPS_L1CA_L1_SNR.csv'),
    "GPS_L2": os.path.join(file_path, f'{nameFile_int}_GPS_L2CM_L2_SNR.csv'),
}

data = {}
for system_band, file in files.items():
    if os.path.exists(file):
        df = pd.read_csv(file)
        df.set_index(df.columns[0], inplace=True)
        #df.index = pd.to_datetime(df.index, format='%H:%M:%S.%f')
        df.index = pd.to_datetime(df.index, format='%H:%M:%S')
        data[system_band] = df

# Создание интерактивного графика
fig = go.Figure()

for system_band, df in data.items():
    for col_name in df.columns:
        if col_name == 'Unnamed: 0':
            continue
        fig.add_trace(go.Scatter(x=df.index, y=df[col_name], mode='lines+markers', line=dict(width=1),marker=dict(size=4),name=f"{system_band} - Satellite {col_name}"))

# Настройка размеров и заголовков графика
fig.update_layout(
    height=800,
    width=1200,
    title="5, BeiDou and GPS Systems",
    plot_bgcolor='white',
    xaxis=dict(
        title='Time',
        tickformat='%H:%M:%S',
        tickmode='auto',
        nticks=10,
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=0.5,
        tickangle=0
    ),
    yaxis=dict(
        title='SNR, dBHz',
        range=[10, 60],
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=0.5
    ),
    legend=dict(
        x=1.02,
        y=1,
        traceorder='normal',
        bgcolor='rgba(255, 255, 255, 0)',
        bordercolor='black',
        borderwidth=1
    )
)

# Добавление кнопок для выбора всех спутников, ни одного спутника и для выбора спутников для каждой системы
fig.update_layout(
    updatemenus=[
        dict(
            buttons=list([
                dict(label='All',
                     method='update',
                     args=[{'visible': [True]*len(fig.data)},
                           {'title': 'All Satellites'}]),
                dict(label='None',
                     method='update',
                     args=[{'visible': [False]*len(fig.data)},
                           {'title': 'No Satellites'}]),
            ]),
            direction="left",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.1,
            xanchor="left",
            y=1.15,
            yanchor="top"
        ),
        dict(
            buttons=[
                dict(label='BeiDou L1',
                     method='update',
                     args=[{'visible': [trace.name.startswith("BeiDou_L1") for trace in fig.data]},
                           {'title': 'BeiDou L1'}]),
                dict(label='BeiDou L2',
                     method='update',
                     args=[{'visible': [trace.name.startswith("BeiDou_L2") for trace in fig.data]},
                           {'title': 'BeiDou L2'}]),
                dict(label='GPS L1',
                     method='update',
                     args=[{'visible': [trace.name.startswith("GPS_L1") for trace in fig.data]},
                           {'title': 'GPS L1'}]),
                dict(label='GPS L2',
                     method='update',
                     args=[{'visible': [trace.name.startswith("GPS_L2") for trace in fig.data]},
                           {'title': 'GPS L2'}]),
            ],
            direction="left",
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.3,
            xanchor="left",
            y=1.15,
            yanchor="top"
        ),
    ]
)

# Добавление кнопок для выбора каждого спутника отдельно
button_list = []
for idx, trace in enumerate(fig.data):
    button = dict(method='update',
                  label=trace.name,
                  args=[{'visible': [False]*len(fig.data)},
                        {'title': trace.name}])
    button['args'][0]['visible'][idx] = True
    
    button_list.append(button)

fig.update_layout(
    updatemenus=[dict(type="dropdown",
                      buttons=button_list,
                      direction="down",
                      x=1.3,
                      xanchor="left",
                      y=1,
                      yanchor="top")]
)

# Показ графика
fig.show()
