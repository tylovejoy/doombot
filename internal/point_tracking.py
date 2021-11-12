import logging
import operator
from math import ceil
logger = logging.getLogger(__name__)
from internal.constants_bot_prod import BONUS_ROLE_ID

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
        self.compute_points_general()

    def _setup_points(self):
        cache = set()
        for category in self.records.keys():
            for record in self.records[category]:
                if record.posted_by in cache:
                    continue
                cache.add(record.posted_by)
                self._points[record.posted_by] = {}
                self._points[record.posted_by]["points"] = {
                    "ta": 0,
                    "mc": 0,
                    "hc": 0,
                    "bo": 0,
                    "ta_missions": 0,
                    "mc_missions": 0,
                    "hc_missions": 0,
                    "bo_missions": 0,
                    "general": 0,
                }
                
                self._points[record.posted_by]["count"] = {
                    "ta": {
                        "easy": 0,
                        "medium": 0,
                        "hard": 0,
                        "expert": 0,
                    },
                    "mc": {
                        "easy": 0,
                        "medium": 0,
                        "hard": 0,
                        "expert": 0,
                    },
                    "hc": {
                        "easy": 0,
                        "medium": 0,
                        "hard": 0,
                        "expert": 0,
                    },
                    "bo": {
                        "easy": 0,
                        "medium": 0,
                        "hard": 0,
                        "expert": 0,
                    },
                    "general": 0,
                }

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
            self._points[record.posted_by]["points"][category] = points

    def compute_points_missions(self):
        for t_cat in self.active_categories:
            for record in self.records[t_cat]:
                for m_cat in ["expert", "hard", "medium", "easy"]:
                    mission_type = self.missions[m_cat][t_cat]["type"]
                    mission_target = self.missions[m_cat][t_cat]["target"]
                    mission_points = {
                                "expert": 2000,
                                "hard": 1500,
                                "medium": 1000,
                                "easy": 500,
                            }
                    if mission_type == "sub":
                        if float(record.record) < float(mission_target):
                            self._points[record.posted_by]["count"][t_cat][m_cat] += 1
                            self._points[record.posted_by]["points"][t_cat + "_missions"] = mission_points[m_cat]
                            break
                    elif mission_type == "complete":
                        if record:
                            self._points[record.posted_by]["count"][t_cat][m_cat] += 1
                            self._points[record.posted_by]["points"][t_cat + "_missions"] = mission_points[m_cat]
                            break

    def compute_points_general(self):
        general = self.missions["general"]

        if general["type"] == "xp":
            target = general["target"]

            for user_id in self._points:
                total = 0
                total += self._points[user_id]["points"]["ta"]
                total += self._points[user_id]["points"]["mc"]
                total += self._points[user_id]["points"]["hc"]
                total += self._points[user_id]["points"]["bo"]
                if total >= target:
                    self._points[user_id]["points"]["general"] += 2000

        elif general["type"] == "top":
            target = general["target"]
            ta = self.ta_records[:3]
            mc = self.mc_records[:3]
            hc = self.hc_records[:3]
            bo = self.bo_records[:3]
            for user_id in self._points:
                total = 0
                for record in ta:
                    if user_id == record.posted_by:
                        total += 1
                for record in mc:
                    if user_id == record.posted_by:
                        total += 1
                for record in hc:
                    if user_id == record.posted_by:
                        total += 1
                for record in bo:
                    if user_id == record.posted_by:
                        total += 1
                if total >= target:
                    self._points[user_id]["points"]["general"] += 2000

        elif general["type"] == "missions":
            target = general["target"].split(" ")
            logger.info(target)
            logger.info(target[0])
            logger.info(target[1])
            target_cat = target[1]
            target = int(target[0])

            total = 0
            for user_id in self._points:
                total += self._points[user_id]["count"]["ta"][target_cat]
                total += self._points[user_id]["count"]["mc"][target_cat]
                total += self._points[user_id]["count"]["hc"][target_cat]
                total += self._points[user_id]["count"]["bo"][target_cat]
                if total >= target:
                    self._points[user_id]["points"]["general"] += 2000
