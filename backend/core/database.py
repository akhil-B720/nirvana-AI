import math
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True
)

# Custom SQLite functions for geodesic/spatial math when running without PostGIS
if is_sqlite:
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        # Register haversine distance function: haversine(lat1, lon1, lat2, lon2) -> kilometers
        def haversine(lat1, lon1, lat2, lon2):
            if any(v is None for v in (lat1, lon1, lat2, lon2)):
                return None
            try:
                lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = (math.sin(dlat / 2) ** 2 +
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                     math.sin(dlon / 2) ** 2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                return 6371.0 * c
            except Exception:
                return None

        dbapi_connection.create_function("haversine_km", 4, haversine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
