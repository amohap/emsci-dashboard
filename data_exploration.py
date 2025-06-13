import json
import numpy as np
import pandas as pd

# Load data
df = pd.read_excel('emsci_data_2023.xlsx', sheet_name='qry_rand_CATHERINE_ISNCSCI_Age_')

# check how many entries per patient
# size() returns a Series with the counts of entries per group; RandomID is the grouping key
# and reset_index() converts it to a DataFrame and moves RandomID back to a column while renaming the counts column to 'counts'
grouped = df.groupby('RandomID').size().reset_index(name='counts')

# Check if every patient has 5 entries
if not (grouped['counts'] == 5).all():
    raise ValueError("Not all patients have exactly 5 entries. Check the data.")

# Check if the ExamStage is in chronological order for each patient (stages are 'very acute', 'acute I', 'acute II', 'acute III', 'chronic')
if not df.groupby('RandomID')['ExamStage'].apply(lambda x: list(x) == sorted(x.unique(), key=lambda y: ['very acute', 'acute I', 'acute II', 'acute III', 'chronic'].index(y))).all():
    raise ValueError("ExamStage is not in chronological order for all patients. Check the data.")

# summary total number of patients, AgeatDOI, Sex, Cause
summary = df.groupby('RandomID').agg(
    AgeAtDOI=('AgeAtDOI', 'first'),
    Sex=('Sex', 'first'),
    Cause=('Cause', 'first')
).reset_index()

# Create cleaned-up dictionary
results = {
    'total_patients': int(summary['RandomID'].nunique()),

    'age_stats': {
        'count': int(summary['AgeAtDOI'].count()),
        'missing': int(summary['AgeAtDOI'].isna().sum()),
        'min': float(summary['AgeAtDOI'].min()),
        'max': float(summary['AgeAtDOI'].max()),
        'mean': round(float(summary['AgeAtDOI'].mean()), 2),
        'median': round(float(summary['AgeAtDOI'].median()), 2),
        'std': round(float(summary['AgeAtDOI'].std()), 2)
    },

    'sex_distribution': {
        'counts': {k: int(v) for k, v in summary['Sex'].value_counts().items()},
        'missing': int(summary['Sex'].isna().sum())
    },

    'cause_distribution': {
        'counts': {k: int(v) for k, v in summary['Cause'].value_counts().items()},
        'missing': int(summary['Cause'].isna().sum())
    }
}

# Pretty-print the dictionary
print(json.dumps(results, indent=2, sort_keys=True))

# Clean AIS column
df['AIS'] = df['AIS'].astype(str).str.strip().str.upper()

# Pivot so each patient has one row, each stage is a column
stage_order = ['very acute', 'acute I', 'acute II', 'acute III', 'chronic']
ais_pivot = df.pivot(index='RandomID', columns='ExamStage', values='AIS')
ais_pivot = ais_pivot.reindex(columns=stage_order)

# Count AIS grades in each stage
ais_stage_counts = ais_pivot.apply(lambda col: col.value_counts(dropna=False)).fillna(0).astype(int).to_dict()

# Count pairwise changes from one stage to the next
pairwise_changes = {}
for i in range(len(stage_order) - 1):
    from_stage = stage_order[i]
    to_stage = stage_order[i + 1]
    stage_df = ais_pivot[[from_stage, to_stage]].dropna()
    changes = (stage_df[from_stage] != stage_df[to_stage]).value_counts()
    pairwise_changes[f'{from_stage} -> {to_stage}'] = {
        'changed': int(changes.get(True, 0)),
        'unchanged': int(changes.get(False, 0))
    }

# Add explicit transition from very acute to chronic
if 'very acute' in ais_pivot.columns and 'chronic' in ais_pivot.columns:
    va_chronic_df = ais_pivot[['very acute', 'chronic']].dropna()
    changes_va_chronic = (va_chronic_df['very acute'] != va_chronic_df['chronic']).value_counts()
    pairwise_changes['very acute -> chronic'] = {
        'changed': int(changes_va_chronic.get(True, 0)),
        'unchanged': int(changes_va_chronic.get(False, 0))
    }


# Count who changed at all vs. remained the same
valid_patients = ais_pivot.dropna()
n_unique_grades = valid_patients.nunique(axis=1)
total_change_summary = {
    'remained_same_all_stages': int((n_unique_grades == 1).sum()),
    'changed_at_least_once': int((n_unique_grades > 1).sum())
}

# Count explicit transitions from very acute to chronic
start_end_df = ais_pivot[['very acute', 'chronic']].dropna()
explicit_transitions = start_end_df.apply(lambda row: f"{row['very acute']} -> {row['chronic']}", axis=1)
explicit_transition_counts = explicit_transitions.value_counts().to_dict()

# Final summary dictionary
ais_summary = {
    'ais_stage_counts': ais_stage_counts,
    'pairwise_changes': pairwise_changes,
    'total_change_summary': total_change_summary,
    'explicit_transitions_very_acute_to_chronic': {k: int(v) for k, v in explicit_transition_counts.items()}
}

print(json.dumps(ais_summary, indent=2, sort_keys=True))

# Combine both summaries
all_results = {
    'demographic_summary': results,
    'ais_analysis': ais_summary
}

# Save all results to a JSON file
with open('summary_results.json', 'w') as f:
    json.dump(all_results, f, indent=2, sort_keys=True)

print("All results saved to 'summary_results.json'")
