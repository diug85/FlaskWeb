import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.finance as fin
from indicators import *

start = datetime.datetime(2017,1,1)
end = datetime.datetime.now()

datos = gethistory('amx', start, end)
print('                                   ________________ =) _______________')
sar = PSAR(datos)
print(sar)

gs = gridspec.GridSpec(3,1, height_ratios=[1, 3, 1])
gs.update(wspace=0)
ax1 = plt.subplot(gs[0])
ax1.plot(np.arange(10))
ax2 = plt.subplot(gs[1])
ax2.plot(sar,'go')
fin.candlestick2_ohlc(ax2,datos['Open'],datos['High'],datos['Low'],datos['Close'])
ax3 = plt.subplot(gs[2])
ax3.plot(np.cos(np.arange(10)))