#!/usr/bin/env python
# coding: utf-8

# # Data Preparation
# ### Import necessary modules

# In[1]:


import pandas as pd
import numpy as np

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

import warnings
warnings.filterwarnings("ignore")


# ### Read data into dataframe

# In[2]:


bottle_df = pd.read_csv("bottle.csv")
bottle_df.head()


# ### Rename Columns

# In[3]:


columns = ["Cast Count", "Bottle Count", "Station ID", "Depth ID", "Depth", "Temperature", "Salinity",
           "O2_mL/L", "H2O Density", "O2 Sat", "O2_µmol/Kg", "Bottle No", "Record Indicator",
           "Temperature Precision", "Temperature Quality", "Salinity Precision", "Salinity Quality",
           "Pressure Quality", "O2 Quality", "H20_Density Quality", "O2_Saturation Quality",
           "Chlorophyll-a", "Chlorophyll-a Quality", "Phaeophytin_Concentration", "Phaeophytin Quality", "Phosphate Concentration",
           "Phosphate Quality", "Silicate Concentration", "Silicate Quality", "Nitrite Concentration",
           "Nitrite Quality", "Nitrate Concentration", "Nitrate Quality", "NH4 Concentration", "NH4 Quality",
           "C14_As1", "C14_As1 Precision", "C14_As1 Quality", "C14_As2", "C14_As2 Precision", "C14_As2 Quality",
           "C14_As_Dark", "C14_As_Dark Precision", "C14_As_Dark Quality", "Mean_C14_As", "Mean_C14_As Precision",
           "Mean_C14_As Quality", "Incubation Time", "Light Intensity", "Reported Depth", "Reported Temperature",
           "Reported Potential Temperature", "Reported Salinity", "Reported Potential Density",
           "Reported Specific Volume Anomaly", "Reported Dynamic Height", "Reported O2_mL/L", "Reported O2 Sat",
           "Reported Silicate Concentration", "Reported Phosphate Concentration", "Reported Nitrate Concentration",
           "Reported Nitrite Concentration", "Reported NH4 Concentration", "Reported Chlorophyll-a",
           "Reported Phaeophytin", "Pressure (decibars)", "Sample No", "Dissolved_Inorganic_Carbon1",
           "Dissolved_Inorganic_Carbon2", "Total Alkalinity1", "Total Alkalinity2", "pH2", "pH1",
           "DIC Quality Comment"
          ]

bottle_df.columns = columns

bottle_df.head()


# ### Check shape of dataframe

# In[ ]:


bottle_df.shape


# ### Check info of dataframe

# In[ ]:


bottle_df.iloc[:, 0:4].head()


# In[ ]:


#bottle_df.info()


# **We can see we have quite a number of missing values which will be dealt with going forward**
# 
# **The first four columns have no missing values (they are more of identifiers) so they won't be involved in preprocessing steps like imputation and scaling**
# 

# ### Define a function that will handle the full preprocessing of the data

# In[4]:


def preprocess_data(drop_threshold=70, num_strategy="mean",
                    cat_strategy="most_frequent", fill_value=-999,
                    scaling="standard", file_name="prepared_data.csv"):
    """
    drop_threshold can accept any value between 0 and 100;
    num_strategy can accept "mean", "median" or "constant"
    fill_value: to be specified when num_strategy = "constant"...can take any value
    scaling can accept "standard" or "normal"
    file_name should be specified
    """
    
    data = bottle_df.copy() # make a copy of the original dataframe
    
    """"Drop columns with percent of missing values greater than the threshold"""
    # Get the percentage of missing values for each column
    percent_missing = round(data.isna().sum() / data.shape[0] * 100, 2)
    
    # create a dictionary of the missing values and percent per column
    values = {"Total number of missing values": data.isna().sum(), "Percent of Missing Values": percent_missing}
    
    # convert the dictionary to a dataframe
    missing = pd.DataFrame(values)
    
    # get the columns that fall above the drop_threshold 
    columns_to_drop = missing[missing["Percent of Missing Values"] > drop_threshold].index
    
    # drop the columns
    data.drop(columns_to_drop, axis=1, inplace=True)
    
    # since salinity is the target feature, it should no have missing values
    data.dropna(subset=["Salinity"], inplace=True)
    
    # As earlier stated, exclude the first four columns from the following steps
    new_data = data.iloc[:, 4:]
    """split the dataset into continuous and categorical columns""" 
    # create an empty dictionary to hold the number of unique values per column
    uniques = {}
    
    # iterate through the data columns and append the number of unique values in each column to the
    # unique dictionary
    for column in new_data.columns:
        uniques[column] = new_data[column].nunique()
    
    # from careful examination, a threshold of 6 unique values seems to be appropriate for the split
    
    # get the categorical and continuous columns based on the threshold 
    cat_attributes = [column for column in uniques if uniques[column] <= 6]
    num_attributes = [column for column in uniques if uniques[column] > 6]
    
    # Create a new dataframe with the created attributes in a specific order
    new_data = pd.concat([new_data[num_attributes], new_data[cat_attributes]], axis=1)
    
    """Create a pipeline for imputation and scaling"""
    # create a SimpleImputer object for the numerical columns based on the specified strategy
    if num_strategy == "constant":
        numerical_imputer = SimpleImputer(strategy=num_strategy, fill_value=fill_value)
    else:
        numerical_imputer = SimpleImputer(strategy=num_strategy)
    
    # create a SimpleImputer object for the categorical columns based on the specified strategy 
    categorical_imputer = SimpleImputer(strategy=cat_strategy)
    
    # create a scaling object for standardization or normalization
    if scaling == "standard":
        scaler = StandardScaler()
    elif scaling == "normal":
        scaler = MinMaxScaler()
        
    # Create a pipeline to perform imputation and scaling on the numerical attributes
    numerical_pipeline = Pipeline([("imputer", numerical_imputer), ("scaler", scaler)])
    
    # create a full pipeline for both numerical and categorical attributes
    full_pipeline = ColumnTransformer([("num", numerical_pipeline, num_attributes),
                                       ("cat", categorical_imputer, cat_attributes)])
    
    # Preprocess the data using the full pipeline
    prepared_bottle_df = pd.DataFrame(full_pipeline.fit_transform(new_data),
                                     columns=num_attributes + cat_attributes)
    
    # restore the excluded columns
    excluded_columns = data.iloc[:, 0:4]
    excluded_columns.reset_index(drop=True, inplace=True)
    prepared_bottle_df.reset_index(drop=True, inplace=True)
    
    prepared_df = pd.concat([excluded_columns, prepared_bottle_df], axis=1)
    
    # assert that there are no missing values in the prepared dataframe
    assert not all(prepared_df.isna().sum()) 
    
    # save the dataframe to a csv file
    #prepared_bottle_df.to_csv(file_name)
    
    return prepared_df


# ### Call the function using the default parameters (70% threshold, mean imputation for numerical attributes, modal imputation for categorical attributes, standardization for numerical attributes)

# In[5]:


#processed_bottle = preprocess_data()


# In[6]:


#processed_bottle.to_csv('processed_bottle.csv', index=False)


# In[ ]:




