import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
import matplotlib.pyplot as plt
import seaborn as sns





def clean_and_transform_target(data, target_column=None, method=['auto', 'auto']):
    """
    Cleans and potentially transforms a target variable in a dataset based on a specified method.
    The method includes both the data type and the action for handling missing values or transformations.

    Parameters:
    - data (pd.DataFrame): The dataset containing the target variable.
    - target_column (str): The name of the target variable column.
    - method (list): A two-element list where the first element specifies the data type
                     ('numerical', 'categorical', 'auto') and the second element specifies
                     the action ('mean', 'median', 'mode', 'drop', 'encode', 'missing', 'zero').

    Returns:
    - pd.DataFrame: Dataset with the cleaned or transformed target variable.
    """
    data_type, action = method
    if not target_column:
        column_names=data.columns.tolist()
        for x in column_names:
            data=clean_and_transform_target(data,x)
    
    if data_type == 'auto':
        if data[target_column].dtype in [np.int64, np.float64]:
            data_type = 'numerical'
        else:
            data_type = 'categorical'
    
    if data_type == 'numerical':
        if action == 'mean':
            fill_value = data[target_column].mean()
        elif action == 'median':
            fill_value = data[target_column].median()
        elif action == 'zero':
            fill_value = 0
        elif action == 'drop':
            return data.dropna(subset=[target_column])
        data[target_column].fillna(fill_value, inplace=True)
    
    elif data_type == 'categorical':
        if action == 'mode':
            fill_value = data[target_column].mode()[0]
        elif action == 'missing':
            fill_value = 'Missing'
        elif action == 'drop':
            return data.dropna(subset=[target_column])
        elif action == 'encode':
            # Perform one-hot encoding on the target variable
            data = pd.get_dummies(data, columns=[target_column], prefix=target_column, dummy_na=True)
            return data
        data[target_column].fillna(fill_value, inplace=True)
    
    return data




def transform_and_scale(data, target_columns=None):
    """
    
    
    Parameters:
    - data (pd.DataFrame): input dataframe
    - target_columns (list or None): specific columns to process, else all numeric
    
    Returns:
    - pd.DataFrame: transformed dataframe
    """
    df = data.copy()
    scaler = StandardScaler()
    
    if target_columns is None:
        target_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    skewness = df[target_columns].skew()
    
    for col in target_columns:
        val = skewness[col]
        original = df[col].copy()
        
        # Right skew → log1p + scale
        if val >= 1:
            df[col] = np.log1p(df[col] - df[col].min() + 1)  # shift to avoid negatives
            df[col] = scaler.fit_transform(df[[col]])
        
        # Left skew → cube if negatives exist, else square
        elif val <= -1:
            if (df[col] < 0).any():
                df[col] = np.power(df[col], 3)
            else:
                df[col] = np.power(df[col], 2)
            df[col] = scaler.fit_transform(df[[col]])
        
        # Nearly normal → only scale
        elif -1 < val < 1:
            df[col] = scaler.fit_transform(df[[col]])
        
        # Plot before vs after
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        
        sns.kdeplot(original, fill=True, ax=axes[0], color="skyblue")
        axes[0].set_title(f"{col} - Before (Skew={val:.2f})")
        
        sns.kdeplot(df[col], fill=True, ax=axes[1], color="lightgreen")
        axes[1].set_title(f"{col} - After")
        
        plt.suptitle(f"Normality Check for {col}")
        plt.show()
    
    return df
def make_mi_scores(X, y, discrete_features='auto'):
    """
    Compute mutual information scores for features against target y.
    Automatically detects whether to use classification or regression MI.
    
    Parameters:
    - X (pd.DataFrame): Features
    - y (pd.Series or np.array): Target variable
    - discrete_features: 'auto', bool array, or indices of discrete features
    
    """
    # Detect if classification or regression
    if pd.api.types.is_numeric_dtype(y):
        task_type = "regression"
        mi = mutual_info_regression(X, y, discrete_features=discrete_features, random_state=0)
    else:
        task_type = "classification"
        mi = mutual_info_classif(X, y, discrete_features=discrete_features, random_state=0)
    
    mi_scores = pd.Series(mi, index=X.columns).sort_values(ascending=False)
    print(f"Task detected: {task_type}")
    return mi_scores

                
                
             
        
    