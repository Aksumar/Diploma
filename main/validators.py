from io import StringIO

import pandas as pd
from django.core.exceptions import ValidationError
from pandas.api.types import is_numeric_dtype, is_string_dtype


def getfile(file):
    if '.csv' in file.name:
        file.seek(0)
        return pd.read_csv(file, index_col=0)
    elif ('.xlsx' in file.name) or ('.xls' in file.name):
        return pd.read_excel(file, index_col=0)
    return None


def have_nulls(df):
    if df.isnull().values.any():
        raise ValidationError('В файле содержатся нулевые знаечния.')

def unique_id(df):
    if not df.index.is_unique:
        raise ValidationError('В файле содержатся неуникальные значения в первой колонке.')



def validate_file_content(file):
    print("kdmckd")
    df = getfile(file)
    if df is not None:
        have_nulls(df)
