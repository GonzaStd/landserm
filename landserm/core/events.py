class Event:
    def __init__(self, domain, kind, subject, payload, severity):
        self.domain = domain
        self.kind = kind
        self.subject = subject
        self.payload = payload
        self.severity = severity

    def getBasicData(self):
        basic_data = {
            "domain": self.domain,
            "kind": self.kind,
            "subject": self.subject,
            "payload": self.payload,
            "severity": self.severity
        }
        return basic_data
