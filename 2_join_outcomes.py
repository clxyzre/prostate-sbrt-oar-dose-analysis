import openpyxl
import pandas as pd
import numpy as np

MRI_FILE = '/mnt/user-data/uploads/Input_Prost_scores_latetoxicity_anyonmized.xlsx'
wb = openpyxl.load_workbook(MRI_FILE, data_only=True, read_only=True)

ws = wb['1-year score_Matched']
rows = list(ws.iter_rows(values_only=True))
header = rows[0]
recs = []
for r in rows[2:]:
    d = dict(zip(header, r))
    if d.get('Patient Key') is None:
        continue
    recs.append({
        'patient_key': int(d['Patient Key']),
        'late_GU': d.get('Late GU'),
        'late_GI': d.get('Late GI'),
        'age': d.get('Age'),
        'ipss': d.get('IPSS'),
        'gland_vol': d.get('GLAND VOL'),
        'risk_group': d.get('Risk Group'),
        'adt_used': d.get('ADT Used?'),
        'spaceoar': d.get('SpaceOAR'),
    })
outcomes = pd.DataFrame(recs)
outcomes['patient_id'] = outcomes['patient_key'].apply(lambda k: f'Pat{k}')
print("Outcomes shape:", outcomes.shape)
print(outcomes['late_GU'].value_counts(dropna=False))
print(outcomes['late_GI'].value_counts(dropna=False))

# dose metrics (MRI cohort only), pivot wide
dose = pd.read_csv('dvh_metrics_combined.csv')
dose_mri = dose[dose.cohort == 'MRI']
wide = dose_mri.pivot_table(index='patient_id', columns='organ',
                             values=['Dmean_Gy','Dmax_Gy','V50pctRx','V90pctRx'])
wide.columns = [f'{organ}_{metric}' for metric, organ in wide.columns]
wide = wide.reset_index()

merged = outcomes.merge(wide, on='patient_id', how='inner')
merged.to_csv('mri_dose_outcomes_merged.csv', index=False)
print("Merged shape:", merged.shape)
print(merged[['patient_id','late_GU','late_GI','Bladder_Dmean_Gy','Rectum_Dmean_Gy']].head(10))
