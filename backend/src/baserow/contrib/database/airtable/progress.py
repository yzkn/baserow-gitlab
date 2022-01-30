from math import floor


class Progress:
    def __init__(self, total):
        self.total = total
        self.progress = 0
        self.updated_events = []

    def register_updated_event(self, event):
        self.updated_events.append(event)

    def increment(self, state=None, by=1):
        self.progress += by
        percentage = floor(self.progress / self.total * 100)
        for event in self.updated_events:
            event(percentage, state)

    def add_child(self, instance, progress):
        last_percentage = 0

        def updated(percentage, state):
            nonlocal last_percentage
            nonlocal progress
            nonlocal self

            progress_percentage = floor(percentage / self.total * progress)
            diff = progress_percentage - last_percentage
            if diff > 0:
                last_percentage = progress_percentage
                self.progress += diff
                parent_percentage = floor(self.progress / self.total * 100)
                for event in self.updated_events:
                    event(parent_percentage, state)

        instance.register_updated_event(updated)
