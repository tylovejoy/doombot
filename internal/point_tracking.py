import operator
from math import ceil

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


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
        
        self._top = {}
        self._min = {}
        self._points = {}

        self._setup_points()

        self.active_categories = []

        if self.ta_records:
            self.active_categories.append("ta")
            self._top["ta"] = self.ta_records[0].record
            self._min["ta"] = self._top["ta"] * 1.2
            self.compute_points_lb("ta")

        if self.mc_records:
            self.active_categories.append("mc")
            self._top["mc"] = self.mc_records[0].record
            self._min["mc"] = self._top["mc"] * 1.2
            self.compute_points_lb("mc")

        if self.hc_records:
            self.active_categories.append("hc")
            self._top["hc"] = self.hc_records[0].record
            self._min["hc"] = self._top["hc"] * 1.2
            self.compute_points_lb("hc")

        if self.bo_records:
            self.active_categories.append("bo")
            self._top["bo"] = self.bo_records[0].record
            self._min["bo"] = self._top["bo"] * 1.2
            self.compute_points_lb("bo")


        self.compute_points_missions()



    def _setup_points(self):
        cache = set()
        for category in self.records.keys():
            for record in self.records[category]:
                if record.posted_by in cache:
                    continue
                cache.add(record.posted_by)
                self._points[record.posted_by] = {}
                self._points[record.posted_by]["points"] = 0
                self._points[record.posted_by]["count"] = 0


    def compute_points_lb(self, category):
        for record in self.records[category]:
            if record.record > 0:
                points = 2500
                if record.record > self._min[category]:
                    points -= 2400
                else:
                    points -= ceil(((record.record - self._top[category]) * (2400 / (self._min[category] - self._top[category]))))
            else:
                points = 0
            self._points[record.posted_by]["points"] += points


    def compute_points_missions(self):
        for t_cat in self.active_categories:
            for record in self.records[t_cat]:
                for m_cat in ["expert", "hard", "medium", "easy"]:
                    mission_type = self.missions[m_cat][t_cat]["type"]
                    mission_target = self.missions[m_cat][t_cat]["target"]
                    if mission_type == "sub":
                        if float(record.record) < mission_target:
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


if __name__ == "__main__":
    missions = {
            "easy": {
                "ta": {"type": "sub", "target": 17},
                "mc": {"type": "sub", "target": 180},
                "hc": None,
                "bo": None,
            },
            "medium": {
                "ta": {"type": "sub", "target": 15},
                "mc": {"type": "sub", "target": 90},
                "hc": None,
                "bo": None,
            },
            "hard": {
                "ta": {"type": "sub", "target": 14},
                "mc": {"type": "sub", "target": 50},
                "hc": None,
                "bo": None,
            },
            "expert": {
                "ta": {"type": "sub", "target": 13.5},
                "mc": {"type": "sub", "target": 43},
                "hc": None,
                "bo": None,
            },
            "general": {},
        }
    records = {
        "ta": [
            dotdict({"posted_by": 1, "record": 13.41}),
            dotdict({"posted_by": 2, "record": 13.47}),
            dotdict({"posted_by": 3, "record": 13.98}),
        ],
        "mc": [
            dotdict({"posted_by": 1, "record": 43.01}),
            dotdict({"posted_by": 2, "record": 48.83}),
        ],
        "hc": [],
        "bo": [],
    }
    obj = CategoryPointTracking(missions, records)
    print(obj._points)