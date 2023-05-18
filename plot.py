from __future__ import division
from collections import defaultdict
from matplotlib import rcParams
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.use('Agg')

rcParams['font.serif'] = ['Times']
plt.style.use('grayscale')

mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42

new_params = {
    'axes.labelsize': 100,
    'xtick.labelsize': 100,
    'ytick.labelsize': 150,
    'legend.fontsize': 45,
    'lines.markersize': 45,
    'xtick.major.pad': 15,
    'ytick.major.pad': 10,
    'font.size': 85,
    'grid.linestyle': 'dashdot',
    'patch.edgecolor': 'black',
    'patch.force_edgecolor': True,
    'font.serif': 'Times',
    'grid.alpha': 0.4,
}
mpl.rcParams.update(new_params)

bench_names = []
bench_all = []

stats = defaultdict(list)


bench_names_final = ['LR-serv',	'CNN-serv',	'RNN-serv',	'ML-tr', 'VidConv', 'ImgRot',	'ImgRes',
                     'CreateOrd', 'PayOrd', 'FuncAvg', 'TcktApp', 'TripInfApp', 'GetLeftApp', 'CancApp', 'AppAvg']

global_fontsize = -15

plot_names = bench_names_final[:]
fig, ax = plt.subplots(figsize=(12, 6))
index = np.arange(len(plot_names))
bar_width = 0.2
start_gap = -0.5
# start_gap = -0.05
patterns = ['x', '/', 'xx', '\\']
start = 1

low_load_new = []
med_load_new = []
high_load_new = []

rects1 = ax.bar(start_gap + index + 0 * bar_width - start, low_load_new, bar_width, color='azure', label="Low Load")
rects2 = ax.bar(start_gap + index + 1 * bar_width - start, med_load_new, bar_width, color='paleturquoise', label="Medium Load")
rects3 = ax.bar(start_gap + index + 2 * bar_width - start, high_load_new, bar_width, color='darkturquoise', label="High Load")


# plt.axvline(x=8.2, color='b', linewidth=3, linestyle="--")
# ax.text(3, 0.32, 'Functions', ha='center', va='bottom', fontsize=global_fontsize+28)
# ax.text(11, 0.32, 'Applications', ha='center', va='bottom', fontsize=global_fontsize+28)

ax.margins(x=0.01)
ax.set_ylim([0, 0.402])
ax.set_yticks(np.arange(0, 0.41, 0.1))
ax.tick_params(axis="y", labelsize=global_fontsize+30, pad=0)
ax.set_ylabel("Norm. Tail Latency", fontsize=global_fontsize+30)
ax.tick_params(axis='x', which='major', pad=0, labelsize=global_fontsize+30)
ax.set_xticks(start_gap + index + bar_width * 1 - start)
ax.set_xticklabels(bench_names_final)
ax.tick_params(axis="x", labelsize=global_fontsize+30, rotation=45)
#ax.legend(loc=2, ncol=10, mode=None, borderaxespad=0., frameon=False, fontsize=global_fontsize +30)
ax.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", mode="expand", borderaxespad=0, fancybox=True, shadow=True,
          ncol=10, frameon=False, fontsize=global_fontsize + 28)

ax.grid(visible=True, axis='y')
plt.tight_layout()
plt.savefig("tail.pdf")
