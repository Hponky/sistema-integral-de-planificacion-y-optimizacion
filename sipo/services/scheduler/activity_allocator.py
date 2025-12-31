
import random
import datetime

DISABLE_BREAKS_PVDS = False  # Enabled break and PVD generation

class ActivityAllocator:
    def allocate_activities(self, schedule_results):
        """
        Post-processes the scheduled shifts to insert Breaks and PVDs.
        Modifies schedule_results in place.
        """
        for agent_res in schedule_results:
            shifts = agent_res["shifts"]
            for date_str, shift_data in shifts.items():
                if shift_data["type"] != "WORK":
                    shift_data["activities"] = []
                    shift_data["breaks_list"] = []
                    shift_data["pvds_list"] = []
                    continue
                
                # If activities already exist (manual or from previous run), 
                # we keep them unless shift window changed or they are empty.
                # However, recalculate logic usually wants fresh ones UNLESS they are marked manual.
                if shift_data.get("activities") and shift_data.get("manual_activities"):
                    # We MUST update startStr/endStr just in case or assume they are correct
                    # But if manual, we skip auto-generation.
                    continue

                duration_min = shift_data["duration_minutes"]
                duration_h = duration_min / 60.0
                start_min = shift_data["start_min"]
                end_min = shift_data["end_min"]
                
                duracion_redondeada = round(duration_h)
                activities = []
                
                # 1. Break
                break_dur = self._calculate_breaks(duracion_redondeada)
                break_activity = None
                
                if break_dur > 0:
                    ventana_min = start_min + 120
                    ventana_max = min(start_min + 270, end_min - 60)
                    if ventana_max > ventana_min:
                        target_start = random.randint(ventana_min, ventana_max - break_dur)
                        target_start = (target_start // 5) * 5
                        break_activity = {
                            "type": "BREAK",
                            "start": target_start,
                            "end": target_start + break_dur,
                            "duration": break_dur,
                            "startStr": f"{target_start // 60:02d}:{target_start % 60:02d}",
                            "endStr": f"{(target_start + break_dur) // 60:02d}:{(target_start + break_dur) % 60:02d}"
                        }
                        activities.append(break_activity)
                
                # 2. PVDs
                num_pvds = duracion_redondeada
                pvd_dur = 5 
                curr_pvd_start = start_min + random.randint(45, 65)
                for _ in range(num_pvds):
                    if len([a for a in activities if a["type"] == "PVD"]) >= 10: break
                    pvd_start_floored = (curr_pvd_start // 5) * 5
                    pvd_end = pvd_start_floored + pvd_dur
                    if break_activity and max(pvd_start_floored, break_activity["start"]) < min(pvd_end, break_activity["end"]):
                        pvd_start_floored = break_activity["end"] + 10
                        pvd_end = pvd_start_floored + pvd_dur
                    if pvd_end < end_min:
                        activities.append({
                            "type": "PVD",
                            "start": pvd_start_floored,
                            "end": pvd_end,
                            "duration": pvd_dur,
                            "startStr": f"{pvd_start_floored // 60:02d}:{pvd_start_floored % 60:02d}",
                            "endStr": f"{pvd_end // 60:02d}:{pvd_end % 60:02d}"
                        })
                    curr_pvd_start = pvd_start_floored + random.randint(50, 65)
                
                activities.sort(key=lambda x: x["start"])
                shift_data["activities"] = activities
                shift_data["breaks_list"] = [a for a in activities if a["type"] == "BREAK"]
                shift_data["pvds_list"] = [a for a in activities if a["type"] == "PVD"]
                shift_data["formatted_activities"] = self._format_activities(activities)
        
        return schedule_results

    def _calculate_breaks(self, duracion_redondeada):
        if 4 <= duracion_redondeada <= 5: return 10
        elif 6 <= duracion_redondeada <= 8: return 20
        elif 9 <= duracion_redondeada <= 10: return 30
        return 0

    def _format_activities(self, activities):
        res = []
        for act in activities:
            res.append(f"{act['type']} ({act['startStr']}-{act['endStr']})")
        return "; ".join(res)
