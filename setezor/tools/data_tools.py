from pandas import DataFrame

def dataframe_prepare(df: DataFrame):
        def preparing(value, list_delimiter='\n'):
            if isinstance(value, list):
                return list_delimiter.join(value)
            else:
                return str(value)
        
        df = df.fillna('')
        for i in df.columns:
            df[i] = df[i].apply(preparing)
        return df