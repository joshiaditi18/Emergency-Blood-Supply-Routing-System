import os

from argon2 import PasswordHasher

from backend.app import db
from backend.app.models import (
    BloodInventory,
    Hospital,
    HospitalConnection,
    User,
)


BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")


def seed_demo_data():
    if Hospital.query.first():
        return

    demo_password = os.getenv("DEMO_ADMIN_PASSWORD")
    if not demo_password:
        raise RuntimeError("Set DEMO_ADMIN_PASSWORD before seeding demo users")

    password_hash = PasswordHasher().hash(demo_password)
    db.session.add(User(
        email="admin@demo.blood",
        password_hash=password_hash,
        role="ADMIN",
        full_name="Demo Administrator",
    ))

    hospitals = []
    for index in range(1, 11):
        hospital = Hospital(
            code=f"H{index}",
            name=f"Demo Regional Hospital {index}",
            latitude=28.60 + index * 0.025,
            longitude=77.20 + index * 0.02,
            address=f"{index} Civic Health Avenue",
        )
        hospitals.append(hospital)
        db.session.add(hospital)

    db.session.flush()

    for index, hospital in enumerate(hospitals):
        for blood_group in BLOOD_GROUPS:
            units = 6 + ((index * 3 + len(blood_group)) % 15)
            db.session.add(BloodInventory(
                hospital_id=hospital.id,
                blood_group=blood_group,
                units_available=units,
            ))

    for index in range(len(hospitals) - 1):
        db.session.add(HospitalConnection(
            source_hospital_id=hospitals[index].id,
            destination_hospital_id=hospitals[index + 1].id,
            distance_km=4 + index,
            estimated_minutes=8 + index * 2,
        ))
        db.session.add(HospitalConnection(
            source_hospital_id=hospitals[index + 1].id,
            destination_hospital_id=hospitals[index].id,
            distance_km=4 + index,
            estimated_minutes=8 + index * 2,
        ))
