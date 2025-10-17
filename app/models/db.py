from sqlalchemy import create_engine, String, Integer, JSON, Column, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Dict, Any, List

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(100))
    bio: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(100))


    resumes: Mapped[List['Resume']] = relationship(back_populates='user', lazy='dynamic')
    job_descriptions: Mapped[List['JobDescription']] = relationship(back_populates='user', lazy='dynamic')

    updated_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    
    

    def set_password(self, password):
        self.password = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password, password)
    

class Resume(Base):
    __tablename__ = 'resumes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    serial_number: Mapped[int] = mapped_column(Integer) 
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_text: Mapped[str] = mapped_column(String(5000), nullable=True)
    template: Mapped[int] = mapped_column(Integer, nullable=False)
    parsed_resume: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    user: Mapped['User'] = relationship('User', back_populates='resumes')
    
    updated_at: Mapped[str] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)


class JobDescription(Base):
    __tablename__ = 'job_descriptions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    serial_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    user: Mapped['User'] = relationship('User', back_populates='job_descriptions')

    created_at: Mapped[str] = mapped_column(DateTime, nullable=False)


