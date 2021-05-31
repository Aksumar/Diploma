import pandas as pd
from django.core.exceptions import ValidationError
from pandas.api.types import is_numeric_dtype, is_string_dtype


def validate_extention(file):
    if '.csv' in file.name:
        return pd.read_csv(file)
    elif ('.xlsx' in file.name) or ('.xls' in file.name):
        return pd.read_excel(file)

def have_nulls(df):
    if df.isnull().values.any():
        raise ValidationError('В файле содержатся нулевые знаечния.')

def unique_id(df):
    if not df.index.is_unique:
        raise ValidationError('В файле содержатся неуникальные значения в первой колонке.')



def validate_file_content(file):
    df = validate_extention(file)
    have_nulls(df)
