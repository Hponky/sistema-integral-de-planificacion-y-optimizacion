"""
Módulo de exportación a Excel para Forecasting.
Contiene la lógica para exportar curvas y distribuciones a archivos Excel.
"""

import pandas as pd
import io
import logging

logger = logging.getLogger(__name__)


class ExcelExporter:
    """
    Exporta datos de forecasting a archivos Excel con formato profesional.
    """

    def export_curve(self, final_curve, labels):
        """
        Exporta una curva individual a Excel.
        
        Args:
            final_curve (dict): Diccionario con la curva
            labels (list): Lista de etiquetas de tiempo
            
        Returns:
            BytesIO: Archivo Excel en memoria
        """
        try:
            df = pd.DataFrame([final_curve])
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Curva_Ponderada')
            output.seek(0)
            return output
        except Exception as e:
            logger.error(f"Error en export_curve_to_excel: {e}")
            raise

    def export_all_curves(self, curves_by_day, time_labels):
        """
        Exporta todas las curvas diarias a un archivo Excel.
        
        Args:
            curves_by_day (dict): Diccionario con curvas por día
            time_labels (list): Lista de etiquetas de tiempo
            
        Returns:
            BytesIO: Archivo Excel en memoria
        """
        try:
            rows = []
            day_map = {
                0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 
                3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
            }
            
            for day_idx in range(7):
                day_str = str(day_idx)
                if day_str in curves_by_day:
                    curve = curves_by_day[day_str]
                    row = {'Dia': day_map[day_idx]}
                    for label in time_labels:
                        row[label] = curve.get(label, 0)
                    rows.append(row)
            
            df = pd.DataFrame(rows)
            cols = ['Dia'] + sorted(time_labels)
            df = df[cols]
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Curvas_Semanales')
                
                workbook = writer.book
                worksheet = writer.sheets['Curvas_Semanales']
                header_format = workbook.add_format({
                    'bold': True, 
                    'bg_color': '#6366f1', 
                    'font_color': 'white', 
                    'border': 1
                })
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
            
            output.seek(0)
            return output
        except Exception as e:
            logger.error(f"Error exporting curves to excel: {e}")
            raise

    def export_intraday_distribution(self, output_rows, time_labels):
        """
        Exporta la distribución intradía a un archivo Excel.
        
        Args:
            output_rows (list): Lista de diccionarios con los datos distribuidos
            time_labels (list): Lista de etiquetas de tiempo
        
        Returns:
            BytesIO: Archivo Excel en memoria
        """
        try:
            df = pd.DataFrame(output_rows)
            
            # Reordenar columnas
            metadata_cols = ['Fecha', 'Dia', 'Semana', 'Tipo']
            existing_metadata = [col for col in metadata_cols if col in df.columns]
            time_cols = [col for col in df.columns if col in time_labels]
            
            ordered_cols = existing_metadata + sorted(time_cols)
            df = df[ordered_cols]
            
            # --- DEBUG: Comparar con Guardado ---
            if 'Fecha' in df.columns and len(df) > 0:
                print(f"[DEBUG EXPORT] Exportando {len(df)} filas.", flush=True)
                print(f"[DEBUG EXPORT] Primeras 3 fechas: {df['Fecha'].head(3).tolist()}", flush=True)
                first_t = time_labels[0] if time_labels else None
                if first_t and first_t in df.columns:
                    print(f"[DEBUG EXPORT] Valores para {first_t} (primeras 3): {df[first_t].head(3).tolist()}", flush=True)
            # ------------------------------------
            
            # Convertir Fecha a formato legible
            if 'Fecha' in df.columns:
                # Usar format='mixed' para manejar diferentes formatos (ISO, DD/MM/YYYY, etc.)
                try:
                    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, format='mixed').dt.strftime('%d/%m/%Y')
                except TypeError:
                    # Fallback para versiones de pandas que no soportan format='mixed'
                    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True).dt.strftime('%d/%m/%Y')
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Distribucion_Intraday')
                
                workbook = writer.book
                worksheet = writer.sheets['Distribucion_Intraday']
                
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#6366f1',
                    'font_color': 'white',
                    'border': 1
                })
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Ajustar ancho de columnas
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, min(max_len, 15))
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"Error exportando distribución intradía a Excel: {e}")
            raise

    def export_intramonth_distribution(self, df_result):
        """
        Exporta la distribución intrames a un archivo Excel.
        """
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_result.to_excel(writer, index=False, sheet_name='Distribucion_Diaria')
            output.seek(0)
            return output
        except Exception as e:
            logger.error(f"Error exportando distribución intrames a Excel: {e}")
            raise

    def export_expected_calls(self, df, sheet_name='Llamadas_Esperadas'):
        """
        Exporta datos de llamadas esperadas a Excel.
        
        Args:
            df (pd.DataFrame): DataFrame con datos
            sheet_name (str): Nombre de la hoja
            
        Returns:
            BytesIO: Archivo Excel en memoria
        """
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name=sheet_name)
                
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]
                
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#6366f1',
                    'font_color': 'white',
                    'border': 1
                })
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Ajustar ancho de columnas
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, min(max_len, 20))
            
            output.seek(0)
            return output
            
        except Exception as e:
            logger.error(f"Error exportando llamadas esperadas a Excel: {e}")
            raise
