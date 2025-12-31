import json
import math
import numpy as np

class DimensioningCalculator:
    def vba_erlang_b(self, servers, intensity):
        if servers < 0 or intensity < 0: return 0
        max_iterate = int(servers); last = 1.0; b = 1.0
        for count in range(1, max_iterate + 1):
            b = (intensity * last) / (count + (intensity * last)); last = b
        return max(0, min(b, 1))

    def vba_erlang_c(self, servers, intensity):
        if servers <= intensity: return 1.0
        b = self.vba_erlang_b(servers, intensity); denominator = (1 - (intensity / servers) * (1 - b))
        if denominator == 0: return 1.0
        return max(0, min(b / denominator, 1))

    def vba_sla(self, agents, service_time, calls_per_hour, aht):
        if agents <= 0 or aht <= 0 or calls_per_hour < 0: return 1.0 if calls_per_hour == 0 else 0.0
        traffic_rate = (calls_per_hour * aht) / 3600.0
        if traffic_rate >= agents: return 0.0
        c = self.vba_erlang_c(agents, traffic_rate); exponent = (traffic_rate - agents) * (service_time / aht)
        try: sl_queued = 1 - c * math.exp(exponent)
        except OverflowError: sl_queued = 0
        return max(0, min(sl_queued, 1))

    def _calculate_sl_capacity(self, num_agents, aht, sl_target, sl_time, interval_seconds=1800):
        if num_agents <= 0 or aht <= 0: return 0
        
        # Optimization: Use Binary Search instead of Linear Search
        # SLA is monotonic with traffic intensity.
        low = 0.0
        high = float(num_agents)
        best_traffic = 0.0
        
        # 12 iterations gives accuracy of ~0.0002 agents
        for _ in range(12):
            mid = (low + high) / 2
            if mid <= 0: break
            
            calls_equivalent = (mid * 3600) / aht
            sl = self.vba_sla(num_agents, sl_time, calls_equivalent, aht)
            
            if sl >= sl_target:
                best_traffic = mid
                low = mid # Try higher traffic
            else:
                high = mid # Too much traffic
                
        return math.floor((best_traffic * interval_seconds) / aht)

    def calculate_required_agents(self, calls, aht, sl_target, sl_time, is_nda=False):
        if calls <= 0 or aht <= 0: return 0.0
        # calls are per 30 mins, convert to hourly rate
        calls_per_hour = calls * 2
        
        # Traffic intensity (Erlangs)
        traffic = (calls_per_hour * aht) / 3600.0
        
        # If target IS NDA (Attention Level), use Linear Model
        # NDA = Capacity / Demand. So Required = Demand * Target_NDA
        if is_nda:
            # Fix: NDA target usually means we want Capacity / Demand = Target (Standard Linear)
            # OR we want to handle 77% of volume. 
            # Industry standard for linear NDA (without Erlang) is: Required = Traffic / Target_NDA
            
            # Normalizar target (si viene como 77 en lugar de 0.77)
            target = float(sl_target)
            if target > 1: target /= 100.0
            
            if target <= 0: return float(traffic)
            return float(traffic / target)
            
        # Binary search for minimum agents meeting SLA (Erlang C)
        # Lower bound: at least traffic intensity agents needed
        low = max(1, int(traffic))
        # Upper bound: Generous estimate (traffic * 3 or traffic + 50)
        high = max(int(traffic * 3), int(traffic) + 50)
        
        best_agents = high
        
        # Binary search: ~12 iterations instead of up to 2000
        for _ in range(20):
            if low > high:
                break
            mid = (low + high) // 2
            sl = self.vba_sla(mid, sl_time, calls_per_hour, aht)
            
            if sl >= sl_target:
                best_agents = mid
                high = mid - 1  # Try fewer agents
            else:
                low = mid + 1  # Need more agents
        
        return float(best_agents)

    def calculate_metrics(self, schedule_results, forecast_data=None, service_level_target=None, service_time_target=None, interval_minutes=5):
        """
        Calculates coverage, capability, SLA, etc. with higher precision.
        interval_minutes: Resolution of metrics (default 5 for maximum precision).
        """
        num_slots = int(1440 / interval_minutes)
        scaling_factor = 30.0 / interval_minutes # How many high-res slots fit in one 30-min forecast slot
        
        metrics = {
             "total_hours": 0,
             "total_agents_scheduled": len(schedule_results),
             "daily_metrics": {},
             "interval_minutes": interval_minutes
        }
        
        if service_level_target is None or service_time_target is None:
            raise ValueError("service_level_target and service_time_target are required")
        
        coverage_map = {}
        breaks_map = {}
        pvds_map = {}
        
        for agent in schedule_results:
            for date_str, shift in agent["shifts"].items():
                if shift["type"] == "WORK":
                    metrics["total_hours"] += shift["duration_minutes"] / 60.0
                    if date_str not in coverage_map:
                        coverage_map[date_str] = [0.0] * num_slots
                        breaks_map[date_str] = [0.0] * num_slots
                        pvds_map[date_str] = [0.0] * num_slots
                    
                    start_min = shift["start_min"]
                    end_min = shift["end_min"]
                    
                    # Initial coverage
                    for i in range(num_slots):
                        slot_start = i * interval_minutes
                        slot_end = (i + 1) * interval_minutes
                        overlap = max(0, min(end_min, slot_end) - max(start_min, slot_start))
                        if overlap > 0:
                            coverage_map[date_str][i] += (overlap / float(interval_minutes))
                            
                    # Subtract activities (breaks, PVDs)
                    for act in shift.get("activities", []):
                        a_start = act["start"]
                        a_end = act["end"]
                        a_type = act["type"]
                        
                        for i in range(num_slots):
                            slot_start = i * interval_minutes
                            slot_end = (i + 1) * interval_minutes
                            overlap = max(0, min(a_end, slot_end) - max(a_start, slot_start))
                            if overlap > 0:
                                val = (overlap / float(interval_minutes))
                                coverage_map[date_str][i] -= val
                                if a_type == "BREAK":
                                    breaks_map[date_str][i] += val
                                elif a_type == "PVD":
                                    pvds_map[date_str][i] += val

        # Final pass for KPI integration
        for date_str, agents_in_slot in coverage_map.items():
            day_forecast = forecast_data.get(date_str) or {}
            
            day_metrics = []
            susceptible_slots = []
            
            day_breaks = breaks_map[date_str]
            day_pvds = pvds_map[date_str]

            for i in range(num_slots):
                # Map high-res slot back to 30-min forecast slot
                forecast_idx = int(i * interval_minutes / 30)
                fc_val = day_forecast.get(forecast_idx) or day_forecast.get(str(forecast_idx)) or {'calls': 0, 'aht': 300, 'required': 0}
                
                # Demand scaling: demand in a 10-min slot is 1/3 of the 30-min demand
                calls_demand = float(fc_val.get('calls', 0)) / scaling_factor
                aht_val = float(fc_val.get('aht', 300))
                required_agents = float(fc_val.get('required', 0)) # Required agents usually doesn't scale linearly (Erlang) but for visualization it's okay to keep the same target
                
                if required_agents <= 0.1 and calls_demand > 0:
                    # Recalculate based on scaled demand
                    required_agents = self.calculate_required_agents(calls_demand * scaling_factor, aht_val, service_level_target, service_time_target)

                if aht_val <= 0: aht_val = 300
                
                n_agents = max(0, agents_in_slot[i])
                n_breaks = day_breaks[i]
                n_pvds = day_pvds[i]
                
                # SL Calculation: Use hourly rates (demand * 6 if 10min, or scaling_factor * 2)
                sl_real_pct = self.vba_sla(n_agents, service_time_target, calls_demand * (60.0/interval_minutes), aht_val) * 100.0
                
                capacity_linear = n_agents * (interval_minutes * 60.0 / aht_val)
                attainable_volume = min(capacity_linear, calls_demand) if calls_demand > 0 else 0
                nda_pct = (attainable_volume / calls_demand * 100) if calls_demand > 0 else 100.0
                
                susceptible = sl_real_pct < (service_level_target * 100 * 0.5) 
                if susceptible: susceptible_slots.append(i)
                
                day_metrics.append({
                    "slot": i,
                    "agents": round(n_agents, 3),
                    "breaks": round(n_breaks, 3),
                    "pvds": round(n_pvds, 3),
                    "required": required_agents,
                    "demand": round(calls_demand, 3),
                    "attainable": round(attainable_volume, 3),
                    "coverage_pct": sl_real_pct, 
                    "nda_pct": nda_pct,
                    "susceptible": susceptible
                })
                
            metrics["daily_metrics"][date_str] = {
                "slots": day_metrics,
                "susceptible_slots": susceptible_slots
            }
            
        metrics["coverage"] = coverage_map
        return metrics

