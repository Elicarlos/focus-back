from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # Nulo se usar apenas Google OAuth
    username = Column(String, unique=True, index=True, nullable=False)
    avatar_url = Column(String, nullable=True)
    country = Column(String, default="BR") # Nacionalidade do usuário para o Ranking

    # Gamificação e Estado
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    gems = Column(Integer, default=100)
    streak = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    water_units = Column(Integer, default=0)
    skill_points = Column(Integer, default=0)
    tree_health = Column(Integer, default=100)
    tree_dead = Column(Boolean, default=False)
    
    # Ingredientes de Alquimia
    mudas = Column(Integer, default=0)
    adubos = Column(Integer, default=0)
    essencias = Column(Integer, default=0)
    
    # Timestamps
    last_streak_date = Column(String, nullable=True)
    last_activity_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relacionamentos
    todos = relationship("TodoItem", back_populates="owner", cascade="all, delete-orphan")
    forest = relationship("TreeHistory", back_populates="owner", cascade="all, delete-orphan")
    unlocked_skills = relationship("SkillUnlocked", back_populates="owner", cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="owner", cascade="all, delete-orphan")
    drafts = relationship("DraftItem", back_populates="owner", cascade="all, delete-orphan")

class TreeHistory(Base):
    __tablename__ = "tree_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    theme = Column(String, default="cajuina")
    completed_at = Column(String, nullable=False)

    owner = relationship("User", back_populates="forest")

class TodoItem(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="todos")

class SkillUnlocked(Base):
    __tablename__ = "skills_unlocked"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_id = Column(String, nullable=False)

    owner = relationship("User", back_populates="unlocked_skills")

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(String, nullable=False) # ex: 'goldpot', 'aura', 'potion_vitality', etc.
    quantity = Column(Integer, default=1)
    equipped = Column(Boolean, default=False)

    owner = relationship("User", back_populates="inventory")

class DraftItem(Base):
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(String, index=True, nullable=False)
    content = Column(String, default="")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="drafts")
