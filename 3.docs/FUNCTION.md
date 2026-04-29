<!-- LLM_IGNORE_START -->
# FinanceIQ - Success DNA Forecasting Platform

## Algorithmic Scoring System

The FinanceIQ platform implements a comprehensive multi-method scoring system that evaluates stock performance using historical data and machine learning algorithms. The system combines both traditional financial metrics and advanced machine learning techniques to provide robust predictions.

### Core Components

#### 1. Parameter Catalog
The platform uses a comprehensive set of financial parameters grouped by category:

- **Karlilik (Profitability)**:
  - ROE (Return on Equity)
  - ROA (Return on Assets)
  - Brut Kar Marji (Gross Profit Margin)
  - FAVOK Marji (Operating Profit Margin)
  - Net Kar Marji (Net Profit Margin)

- **Nakit Akisi (Cash Flow)**:
  - FCF (Free Cash Flow)
  - OCF (Operating Cash Flow)

- **Buyume (Growth)**:
  - Net Kar Buyumesi (Net Income Growth)
  - FAVOK Buyumesi (Operating Income Growth)
  - FCF Buyumesi (Free Cash Flow Growth)

- **Borc/Risk (Leverage/Risk)**:
  - Net Borc / FAVOK (Debt to Operating Cash Flow)
  - Borc / Ozsermaye (Debt to Equity)
  - Faiz Karsilama (Interest Coverage Ratio)
  - Net Borc / Equity (Net Debt to Equity)

- **Verimlilik (Efficiency)**:
  - Asset Turnover
  - Inventory Turnover
  - Receivables Turnover
  - Working Capital Turnover

- **Degerleme (Valuation)**:
  - F/K (P/E Ratio)
  - PD/DD (P/B Ratio)
  - FD/FAVOK (Enterprise Value to Operating Cash Flow)
  - PEG Ratio

- **Likidite (Liquidity)**:
  - Current Ratio
  - Quick Ratio
  - Cash Ratio

- **Temettu (Dividend)**:
  - Temettu Verimi (Dividend Yield)

#### 2. Data Processing Pipeline

1. **Data Import**: 
   - Excel files with historical winner stocks (2023, 2024, 2025)
   - Quarterly fundamentals CSV upload (must match the structure and data quality of `@CLEANED_Financial/` directory)

2. **Exact Ratio Computation**:
   - All parameters are computed using exact financial data rather than proxy formulas
   - Computation based on quarterly fundamentals data
   - All ratios are calculated using the formulas specified in the catalog
   - The `@CLEANED_Financial/` directory contains the main and correct data for parameters

3. **Feature Engineering**:
   - Data normalization and standardization
   - Statistical measures (mean, standard deviation, coefficient of variation)
   - Temporal analysis across multiple years

#### 3. Machine Learning Methods

The system employs multiple machine learning approaches to compute parameter importance scores:

1. **Spearman Correlation**:
   - Measures monotonic relationships between parameters and returns
   - Ranks parameters by their correlation strength
   - Handles non-linear relationships well

2. **Pearson Correlation**:
   - Measures linear relationships between parameters and returns
   - Provides baseline correlation scores

3. **Mutual Information**:
   - Measures information gain between parameters and returns
   - Captures both linear and non-linear dependencies
   - More robust than correlation for complex relationships

4. **Random Forest Importance**:
   - Uses ensemble learning to determine parameter importance
   - Provides robust feature selection
   - Handles interactions between parameters

5. **Recursive Feature Elimination (RFE)**:
   - Sequential feature selection method
   - Identifies most important features iteratively
   - Uses a base estimator to rank features

6. **LASSO Regression**:
   - Linear regression with L1 regularization
   - Performs feature selection and shrinkage
   - Identifies parameters with significant predictive power

7. **SHAP Values**:
   - Shapley value-based explanations
   - Provides detailed contribution analysis
   - Offers model interpretability

8. **Clustering Similarity**:
   - Uses KMeans clustering to identify parameter patterns
   - Measures similarity between parameter values across stocks
   - Provides clustering-based importance scores

#### 4. Ensemble Scoring System

The final parameter scores are computed using a weighted ensemble approach:

- **Cross-sectional Score** (30% weight):
  - Measures parameter variation within a year
  - Normalized by coefficient of variation

- **Temporal Score** (20% weight):
  - Measures parameter stability across years
  - Uses temporal consistency analysis

- **Transition Score** (10% weight):
  - Measures parameter volatility over time
  - Uses z-score analysis

- **Ensemble Score** (40% weight):
  - Combines all ML method scores
  - Weighted average of Spearman, Pearson, Mutual Info, RF, RFE, LASSO, SHAP, and Clustering scores

#### 5. Model Types

The platform supports different prediction models:

1. **Scoring Model** (Default):
   - Uses ensemble parameter weights for prediction
   - Standard scoring approach

2. **DBSCAN Model**:
   - Uses density-based clustering for anomaly detection
   - Identifies outliers in parameter space

3. **GMM Model**:
   - Gaussian Mixture Model approach
   - Uses probabilistic clustering

4. **XGBoost Model**:
   - Gradient boosting approach
   - Weighted parameter contributions

5. **Prophet Model**:
   - Time series forecasting
   - Incorporates trend information

6. **ARIMA Model**:
   - Autoregressive integrated moving average
   - Time series analysis approach

#### 6. Evaluation Methods

The system uses time-CV (rolling window) evaluation:

- **Rolling Window**: Uses 2-year windows to evaluate model stability
- **Rank Stability**: Measures how consistently parameters rank across time
- **Overlap Analysis**: Measures how many stocks maintain similar rankings

#### 7. Risk Factors

The scoring system incorporates risk adjustments:

- **Low Risk**: 85% weight adjustment
- **Medium Risk**: 100% weight (default)
- **High Risk**: 115% weight adjustment

This comprehensive approach ensures robust, multi-dimensional stock evaluation that combines traditional financial analysis with modern machine learning techniques.
<!-- LLM_IGNORE_END -->
