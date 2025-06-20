# Step 1: Import Required Libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os

# Create directories if they don't exist
os.makedirs('data/raw', exist_ok=True)
os.makedirs('data/processed', exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('results', exist_ok=True)


# Load Dataset
def load_data(file):
    """Load the dataset from a file"""
    print(f"Loading data from {file}...")
    df = pd.read_csv(file)
    print(f"Dataset loaded with shape: {df.shape}")
    return df

# Example usage:
# df = load_data('data/raw/your_ghg_dataset.csv')

# Step 3: Data Preprocessing (EDA+Cleaning+Encoding)
def explore_data(df):
    """Perform exploratory data analysis"""
    print("\nExploratory Data Analysis:")
    print("\nFirst 5 rows:")
    print(df.head())
    
    print("\nData types:")
    print(df.dtypes)
    
    print("\nSummary statistics:")
    print(df.describe())
    
    print("\nMissing values:")
    print(df.isnull().sum())
    
    # Visualize the distribution of the target variable
    plt.figure(figsize=(10, 6))
    sns.histplot(df['emissions'], kde=True)  # Update with your actual target column
    plt.title('Distribution of GHG Emissions')
    plt.xlabel('Emissions')
    plt.ylabel('Frequency')
    plt.savefig('results/emissions_distribution.png')
    plt.close()
    
    # Correlation matrix for numerical features
    numerical_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    corr_matrix = df[numerical_cols].corr()
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    plt.title('Correlation Matrix of Numerical Features')
    plt.tight_layout()
    plt.savefig('results/correlation_matrix.png')
    plt.close()
    
    return numerical_cols

def preprocess_data(df, target_column='emissions'):
    """Preprocess the data for modeling"""
    print("\nPreprocessing data...")
    
    # Make a copy of the dataframe
    df_processed = df.copy()
    
    # Identify numerical and categorical columns
    numerical_cols = df_processed.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df_processed.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Remove target from features if present
    if target_column in numerical_cols:
        numerical_cols.remove(target_column)
    
    # Create preprocessing pipelines
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    # Combine preprocessing steps
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numerical_transformer, numerical_cols),
            ('cat', categorical_transformer, categorical_cols)
        ])
    
    # Split the data into features and target
    X = df_processed.drop(target_column, axis=1)
    y = df_processed[target_column]
    
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training set shape: {X_train.shape}")
    print(f"Testing set shape: {X_test.shape}")
    
    # Fit the preprocessor on the training data
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # Save the preprocessor
    joblib.dump(preprocessor, 'models/preprocessor.pkl')
    
    return X_train_processed, X_test_processed, y_train, y_test, preprocessor


# Step 4: Training
def train_linear_regression(X_train, y_train):
    """Train a Linear Regression model"""
    print("\nTraining Linear Regression model...")
    model = LinearRegression()
    model.fit(X_train, y_train)
    print("Linear Regression model trained.")
    return model

# Step 6: Hyperparameter Tuning
def tune_random_forest(X_train, y_train):
    """Tune hyperparameters for Random Forest using GridSearchCV"""
    print("\nTuning Random Forest hyperparameters...")
    
    # Define the parameter grid
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    
    # Create the model
    rf = RandomForestRegressor(random_state=42)
    
    # Create the grid search
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=5,
        n_jobs=-1,
        scoring='neg_mean_squared_error',
        verbose=1
    )
    
    # Fit the grid search
    grid_search.fit(X_train, y_train)
    
    # Get the best parameters and model
    best_params = grid_search.best_params_
    best_model = grid_search.best_estimator_
    
    print(f"Best parameters: {best_params}")
    print(f"Best RMSE: {np.sqrt(-grid_search.best_score_):.4f}")
    
    return best_model


# Step 5: Prediction and Evaluation
def evaluate_model(model, X_test, y_test, model_name):
    """Evaluate model performance using multiple metrics"""
    print(f"\nEvaluating {model_name}...")
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Print metrics
    print(f"{model_name} performance:")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"R² Score: {r2:.4f}")
    
    # Create a dictionary of metrics
    metrics = {
        'Model': model_name,
        'RMSE': rmse,
        'MAE': mae,
        'R²': r2
    }
    
    # Plot actual vs predicted values
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test, y_pred, alpha=0.5)
    
    # Add perfect prediction line
    min_val = min(min(y_test), min(y_pred))
    max_val = max(max(y_test), max(y_pred))
    plt.plot([min_val, max_val], [min_val, max_val], 'r--')
    
    plt.xlabel('Actual')
    plt.ylabel('Predicted')
    plt.title(f'{model_name}: Actual vs Predicted')
    plt.tight_layout()
    plt.savefig(f'results/{model_name.lower().replace(" ", "_")}_predictions.png')
    plt.close()
    
    # Save the model
    joblib.dump(model, f'models/{model_name.lower().replace(" ", "_")}.pkl')
    
    return metrics, y_pred


# Step 7: Comparative Study and Selecting the Best Model
def compare_models(models_metrics):
    """Compare models and select the best one"""
    print("\nComparing models...")
    
    # Create a DataFrame from the metrics
    comparison_df = pd.DataFrame(models_metrics)
    comparison_df = comparison_df.set_index('Model')
    
    # Print the comparison
    print("\nModel Comparison:")
    print(comparison_df)
    
    # Save the comparison to a CSV file
    comparison_df.to_csv('results/model_comparison.csv')
    
    # Create a bar chart for RMSE
    plt.figure(figsize=(10, 6))
    comparison_df['RMSE'].plot(kind='bar', color='skyblue')
    plt.title('RMSE Comparison')
    plt.ylabel('RMSE (lower is better)')
    plt.tight_layout()
    plt.savefig('results/rmse_comparison.png')
    plt.close()
    
    # Create a bar chart for R²
    plt.figure(figsize=(10, 6))
    comparison_df['R²'].plot(kind='bar', color='lightgreen')
    plt.title('R² Comparison')
    plt.ylabel('R² (higher is better)')
    plt.tight_layout()
    plt.savefig('results/r2_comparison.png')
    plt.close()
    
    # Select the best model based on RMSE
    best_model = comparison_df['RMSE'].idxmin()
    print(f"\nBest model based on RMSE: {best_model}")
    
    return best_model


# Main function
def main():
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Step 2: Load Dataset
    # Replace with your actual dataset path
    data_path = 'data/raw/ghg_emissions_data.csv'  
    
    # Check if the dataset exists
    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}")
        print("Please download a GHG emissions dataset and place it in the 'data/raw' directory.")
        print("Recommended sources:")
        print("1. Global Carbon Project: https://www.globalcarbonproject.org/carbonbudget/")
        print("2. EPA Greenhouse Gas Reporting Program: https://www.epa.gov/ghgreporting")
        print("3. World Bank Climate Change Data: https://data.worldbank.org/topic/climate-change")
        print("4. Kaggle GHG Emission Datasets: https://www.kaggle.com/datasets?search=greenhouse+gas+emissions")
        return
    
    df = load_data(data_path)
    
    # Step 3: Data Preprocessing
    numerical_cols = explore_data(df)
    X_train, X_test, y_train, y_test, preprocessor = preprocess_data(df)
    
    # Step 4: Training
    lr_model = train_linear_regression(X_train, y_train)
    rf_model = train_random_forest(X_train, y_train)
    
    # Step 5: Prediction and Evaluation
    lr_metrics, lr_preds = evaluate_model(lr_model, X_test, y_test, "Linear Regression")
    rf_metrics, rf_preds = evaluate_model(rf_model, X_test, y_test, "Random Forest")
    
    # Step 6: Hyperparameter Tuning
    tuned_rf_model = tune_random_forest(X_train, y_train)
    tuned_rf_metrics, tuned_rf_preds = evaluate_model(tuned_rf_model, X_test, y_test, "Tuned Random Forest")
    
    # Step 7: Comparative Study and Selecting the Best Model
    models_metrics = [lr_metrics, rf_metrics, tuned_rf_metrics]
    best_model = compare_models(models_metrics)
    
    print("\nGHG Emission Prediction Model completed successfully!")
    print(f"Results and models saved in 'results' and 'models' directories.")

if __name__ == "__main__":
    main()