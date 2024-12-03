from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import Boolean, create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Remix 실행 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 데이터베이스 설정
DATABASE_URL = "sqlite:///./contacts.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 데이터베이스 모델
class ContactDB(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, index=True)
    avatar = Column(String, nullable=False)
    first = Column(String, nullable=False)
    last = Column(String, nullable=False)
    twitter = Column(String, nullable=True)
    favorite = Column(Boolean, nullable=True)


class Contact(BaseModel):
    id : str
    avatar : str| None = None
    first : str| None = None
    last : str| None = None
    twitter : str | None = None
    favorite : bool | None = None

    class Config:
        orm_mode = True


class ContactCreate(BaseModel):
    avatar: Optional[str] = None
    first: Optional[str] = None
    last: Optional[str] = None
    twitter: Optional[str] = None
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/contacts", response_model=List[Contact])
def read_contacts(db: Session = Depends(get_db)):
    contacts = db.query(ContactDB).all()
    return contacts


# 2. Create - 새 연락처 생성
@app.post("/contacts", response_model=Contact)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = ContactDB(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

# 3. Read - 특정 연락처 조회
@app.get("/contacts/{contact_id}", response_model=Contact)
def read_contact(contact_id: str, db: Session = Depends(get_db)):
    contact = db.query(ContactDB).filter(ContactDB.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

# 4. Update - 연락처 수정
@app.put("/contacts/{contact_id}", response_model=Contact)
def update_contact(contact_id: str, contact: ContactCreate, db: Session = Depends(get_db)):

    db_contact = db.query(ContactDB).filter(ContactDB.id == contact_id).first()

    if not db_contact:

        new_contact =  ContactDB(id=contact_id, **contact.model_dump())

        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        return new_contact

    for key, value in contact.model_dump().items():
        setattr(db_contact, key, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact

# 5. Delete - 연락처 삭제
@app.delete("/contacts/{contact_id}", response_model=Contact)
def delete_contact(contact_id: str, db: Session = Depends(get_db)):
    db_contact = db.query(ContactDB).filter(ContactDB.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(db_contact)
    db.commit()
    return db_contact