import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import roc_auc_score, roc_curve
from scipy.stats import mannwhitneyu

df = pd.read_csv('mri_dose_outcomes_merged.csv')

# ============ Figure 3: dose stratified by toxicity grade ============
fig, axes = plt.subplots(1, 2, figsize=(11, 5))

# Bladder dose by Late GU grade
ax = axes[0]
gu = df.dropna(subset=['late_GU', 'Bladder_Dmean_Gy'])
groups = [gu[gu.late_GU == g]['Bladder_Dmean_Gy'].values for g in [0, 1, 2]]
bp = ax.boxplot(groups, labels=[f'Grade 0\n(n={len(groups[0])})', f'Grade 1\n(n={len(groups[1])})', f'Grade 2\n(n={len(groups[2])})'],
                 patch_artist=True, widths=0.6)
for patch, c in zip(bp['boxes'], ['#8FBCE6', '#F5B461', '#E06666']):
    patch.set_facecolor(c); patch.set_alpha(0.8)
ax.set_ylabel('Bladder Mean Dose (Gy)')
ax.set_title('Bladder Dose vs. 1-yr Late GU Toxicity Grade\n(MRI-planned cohort, n=64)', fontsize=11)
ax.grid(axis='y', alpha=0.3)
stat, p = mannwhitneyu(groups[0], groups[2], alternative='two-sided')
ax.text(0.5, 0.95, f'Grade 0 vs 2: p={p:.3f}', transform=ax.transAxes, ha='center', fontsize=9)

# Rectum dose by Late GI presence
ax2 = axes[1]
gi = df.dropna(subset=['late_GI', 'Rectum_Dmean_Gy'])
groups2 = [gi[gi.late_GI == g]['Rectum_Dmean_Gy'].values for g in [0, 1]]
bp2 = ax2.boxplot(groups2, labels=[f'No GI tox\n(n={len(groups2[0])})', f'GI tox Gr1\n(n={len(groups2[1])})'],
                   patch_artist=True, widths=0.6)
for patch, c in zip(bp2['boxes'], ['#8FBCE6', '#E06666']):
    patch.set_facecolor(c); patch.set_alpha(0.8)
ax2.set_ylabel('Rectum Mean Dose (Gy)')
ax2.set_title('Rectum Dose vs. 1-yr Late GI Toxicity\n(only 5 events \u2014 descriptive only)', fontsize=11)
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('fig3_dose_vs_toxicity.png', dpi=150, bbox_inches='tight')
plt.close()

# ============ Logistic regression: bladder dose -> GU toxicity (grade>=2) ============
model_df = df.dropna(subset=['late_GU', 'Bladder_Dmean_Gy', 'Bladder_V50pctRx']).copy()
model_df['GU_high'] = (model_df['late_GU'] >= 2).astype(int)
print(f"N for GU model: {len(model_df)}, events (grade>=2): {model_df['GU_high'].sum()}")

X = model_df[['Bladder_Dmean_Gy', 'Bladder_V50pctRx']].values
y = model_df['GU_high'].values

clf = LogisticRegression()
clf.fit(X, y)

# Leave-one-out cross-validated AUC (honest estimate given small n)
loo = LeaveOneOut()
y_proba = cross_val_predict(LogisticRegression(), X, y, cv=loo, method='predict_proba')[:, 1]
auc = roc_auc_score(y, y_proba)
print(f"Coefficients: Dmean={clf.coef_[0][0]:.4f}, V50pctRx={clf.coef_[0][1]:.4f}, intercept={clf.intercept_[0]:.4f}")
print(f"Leave-one-out cross-validated AUC: {auc:.3f}")

# ============ Figure 4: ROC + predicted probability curve vs Bladder Dmean ============
fig2, axes2 = plt.subplots(1, 2, figsize=(11, 5))

fpr, tpr, _ = roc_curve(y, y_proba)
axes2[0].plot(fpr, tpr, color='#4C72B0', lw=2, label=f'AUC = {auc:.2f}')
axes2[0].plot([0, 1], [0, 1], '--', color='gray')
axes2[0].set_xlabel('False Positive Rate')
axes2[0].set_ylabel('True Positive Rate')
axes2[0].set_title('LOOCV ROC: Bladder Dose \u2192 Grade\u22652 Late GU Toxicity', fontsize=10)
axes2[0].legend(loc='lower right')
axes2[0].grid(alpha=0.3)

# fitted probability curve vs Dmean, holding V50pctRx at median
dmean_range = np.linspace(model_df['Bladder_Dmean_Gy'].min(), model_df['Bladder_Dmean_Gy'].max(), 100)
v50_median = model_df['Bladder_V50pctRx'].median()
X_range = np.column_stack([dmean_range, np.full_like(dmean_range, v50_median)])
probs = clf.predict_proba(X_range)[:, 1]
axes2[1].plot(dmean_range, probs, color='#DD8452', lw=2)
axes2[1].scatter(model_df['Bladder_Dmean_Gy'], model_df['GU_high'], alpha=0.5, color='#4C72B0', s=30)
axes2[1].set_xlabel('Bladder Mean Dose (Gy)')
axes2[1].set_ylabel('P(Grade \u2265 2 Late GU Toxicity)')
axes2[1].set_title('Fitted Dose-Response Curve\n(V50pctRx held at cohort median)', fontsize=10)
axes2[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('fig4_ntcp_model.png', dpi=150, bbox_inches='tight')
plt.close()
print("done")
