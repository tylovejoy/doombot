class PointTracking:

    def __init__(self, records):
        """Accepts a specific category of records."""
        self.records = records
        self._top = records[0].record
        self._min = self._top * 1.2
        self._points = {}

    def compute_points(self):
        for record in self.records:
            if record.record > 0:
                points = 2500
                if record.record > self._min:
                    points -= 2400
                else:
                    points -= ((record.record - self._top) * (2400 / (self._min - self._top)))
            else:
                points = 0

            self._points[record.posted_by] = points

