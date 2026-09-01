import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

df = pd.read_csv('dvh_metrics_combined.csv')

plt.rcParams['font.family'] = 'DejaVu Sans'

# ---- Figure 1: Bladder & Rectum, CT vs MRI ----
shared_organs = ['Bladder', 'Rectum']
fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))

for ax, metric, title in zip(axes, ['Dmean_Gy', 'V50pctRx'],
                              ['Mean Dose (Gy)', 'Volume Receiving \u226550% of Rx Dose (%)']):
    data_to_plot = []
    labels = []
    colors = []
    for organ in shared_organs:
        for cohort, color in [('CT', '#4C72B0'), ('MRI', '#DD8452')]:
            vals = df[(df.organ == organ) & (df.cohort == cohort)][metric].dropna().values
            data_to_plot.append(vals)
            labels.append(f'{organ}\n({cohort})')
            colors.append(color)
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True, widths=0.6, showmeans=False)
    for patch, c in zip(bp['boxes'], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.75)
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(metric)
    ax.tick_params(axis='x', labelsize=9)
    ax.grid(axis='y', alpha=0.3)

    # significance test per organ
    for idx, organ in enumerate(shared_organs):
        ct_vals = df[(df.organ == organ) & (df.cohort == 'CT')][metric].dropna().values
        mri_vals = df[(df.organ == organ) & (df.cohort == 'MRI')][metric].dropna().values
        if len(ct_vals) > 3 and len(mri_vals) > 3:
            stat, p = mannwhitneyu(ct_vals, mri_vals, alternative='two-sided')
            y = max(ct_vals.max(), mri_vals.max()) * 1.05
            x1, x2 = idx*2, idx*2 + 1
            ax.plot([x1+1, x2+1], [y, y], color='black', lw=1)
            sig = 'p<0.001' if p < 0.001 else f'p={p:.3f}'
            ax.text((x1+x2)/2 + 1, y*1.01, sig, ha='center', fontsize=8)

fig.suptitle('Bladder & Rectum Dose: CT-based vs MRI-based Planning (Prostate SBRT)', fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig('fig1_bladder_rectum_ct_vs_mri.png', dpi=150, bbox_inches='tight')
plt.close()

# ---- Figure 2: CT-only OARs (no MRI comparator available) ----
ct_only_organs = ['Femoral Head (L)', 'Femoral Head (R)', 'Penile Bulb', 'Anal Canal']
fig2, ax2 = plt.subplots(figsize=(9, 5.5))
data_to_plot = [df[(df.organ == o) & (df.cohort == 'CT')]['Dmean_Gy'].dropna().values for o in ct_only_organs]
n_labels = [f'{o}\n(n={len(v)})' for o, v in zip(ct_only_organs, data_to_plot)]
bp2 = ax2.boxplot(data_to_plot, labels=n_labels, patch_artist=True, widths=0.6)
for patch in bp2['boxes']:
    patch.set_facecolor('#55A868')
    patch.set_alpha(0.75)
ax2.set_ylabel('Mean Dose (Gy)')
ax2.set_title('Additional Organs at Risk \u2014 CT-planned Cohort Only\n(no MRI-cohort data available for these structures)', fontsize=12)
ax2.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('fig2_ct_only_oars.png', dpi=150, bbox_inches='tight')
plt.close()

print("done")
