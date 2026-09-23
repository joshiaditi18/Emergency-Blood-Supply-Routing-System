from backend.app.models.entities import (
    Allocation,
    AuditLog,
    BloodInventory,
    BloodInventoryTransaction,
    BloodRequest,
    Dispatch,
    Hospital,
    HospitalConnection,
    Notification,
    Route,
    RevokedToken,
    User,
)


def register_models():
    return (
        User,
        Hospital,
        HospitalConnection,
        BloodInventory,
        BloodInventoryTransaction,
        BloodRequest,
        Allocation,
        Route,
        RevokedToken,
        Dispatch,
        AuditLog,
        Notification,
    )
