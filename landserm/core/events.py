class Event:
    def __init__(self, domain, kind, subject, payload):
        self.domain = domain
        self.kind = kind
        self.subject = subject
        self.payload = payload
