import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

def make_candlestick(df, pair, signal=None, entry=None, stop=None, tp=None):
    df_plot = df.copy()
    df_plot['time'] = df_plot['datetime']
    fig, ax = plt.subplots(figsize=(8,4))
    for idx, row in df_plot.iterrows():
        color = 'green' if row['close'] >= row['open'] else 'red'
        ax.plot([row['time'], row['time']], [row['low'], row['high']], color=color, linewidth=1)
        ax.plot([row['time'], row['time']], [row['open'], row['close']], color=color, linewidth=6)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_title(f"{pair} — Candlestick (1min)")
    if signal and entry:
        col = 'green' if signal == 'BUY' else 'red'
        ax.scatter(df_plot['time'].iloc[-1], entry, color=col, s=90, zorder=5)
        if stop:
            ax.axhline(stop, color='gray', linestyle='--')
        if tp:
            ax.axhline(tp, color='gold', linestyle='--')
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf