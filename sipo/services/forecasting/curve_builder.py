"""
Módulo de construcción de curvas ponderadas.
Contiene la lógica para construir curvas representativas basadas en pesos definidos.
"""

import logging

logger = logging.getLogger(__name__)


class CurveBuilder:
    """
    Construye curvas de distribución ponderadas basadas en datos históricos y pesos.
    """

    def build_weighted_curve(self, weights, day_of_week, all_weekly_data, labels):
        """
        Construye una única curva representativa basada en los pesos.
        
        Args:
            weights (dict): Diccionario con pesos por semana/fecha
            day_of_week: Índice del día (0-6) o nombre de festivo
            all_weekly_data (dict): Datos semanales con curvas intradía
            labels (list): Lista de etiquetas de tiempo
            
        Returns:
            dict: Diccionario con final_curve
            
        Raises:
            ValueError: Si no hay datos o los pesos suman cero
        """
        try:
            data_for_day = all_weekly_data.get(str(day_of_week), [])
            if not data_for_day:
                raise ValueError(f"No hay datos para '{day_of_week}'.")
                
            weighted_calls = {label: 0 for label in labels}
            total_weight = sum(float(w) for w in weights.values())
            
            if total_weight == 0:
                raise ValueError("La suma de los pesos es cero. No se puede calcular la curva.")

            for week_data in data_for_day:
                # Intentar obtener peso por 'date' (para festivos) o por 'week' (para días de semana)
                weight_val = weights.get(
                    week_data.get('date'), 
                    weights.get(str(week_data.get('week')))
                )
                if weight_val is None:
                    weight_val = 0
                
                weight = float(weight_val) / total_weight
                if weight > 0:
                    for label in labels:
                        weighted_calls[label] += week_data['intraday_raw'].get(label, 0) * weight
            
            total_weighted_calls = sum(weighted_calls.values())
            if total_weighted_calls == 0:
                final_distribution = {label: 0 for label in labels}
            else:
                final_distribution = {
                    label: (calls / total_weighted_calls) 
                    for label, calls in weighted_calls.items()
                }
            
            return {"final_curve": final_distribution}
            
        except Exception as e:
            logger.error(f"Error en build_weighted_curve: {e}")
            raise

    def combine_curves(self, curves_list, weights=None):
        """
        Combina múltiples curvas en una sola usando pesos opcionales.
        
        Args:
            curves_list (list): Lista de diccionarios de curvas
            weights (list): Lista de pesos (opcional, usa pesos iguales si no se proporciona)
            
        Returns:
            dict: Curva combinada
        """
        if not curves_list:
            return {}
        
        if weights is None:
            weights = [1.0 / len(curves_list)] * len(curves_list)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return curves_list[0] if curves_list else {}
        
        # Obtener todas las etiquetas únicas
        all_labels = set()
        for curve in curves_list:
            all_labels.update(curve.keys())
        
        combined = {label: 0 for label in all_labels}
        
        for curve, weight in zip(curves_list, weights):
            normalized_weight = weight / total_weight
            for label in all_labels:
                combined[label] += curve.get(label, 0) * normalized_weight
        
        return combined

    def normalize_curve(self, curve):
        """
        Normaliza una curva para que sume 100%.
        
        Args:
            curve (dict): Diccionario con valores de curva
            
        Returns:
            dict: Curva normalizada
        """
        total = sum(curve.values())
        if total == 0:
            return {k: 0 for k in curve}
        return {k: v / total for k, v in curve.items()}
