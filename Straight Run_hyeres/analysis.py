import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from IPython.display import display
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score

import statsmodels.api as sm
import statsmodels.formula.api as smf

import scipy.stats as stats
from sklearn.preprocessing import RobustScaler
import warnings
warnings.filterwarnings("ignore")

def show_correlation_matrix(dataframe, taille_figure=(6, 4), cmap="coolwarm"):
    plt.figure(figsize=taille_figure)
    sns.heatmap(dataframe.corr(), cmap=cmap, center=0)
    plt.title("Correlation matrix")
    plt.show()

def show_target_correlation(df, variable="SOG", taille_figure=(6, 4)):
    corr_with_vmg = df.corr()[variable].sort_values(ascending=False)
    #print(f"Correlation with {variable} :")
    # print(corr_with_vmg)
    
    plt.figure(figsize=taille_figure)
    sns.heatmap(corr_with_vmg.to_frame(), annot=True, cmap="coolwarm")
    plt.title(f"Correlation with {variable}")
    plt.show()

def compute_anova(df, target="SOG", max_null_ratio=0.2):
    df_copy = df.copy()
    selected_features = df.columns.drop(target).tolist()

    formula = f"{target} ~ " + " + ".join(selected_features)
    
    try:
        # Fit model and compute ANOVA
        model = smf.ols(formula=formula, data=df).fit()
        anova_results = sm.stats.anova_lm(model, typ=2)
        
        # Add effect size (partial eta squared)
        anova_results['partial_eta_sq'] = anova_results['sum_sq'] / (anova_results['sum_sq'] + model.ssr)
    
        return anova_results.sort_values("F", ascending=False)
    
    except Exception as e:
        print(f"\nError in ANOVA computation: {str(e)}")
        return pd.DataFrame()

from sklearn.linear_model import LinearRegression
import pandas as pd

def linear_regression(df, target="SOG"):
    """
    Fits a linear regression to describe relationships in the dataset.
    No train-test split (assumes descriptive use only).
    """
    # Drop rows with missing target values
    df_clean = df.dropna(subset=[target]).copy()
    X = df_clean.drop(columns=[target])
    y = df_clean[target]
    
    # Fit model
    model = LinearRegression()
    model.fit(X, y)
    
    # Get coefficients
    coef_df = pd.DataFrame({
        'feature': X.columns,
        'coefficient': model.coef_
    }).sort_values('coefficient', key=abs, ascending=False)
    
    # Print summary
    print(f"R²: {model.score(X, y):.3f}")
    print("\nTop coefficients:")
    print(coef_df.head(10).to_string(index=False))
    
    return coef_df

def t_test(df1, df2, target="SOG"):
    t_stat, p_value = stats.ttest_ind(df1[target].dropna(), df2[target].dropna())
    print(f"T-statistic: {t_stat:.3f}, p-value: {p_value:.15f}")
    
    # If p-value is less than 0.05, the difference is statistically significant
    if p_value < 0.05:
        print("The difference is statistically significant, keeping data split.")
    else:
        print("The difference is not statistically significant, keeping data combined.")

def clean(df, target, max_null_ratio):
    df_copy = df.copy()

    # Initial columns and NaN analysis
    initial_cols = df_copy.columns.drop(target)
    print(f"\nInitial features ({len(initial_cols)}): {list(initial_cols)}")

    # Identify columns with too many NaN
    null_ratios = df_copy[initial_cols].isna().mean()
    high_null_cols = null_ratios[null_ratios > max_null_ratio].index.tolist()

    if high_null_cols:
        print(f"\nRemoved features (> {max_null_ratio:.0%} NaN): {high_null_cols}")
        cols = [c for c in initial_cols if c not in high_null_cols]
    else:
        cols = initial_cols.tolist()

    print(f"\nSelected features ({len(cols)}): {cols}")

    # Keep only selected features and target
    df_reduced = df_copy[cols + [target]]

    # Drop rows with NaNs
    initial_samples = len(df_reduced)
    df_clean = df_reduced.dropna()
    remaining_samples = len(df_clean)

    print(f"\nData cleaning:")
    print(f"- Initial samples: {initial_samples}")
    print(f"- Removed samples with NaNs: {initial_samples - remaining_samples}")
    print(f"- Final samples: {len(df_clean)}")

    if len(df_clean) == 0:
        raise ValueError("No valid samples remaining after NaN removal")
    return df_clean


def full_analysis(df_numeric, target_variable,max_null_ratio):
    df_clean = clean(df_numeric, target_variable, max_null_ratio)
    print(f"\nCorrelation with {target_variable}:")
    show_target_correlation(df_clean, variable=target_variable)

    # Compute and display ANOVA results
    print("\nANOVA:")
    anova_results = compute_anova(df_clean, target=target_variable)
    display(anova_results)

    # Apply and display polynomial regression results
    print("\nPolynomial fit:")
    regression_results = linear_regression(df_clean, target=target_variable)
    display(regression_results)