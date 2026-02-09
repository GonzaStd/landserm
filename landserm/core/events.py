class Event:
    def __init__(self, domain: str, kind: str, subject: str, systemdInfo: dict = None):
        self.domain = domain
        self.kind = kind
        self.subject = subject
        self.systemdInfo = systemdInfo
