from app.db.database import engine, Base
from app.db.models import CollectionJob, HistoricalTrainRun

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
