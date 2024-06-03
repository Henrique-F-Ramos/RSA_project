import pandas as pd
import matplotlib.pyplot as plt


try:
    data = pd.read_csv('station_data.csv', on_bad_lines='skip')
except pd.errors.ParserError as e:
    print(f"ParserError: {e}")
    exit(1)

data['timestamp'] = pd.to_datetime(data['timestamp'])

data = data.groupby(['timestamp', 'stationID']).agg({'speed': 'mean'}).reset_index()

pivot_df = data.pivot(index='timestamp', columns='stationID', values='speed')

plt.figure(figsize=(12, 6))

for station_id in pivot_df.columns:
    plt.plot(pivot_df.index, pivot_df[station_id], label=f'Station ID {station_id}')

plt.xlabel('Timestamp')
plt.ylabel('Speed')
plt.title('Speed Change Over Time for Each Station ID')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()
