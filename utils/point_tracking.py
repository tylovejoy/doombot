import operator

from internal.constants_bot_prod import HC_CHAMP

class CategoryPointTracking:

    def __init__(self, missions, records):
        self.missions = missions

        self.ta_records = sorted(records["ta"], key=operator.itemgetter("record"))
        self.mc_records = sorted(records["mc"], key=operator.itemgetter("record"))
        self.hc_records = sorted(records["hc"], key=operator.itemgetter("record"))
        self.bo_records = sorted(records["bo"], key=operator.itemgetter("record"))

        self.records = {
            "ta": self.ta_records,
            "mc": self.mc_records,
            "hc": self.hc_records,
            "bo": self.bo_records,
        }

        self._top = {
            "ta": self.ta_records[0].record,
            "mc": self.mc_records[0].record,
            "hc": self.hc_records[0].record,
            "bo": self.bo_records[0].record,
        }

        self._min = {
            "ta": self._top["ta"] * 1.2,
            "mc": self._top["mc"] * 1.2,
            "hc": self._top["hc"] * 1.2,
            "bo": self._top["bo"] * 1.2,
        }
        self._points = {}
        self._setup_points()
        self.compute_points_lb()
        self.compute_points_missions()



    def _setup_points(self):
        cache = set()
        for category in self.records.keys():
            for record in self.records[category]:
                if record.posted_by in cache:
                    continue
                cache.add(record.posted_by)
                self._points[record.posted_by]["points"] = 0
                self._points[record.posted_by]["count"] = 0


    def compute_points_lb(self, category):
        for record in self.records[category]:
            if record.record > 0:
                points = 2500
                if record.record > self._min:
                    points -= 2400
                else:
                    points -= ((record.record - self._top) * (2400 / (self._min - self._top)))
            else:
                points = 0
            self._points[record.posted_by]["points"] += points


    def compute_points_missions(self):
        for t_cat in ["ta", "mc", "hc", "bo"]:
            for records in self.records.keys():
                for record in records:
                    for m_cat in ["expert", "hard", "medium", "easy"]:
                        mission_type = self.missions[m_cat][t_cat]["type"]
                        mission_target = self.missions[m_cat][t_cat]["target"]
                        if mission_type == "sub":
                            if record < mission_target:
                                self._points[record.posted_by]["count"] += 1
                                mission_points = {
                                    "expert": 2000,
                                    "hard": 1500,
                                    "medium": 1000,
                                    "easy": 500,
                                }
                                self._points[record.posted_by]["points"] += mission_points[m_cat]
                                break
                


    def compute_points_general(self):
        pass

    def send_to_db(self):
        pass