class Event:
    def __init__(self, domain, kind, subject, systemdInfo):
        self.domain = domain
        self.kind = kind
        self.subject = subject
        self.systemdInfo = systemdInfo
