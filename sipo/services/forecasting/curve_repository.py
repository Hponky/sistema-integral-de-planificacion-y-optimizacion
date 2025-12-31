"""
Módulo de repositorio de curvas de forecasting.
Contiene la lógica de persistencia para curvas en la base de datos.
"""

import datetime
import json
import logging

logger = logging.getLogger(__name__)


class CurveRepository:
    """
    Gestiona la persistencia de curvas de forecasting en la base de datos.
    """

    def save_curves(self, segment_id, name, curves_by_day, time_labels, 
                   user_info=None, weeks_analyzed=None, date_range=None):
        """
        Guarda las curvas de forecasting intradía en la base de datos.
        
        Args:
            segment_id: ID del segmento
            name: Nombre descriptivo del forecast
            curves_by_day: Diccionario con curvas por día
            time_labels: Lista de etiquetas de tiempo
            user_info: Información del usuario
            weeks_analyzed: Número de semanas analizadas
            date_range: Rango de fechas analizadas
        
        Returns:
            int: ID del registro creado
        """
        try:
            from models import db, ForecastingCurve
            
            # Verificar si ya existe una curva con el mismo nombre
            existing = ForecastingCurve.query.filter_by(
                segment_id=segment_id,
                name=name
            ).first()
            
            if existing:
                forecast_curve = existing
            else:
                forecast_curve = ForecastingCurve(
                    segment_id=segment_id,
                    name=name,
                    id_legal=user_info.get('idLegal') or user_info.get('id_legal') if user_info else None,
                    username=user_info.get('username') if user_info else None
                )
            
            # Guardar curvas para cada día
            for day_index in range(7):
                curve_data = curves_by_day.get(str(day_index), curves_by_day.get(day_index, {}))
                if curve_data:
                    forecast_curve.set_curve_for_day(day_index, curve_data)
            
            # Guardar metadatos
            forecast_curve.time_labels = json.dumps(time_labels)
            forecast_curve.weeks_analyzed = weeks_analyzed
            forecast_curve.analysis_date_range = date_range
            forecast_curve.created_at = datetime.datetime.utcnow()
            
            if not existing:
                db.session.add(forecast_curve)
            
            db.session.commit()
            logger.info(f"Curvas de forecasting guardadas: ID={forecast_curve.id}, Nombre={name}")
            return forecast_curve.id
            
        except Exception as e:
            logger.error(f"Error guardando curvas de forecasting: {e}")
            from models import db
            db.session.rollback()
            raise

    def get_by_segment(self, segment_id):
        """
        Obtiene todas las curvas de forecasting para un segmento.
        
        Args:
            segment_id: ID del segmento
        
        Returns:
            list: Lista de diccionarios con información de las curvas
        """
        try:
            from models import ForecastingCurve
            
            curves = ForecastingCurve.query.filter_by(segment_id=segment_id).order_by(
                ForecastingCurve.created_at.desc()
            ).all()
            
            return [curve.to_dict() for curve in curves]
            
        except Exception as e:
            logger.error(f"Error obteniendo curvas de forecasting: {e}")
            raise

    def get_by_id(self, curve_id):
        """
        Obtiene una curva de forecasting específica por ID.
        
        Args:
            curve_id: ID de la curva
        
        Returns:
            dict: Diccionario con información de la curva
        """
        try:
            from models import ForecastingCurve
            
            curve = ForecastingCurve.query.get(curve_id)
            if not curve:
                raise ValueError(f"No se encontró la curva con ID {curve_id}")
            
            return curve.to_dict()
            
        except Exception as e:
            logger.error(f"Error obteniendo curva de forecasting: {e}")
            raise

    def delete(self, curve_id):
        """
        Elimina una curva de forecasting.
        
        Args:
            curve_id: ID de la curva
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            from models import db, ForecastingCurve
            
            curve = ForecastingCurve.query.get(curve_id)
            if not curve:
                raise ValueError(f"No se encontró la curva con ID {curve_id}")
            
            # Si hay distribuciones vinculadas a esta curva, también las eliminamos
            from models import ForecastedDistribution
            linked_dists = ForecastedDistribution.query.filter_by(curve_id=curve_id).all()
            for d in linked_dists:
                db.session.delete(d)
                logger.info(f"Distribución vinculada eliminada: ID={d.id} por eliminación de curva {curve_id}")

            db.session.delete(curve)
            db.session.commit()
            logger.info(f"Curva de forecasting eliminada: ID={curve_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando curva de forecasting: {e}")
            from models import db
            db.session.rollback()
            raise

    def delete_distribution(self, dist_id):
        """
        Elimina una distribución de forecasting (ForecastedDistribution).
        """
        try:
            from models import db, ForecastedDistribution
            
            dist = ForecastedDistribution.query.get(dist_id)
            if not dist:
                raise ValueError(f"No se encontró la distribución con ID {dist_id}")
            
            # Si tiene una curva vinculada, también la eliminamos para que actúen como un único registro
            if dist.curve_id:
                from models import ForecastingCurve
                curve = ForecastingCurve.query.get(dist.curve_id)
                if curve:
                    db.session.delete(curve)
                    logger.info(f"Curva vinculada eliminada: ID={dist.curve_id}")

            db.session.delete(dist)
            db.session.commit()
            logger.info(f"Distribución eliminada: ID={dist_id}")
            return True
            
        except Exception as e:
             logger.error(f"Error eliminando distribución: {e}")
             from models import db
             db.session.rollback()
             raise
            
        except Exception as e:
            logger.error(f"Error eliminando curva de forecasting: {e}")
            from models import db
            db.session.rollback()
            raise

    def save_scenario(self, segment_id, name, timeframe_data, user_info=None):
        """
        Guarda el escenario de forecast en la base de datos (DimensioningScenario).
        
        Args:
            segment_id: ID del segmento
            name: Nombre del escenario
            timeframe_data: Datos del forecast
            user_info: Información del usuario
            
        Returns:
            int: ID del escenario creado
        """
        try:
            from models import db, DimensioningScenario
            import json
            
            forecast_json = json.dumps(timeframe_data)
            
            scenario = DimensioningScenario(
                segment_id=segment_id,
                parameters=json.dumps({"name": name, "type": "forecast_import"}),
                agents_online=forecast_json, 
                id_legal=user_info.get('id_legal') if user_info else None,
                username=user_info.get('username') if user_info else None,
                created_at=datetime.datetime.utcnow()
            )
            
            db.session.add(scenario)
            db.session.commit()
            return scenario.id
            
        except Exception as e:
            logger.error(f"Error guardando escenario: {e}")
            from models import db
            db.session.rollback()
            raise

    def save_distribution(self, segment_id, start_date, end_date, output_rows, time_labels, user_info=None, curve_id=None):
        """
        Guarda el resultado de la distribución forecasting (llamadas esperadas).
        """
        try:
            from models import db, ForecastedDistribution
            import datetime
            import json

            # Convertir output_rows a un formato almacenables eficiente (JSON {date: {time: vol}})
            # output_rows es una lista de dicts con 'Fecha', 'Dia', etc. y luego columas de tiempo.
            dist_map = {}
            for row in output_rows:
                date_str = None
                # Intentar obtener string de fecha
                raw_date = row.get('Fecha')
                if hasattr(raw_date, 'strftime'):
                    date_str = raw_date.strftime('%Y-%m-%d')
                else:
                    s_date = str(raw_date).split(' ')[0]
                    # Intentar estandarizar a YYYY-MM-DD
                    try:
                        # Frontend envía DD/MM/YYYY
                        if '/' in s_date:
                            day, month, year = s_date.split('/')
                            # Asumir formato día/mes/año
                            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        else:
                            # Asumir ya está en formato correcto o ISO
                            date_str = s_date
                    except Exception:
                        date_str = s_date
                
                if not date_str: continue
                
                # Columnas de metadata (no son tiempo y no son Fecha)
                metadata_cols = [c for c in row.keys() if c not in time_labels and c != 'Fecha']

                # Extraer volúmenes y metadata
                row_data = {t: float(row.get(t, 0)) for t in time_labels}
                for mc in metadata_cols:
                    val = row.get(mc)
                    if hasattr(val, 'isoformat'):
                        val = val.isoformat()
                    row_data[mc] = val
                
                dist_map[date_str] = row_data
            
            # --- DEBUG: Verificación de guardado ---
            sample_dates = list(dist_map.keys())[:3]
            print(f"[DEBUG REPO] Guardando {len(dist_map)} fechas en DB.", flush=True)
            print(f"[DEBUG REPO] Muestra de fechas en DB: {sample_dates}", flush=True)
            if sample_dates and time_labels:
                first_t = time_labels[0]
                print(f"[DEBUG REPO] Valores para {first_t} en DB (muestra): {[dist_map[d].get(first_t) for d in sample_dates]}", flush=True)
            # --------------------------------------
            
            # Buscar si ya existe para este usuario y fechas para sobreescribir (o crear nuevo)
            # Para simplificar y mantener historial, creamos uno nuevo siempre (o podríamos limpiar antiguos)
            
            from models import Segment
            segment = Segment.query.get(segment_id)
            campaign_code = segment.campaign.code if segment and segment.campaign else None

            dist = ForecastedDistribution(
                segment_id=segment_id,
                start_date=start_date,
                end_date=end_date,
                distribution_data=json.dumps(dist_map),
                time_labels=json.dumps(time_labels),
                id_legal=user_info.get('idLegal') or user_info.get('id_legal') if user_info else None,
                username=user_info.get('username') if user_info else None,
                curve_id=curve_id,
                campaign_code=campaign_code,
                created_at=datetime.datetime.utcnow()
            )
            
            db.session.add(dist)
            db.session.commit()
            logger.info(f"Distribución guardada: ID={dist.id} ({start_date} - {end_date})")
            return dist.id

        except Exception as e:
             logger.error(f"Error guardando distribución: {e}")
             from models import db
             db.session.rollback()
             # No lanzar error para no bloquear el flujo de descarga, solo loguear
             # raise e 

    def get_latest_distribution(self, segment_id, start_date, end_date, id_legal=None):
        """
        Busca la mejor distribución disponible para el segmento.
        Prioriza la marcada como activa (is_selected=True).
        """
        try:
            from models import ForecastedDistribution
            
            # Prioridad 1: Buscar la distribución seleccionada (ACTIVA) para este segmento
            # Ignoramos fechas y usuario aquí porque 'Activa' implica intención explícita
            active_dist = ForecastedDistribution.query.filter_by(
                segment_id=segment_id, 
                is_selected=True
            ).order_by(ForecastedDistribution.created_at.desc()).first()
            
            if active_dist:
                print(f"[DEBUG REPO] Encontrada ACTIVA ID={active_dist.id} para Segment={segment_id}", flush=True)
                logger.info(f"Usando distribución ACTIVA (ID: {active_dist.id}) para segmento {segment_id}")
                return active_dist
            
            # Prioridad 2: Buscar por coincidencia exacta de fechas
            print(f"[DEBUG REPO] No hay Activa. Buscando por fechas: {start_date} a {end_date} para Segment={segment_id}", flush=True)
            query = ForecastedDistribution.query.filter_by(segment_id=segment_id)
            query = query.filter(ForecastedDistribution.start_date == start_date)
            query = query.filter(ForecastedDistribution.end_date == end_date)
            
            if id_legal:
                # Intentar buscar del mismo usuario primero
                user_dist = query.filter_by(id_legal=id_legal).order_by(ForecastedDistribution.created_at.desc()).first()
                if user_dist:
                    print(f"[DEBUG REPO] Encontrada distribución por usuario y fechas: ID={user_dist.id}", flush=True)
                    return user_dist
            
            # Si no hay del mismo usuario, tomar la más reciente de ese rango
            latest = query.order_by(ForecastedDistribution.created_at.desc()).first()
            if latest:
                print(f"[DEBUG REPO] Encontrada distribución más reciente por fechas: ID={latest.id}", flush=True)
            return latest
            
        except Exception as e:
            logger.error(f"Error recuperando distribución: {e}")
            return None

    def get_distributions_by_segment(self, segment_id):
        """
        Obtiene todas las distribuciones guardadas para un segmento.
        """
        try:
            from models import ForecastedDistribution
            dists = ForecastedDistribution.query.filter_by(segment_id=segment_id).order_by(
                ForecastedDistribution.created_at.desc()
            ).all()
            
            results = []
            for d in dists:
                curve_name = None
                from models import ForecastingCurve
                if d.curve_id:
                    # Intento obtener el nombre de la curva vinculada
                    curve = ForecastingCurve.query.get(d.curve_id)
                    curve_name = curve.name if curve else None

                results.append({
                    'id': d.id,
                    'curve_id': d.curve_id,
                    'curve_name': curve_name,
                    'start_date': d.start_date.strftime('%Y-%m-%d'),
                    'end_date': d.end_date.strftime('%Y-%m-%d'),
                    'created_at': d.created_at.isoformat(),
                    'id_legal': d.id_legal,
                    'username': d.username,
                    'is_selected': d.is_selected or False
                })
            return results
        except Exception as e:
            logger.error(f"Error obteniendo distribuciones: {e}")
            raise

    def select_distribution(self, dist_id):
        """
        Marca una distribución como seleccionada y desmarca las demás del segmento.
        """
        try:
            from models import db, ForecastedDistribution
            
            target = ForecastedDistribution.query.get(dist_id)
            if not target:
                raise ValueError("Distribución no encontrada")
                
            # Si ya está seleccionada, desmarcarla (Toggle Off)
            if target.is_selected:
                target.is_selected = False
            else:
                # Desmarcar todas las del mismo segmento y marcar la actual
                ForecastedDistribution.query.filter_by(segment_id=target.segment_id).update({'is_selected': False})
                target.is_selected = True
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error seleccionando distribución: {e}")
            from models import db
            db.session.rollback()
            raise
