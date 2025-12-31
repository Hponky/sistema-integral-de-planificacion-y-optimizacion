"""
Utilidades comunes para el parsing de archivos Excel en el módulo de Forecasting.
Contiene funciones reutilizables para normalización de datos y detección de cabeceras.
"""

import pandas as pd
import numpy as np
import datetime
import logging

logger = logging.getLogger(__name__)


class ExcelParserUtils:
    """
    Proporciona utilidades estáticas para el parsing robusto de archivos Excel.
    """

    @staticmethod
    def find_header_and_normalize(df_raw, keywords=None):
        """
        Busca la fila de encabezado en un DataFrame y normaliza los datos.
        
        Args:
            df_raw (pd.DataFrame): DataFrame sin procesar
            keywords (list): Lista de palabras clave para identificar la fila de encabezado
            
        Returns:
            pd.DataFrame: DataFrame con encabezados normalizados
        """
        if keywords is None:
            keywords = ['fecha', 'date', 'intervalo', 'interval', 'llamada', 'call', 'volumen']
        
        for i in range(min(15, len(df_raw))):
            row_vals = [str(v).lower().strip() for v in df_raw.iloc[i].values]
            if any(k in row_vals for k in keywords):
                new_cols = df_raw.iloc[i].values
                df = df_raw.iloc[i+1:].copy()
                df.columns = new_cols
                return df.reset_index(drop=True)
        return df_raw

    @staticmethod
    def format_interval(x):
        """
        Formatea un valor de intervalo de tiempo a formato HH:MM.
        
        Args:
            x: Valor a formatear (puede ser datetime, time, o string)
            
        Returns:
            str: Intervalo formateado como HH:MM
        """
        try:
            if isinstance(x, (datetime.time, datetime.datetime)):
                return x.strftime('%H:%M')
            s_x = str(x).split(' ')[-1]
            if ':' not in s_x:
                return "00:00"
            return pd.to_datetime(s_x).strftime('%H:%M')
        except:
            return "00:00"

    @staticmethod
    def detect_date_column(df, fallback='Fecha'):
        """
        Detecta automáticamente la columna de fecha en un DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame a analizar
            fallback (str): Nombre de columna por defecto si no se encuentra
            
        Returns:
            str: Nombre de la columna de fecha detectada
        """
        for c in df.columns:
            col_lower = str(c).lower()
            if 'fecha' in col_lower or 'date' in col_lower or 'día' in col_lower:
                return c
        return fallback if fallback in df.columns else df.columns[0]

    @staticmethod
    def detect_volume_column(df, exclude_cols=None):
        """
        Detecta automáticamente la columna de volumen en un DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame a analizar
            exclude_cols (list): Columnas a excluir de la búsqueda
            
        Returns:
            str or None: Nombre de la columna de volumen detectada
        """
        if exclude_cols is None:
            exclude_cols = []
            
        volume_keywords = ['llamada', 'volumen', 'total', 'recibida', 'ofrecida', 'call']
        
        for c in df.columns:
            if c in exclude_cols:
                continue
            col_lower = str(c).lower()
            if any(kw in col_lower for kw in volume_keywords):
                return c
        
        # Fallback: primera columna numérica que no esté excluida
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for c in numeric_cols:
            if c not in exclude_cols:
                return c
        
        return None

    @staticmethod
    def detect_interval_column(df):
        """
        Detecta automáticamente la columna de intervalo en un DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame a analizar
            
        Returns:
            str or None: Nombre de la columna de intervalo detectada
        """
        for c in df.columns:
            col_lower = str(c).lower()
            if 'intervalo' in col_lower or 'hora' in col_lower or 'time' in col_lower:
                return c
        return None

    @staticmethod
    def detect_time_columns(df, exclude_cols=None):
        """
        Detecta columnas que representan intervalos de tiempo (formato HH:MM).
        
        Args:
            df (pd.DataFrame): DataFrame a analizar
            exclude_cols (list): Columnas a excluir
            
        Returns:
            list: Lista de nombres de columnas de tiempo
        """
        if exclude_cols is None:
            exclude_cols = []
        
        return [col for col in df.columns if ':' in str(col) and col not in exclude_cols]

    @staticmethod
    def normalize_dataframe_for_analysis(df, date_col='Fecha'):
        """
        Normaliza un DataFrame para análisis, asegurando formatos consistentes.
        
        Args:
            df (pd.DataFrame): DataFrame a normalizar
            date_col (str): Nombre de la columna de fecha
            
        Returns:
            pd.DataFrame: DataFrame normalizado
        """
        df = df.copy()
        df.columns = [str(col).strip() for col in df.columns]
        
        # Detectar y renombrar columna de fecha
        detected_date_col = ExcelParserUtils.detect_date_column(df, date_col)
        if detected_date_col != date_col and detected_date_col in df.columns:
            df.rename(columns={detected_date_col: date_col}, inplace=True)
        
        # Convertir fecha
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
            df.dropna(subset=[date_col], inplace=True)
        
        return df

    @staticmethod
    def pivot_to_flat(df, id_cols, time_cols, value_name='Llamadas Ofrecidas'):
        """
        Convierte un DataFrame de formato pivote (ancho) a formato plano (largo).
        
        Args:
            df (pd.DataFrame): DataFrame en formato pivote
            id_cols (list): Columnas de identificación
            time_cols (list): Columnas de tiempo a derretir
            value_name (str): Nombre para la columna de valores
            
        Returns:
            pd.DataFrame: DataFrame en formato plano
        """
        return pd.melt(
            df, 
            id_vars=id_cols, 
            value_vars=time_cols, 
            var_name='Intervalo', 
            value_name=value_name
        )

    @staticmethod
    def prepare_historical_dataframe(df_raw, required_cols=None):
        """
        Prepara un DataFrame histórico para análisis, detectando formato y normalizando.
        
        Args:
            df_raw (pd.DataFrame): DataFrame sin procesar
            required_cols (list): Columnas requeridas
            
        Returns:
            pd.DataFrame: DataFrame preparado para análisis
            
        Raises:
            ValueError: Si no se puede preparar el DataFrame correctamente
        """
        if required_cols is None:
            required_cols = ['Fecha', 'Intervalo', 'Llamadas Ofrecidas']
        
        # Buscar encabezado
        df = ExcelParserUtils.find_header_and_normalize(df_raw)
        df.columns = [str(col).strip() for col in df.columns]
        
        # Detectar y renombrar columna de fecha
        fecha_col = ExcelParserUtils.detect_date_column(df)
        df.rename(columns={fecha_col: 'Fecha'}, inplace=True)
        
        # Detectar y renombrar columna de intervalo
        if 'Intervalo' not in df.columns:
            int_col = ExcelParserUtils.detect_interval_column(df)
            if int_col:
                df.rename(columns={int_col: 'Intervalo'}, inplace=True)
        
        # Detectar y renombrar columna de volumen
        if 'Llamadas Ofrecidas' not in df.columns:
            vol_col = ExcelParserUtils.detect_volume_column(df, exclude_cols=['Fecha', 'Intervalo'])
            if vol_col:
                df.rename(columns={vol_col: 'Llamadas Ofrecidas'}, inplace=True)
        
        # Si aún faltan columnas requeridas, intentar conversión de pivote
        if not all(col in df.columns for col in required_cols):
            id_cols = [col for col in df.columns if col.lower() in ['fecha', 'dia', 'día', 'semana', 'tipo']]
            time_cols = ExcelParserUtils.detect_time_columns(df, exclude_cols=id_cols)
            
            if id_cols and time_cols:
                df = ExcelParserUtils.pivot_to_flat(df, id_cols, time_cols)
            else:
                # Re-comprobamos después del intento de pivot
                if not all(col in df.columns for col in required_cols):
                    raise ValueError(
                        f"El archivo debe contener las columnas requeridas: {required_cols}. "
                        f"Columnas detectadas: {list(df.columns)}"
                    )
        
        # Limpiar datos
            # Intentar parsear fechas forzando dayfirst=True para el entorno del usuario
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True)
            # Si el parseo falló masivamente, intentar sin dayfirst
            if df['Fecha'].isna().sum() > len(df) * 0.5:
                 df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            
            df.dropna(subset=['Fecha'], inplace=True)
            
        if 'Llamadas Ofrecidas' in df.columns:
            # Limpiar posibles caracteres no numéricos (como separadores de miles extraños)
            if df['Llamadas Ofrecidas'].dtype == object:
                df['Llamadas Ofrecidas'] = df['Llamadas Ofrecidas'].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['Llamadas Ofrecidas'] = pd.to_numeric(df['Llamadas Ofrecidas'], errors='coerce').fillna(0)
            
        if 'Intervalo' in df.columns:
            df['Intervalo'] = df['Intervalo'].apply(ExcelParserUtils.format_interval)
        
        return df
