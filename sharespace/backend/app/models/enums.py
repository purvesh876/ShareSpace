from enum import StrEnum


class MembershipRole(StrEnum):
    ADMIN = "admin"
    LAB_MANAGER = "lab_manager"
    TECHNICIAN = "technician"
    RESEARCHER = "researcher"
    STUDENT = "student"
    AUDITOR = "auditor"


class ResourceCategory(StrEnum):
    LAB_INSTRUMENT = "lab_instrument"
    WORKSHOP_TOOL = "workshop_tool"
    TESTING_FACILITY = "testing_facility"
    COMPUTING_CLUSTER = "computing_cluster"
    GENERAL_SPACE = "general_space"


class BookingStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_USE = "in_use"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PermitStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"


class QualificationStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
