"""
Seed institutional resources for Apex Institute of Technology.
Non-destructive: checks if resources exist first; does not duplicate records.
"""
import asyncio
from datetime import datetime, timezone
import sys
import uuid

from sqlalchemy import select

from app.db.session import async_sessionmaker, get_async_engine, AsyncSession
from app.models.enums import ResourceCategory
from app.models.organization import Organization
from app.models.resource import Resource


SAMPLE_RESOURCES = [
    {
        "name": "Titan Krios G4 Cryo-TEM",
        "slug": "titan-krios-cryo-tem",
        "category": ResourceCategory.LAB_INSTRUMENT.value,
        "location": "Hall of Sciences, Room B12",
        "description": "State-of-the-art 300 kV cryogenic transmission electron microscope engineered for high-resolution single-particle analysis and cryo-electron tomography.",
        "requires_approval": True,
        "requires_permit": True,
        "requires_qualification": True,
        "hourly_rate_credits": 50,
        "specifications_json": {
            "acceleration_voltage": "300 kV",
            "detector": "Falcon 4i Direct Electron Detector",
            "autoloader": "12 cassettes with automated cryo-transfer",
            "energy_filter": "Selectris X imaging filter",
        },
    },
    {
        "name": "Haas VF-2SS 5-Axis CNC Machining Center",
        "slug": "haas-vf2ss-5axis-cnc",
        "category": ResourceCategory.WORKSHOP_TOOL.value,
        "location": "Central Fabrication Facility, Bay 4",
        "description": "High-speed 5-axis vertical machining center equipped for rapid prototyping, aerospace-grade alloy milling, and precision micro-machining.",
        "requires_approval": False,
        "requires_permit": True,
        "requires_qualification": True,
        "hourly_rate_credits": 30,
        "specifications_json": {
            "spindle_speed": "12,000 RPM",
            "travel_x_y_z": "762 x 406 x 508 mm",
            "tool_changer": "30+1 side-mount",
            "control": "Next-Gen CNC with rigid tapping",
        },
    },
    {
        "name": "NVIDIA DGX H100 Supercomputing Node",
        "slug": "nvidia-dgx-h100-node",
        "category": ResourceCategory.COMPUTING_CLUSTER.value,
        "location": "Enterprise Data Center, Rack 14A",
        "description": "Dedicated multi-GPU AI cluster node designed for training large multimodal foundation models, molecular dynamics, and fluid simulations.",
        "requires_approval": False,
        "requires_permit": False,
        "requires_qualification": False,
        "hourly_rate_credits": 40,
        "specifications_json": {
            "gpus": "8x NVIDIA H100 SXM5 80GB (640GB VRAM)",
            "system_ram": "2TB DDR5",
            "interconnect": "3.2 Tbps Quantum-2 InfiniBand",
            "storage": "30TB NVMe scratch array",
        },
    },
    {
        "name": "Class 100 ISO 5 Photolithography Bench",
        "slug": "iso5-photolithography-bench",
        "category": ResourceCategory.TESTING_FACILITY.value,
        "location": "Nanofabrication Cleanroom, Zone 2",
        "description": "Yellow-room optical lithography workstation with programmable resist spinner, hotplate arrays, and UV contact mask aligner for microfluidics and MEMS.",
        "requires_approval": True,
        "requires_permit": True,
        "requires_qualification": True,
        "hourly_rate_credits": 45,
        "specifications_json": {
            "cleanliness_class": "ISO Class 5 (Class 100 laminar flow)",
            "mask_aligner": "Suss MicroTec MA6 (sub-micron resolution)",
            "spin_coater": "Laurell WS-650 with programmable ramps",
        },
    },
    {
        "name": "Agilent 1290 Infinity II UHPLC-MS System",
        "slug": "agilent-1290-uhplc-ms",
        "category": ResourceCategory.LAB_INSTRUMENT.value,
        "location": "Chemical Engineering Complex, Lab 304",
        "description": "Ultra-high performance liquid chromatography coupled to high-resolution quadrupole time-of-flight mass spectrometer for proteomics and metabolomics.",
        "requires_approval": True,
        "requires_permit": False,
        "requires_qualification": True,
        "hourly_rate_credits": 25,
        "specifications_json": {
            "pressure_rating": "Up to 1300 bar",
            "flow_range": "0.05 to 5.0 mL/min",
            "autosampler_capacity": "Dual needle, 432 sample vials",
            "detector": "Triple Quadrupole MS/MS",
        },
    },
]


async def seed():
    engine = get_async_engine()
    if not engine:
        print("Error: Database connection not configured.", file=sys.stderr)
        return

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Find Apex Institute
        org_stmt = select(Organization).where(Organization.slug == "apex-institute")
        org_res = await session.execute(org_stmt)
        org = org_res.scalars().first()

        if not org:
            print("Error: Apex Institute not found in database.", file=sys.stderr)
            return

        org_name = org.name
        org_slug = org.slug
        now = datetime.now(timezone.utc)
        created_count = 0

        for r_data in SAMPLE_RESOURCES:
            existing_stmt = select(Resource).where(
                Resource.organization_id == org.id,
                Resource.slug == r_data["slug"],
            )
            existing_res = await session.execute(existing_stmt)
            if existing_res.scalars().first():
                continue

            res = Resource(
                id=uuid.uuid4(),
                organization_id=org.id,
                name=r_data["name"],
                slug=r_data["slug"],
                category=r_data["category"],
                location=r_data["location"],
                description=r_data["description"],
                is_available=True,
                requires_approval=r_data["requires_approval"],
                requires_permit=r_data["requires_permit"],
                requires_qualification=r_data["requires_qualification"],
                hourly_rate_credits=r_data["hourly_rate_credits"],
                specifications_json=r_data["specifications_json"],
                created_at=now,
                updated_at=now,
            )
            session.add(res)
            created_count += 1

        await session.commit()
        print(f"Success: Seeded {created_count} real institutional resources in '{org_name}' ({org_slug}).")


if __name__ == "__main__":
    asyncio.run(seed())

