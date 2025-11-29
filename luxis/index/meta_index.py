from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import NoResultFound

Base = declarative_base()


class FileEntry(Base):
    __tablename__ = "file_entries"
    id = Column(Integer, primary_key=True)
    filepath = Column(String, unique=True)
    filehash = Column(String)


class MetaIndex:
    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.FileEntry = FileEntry

    def upsert(self, filepath: str, filehash: str) -> int:
        session = self.Session()
        try:
            entry = session.query(FileEntry).filter_by(filepath=filepath).one()
            entry.filehash = filehash
        except NoResultFound:
            entry = FileEntry(filepath=filepath, filehash=filehash)
            session.add(entry)
        session.commit()
        id_ = entry.id
        session.close()
        return id_

    def get(self, id_: int) -> FileEntry | None:
        session = self.Session()
        obj = session.get(FileEntry, id_)
        session.close()
        return obj

    def get_by_filepath(self, filepath: str) -> FileEntry | None:
        session = self.Session()
        entry = session.query(FileEntry).filter_by(filepath=filepath).first()
        session.close()
        return entry
