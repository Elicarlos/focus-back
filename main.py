from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging
import database, models, schemas, auth
import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Inicializa as tabelas do banco de dados
try:
    logger.info("Criando tabelas no banco de dados se não existirem...")
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Conexão e inicialização das tabelas no banco de dados realizadas com sucesso.")
except Exception as e:
    logger.error(f"Erro ao conectar ou criar tabelas no banco de dados: {str(e)}")

app = FastAPI(title="Pragma Focus API", version="1.0.0")

# Habilita CORS para permitir conexões do front-end hospedado em outro domínio/VPS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://a33qw28hn83ky06i7gua435q.187.127.15.180.sslip.io",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/")
def read_root():
    return {"message": "Pragma Focus Central Backend Online"}

# --- AUTENTICAÇÃO E CADASTRO ---
@app.post("/auth/google", response_model=schemas.Token)
async def auth_google(payload: schemas.GoogleAuthRequest, db: Session = Depends(database.get_db)):
    # Valida credencial do Google
    google_data = await auth.verify_google_token(payload.credential_token)
    email = google_data.get("email")
    name = google_data.get("name", email.split("@")[0])
    picture = google_data.get("picture", "")
    locale = google_data.get("locale", "BR").upper()[:2] # Ex: en-US -> US ou pt-BR -> BR
    
    # Verifica se usuário existe, se não, cria um novo (Cadastro Automático)
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # Garante username único
        username_base = name.replace(" ", "_").lower()
        username = username_base
        count = 1
        while db.query(models.User).filter(models.User.username == username).first():
            username = f"{username_base}_{count}"
            count += 1
            
        user = models.User(
            email=email,
            username=username,
            avatar_url=picture,
            country=locale,
            xp=0,
            level=1,
            gems=100,
            streak=0,
            water_units=0,
            skill_points=0,
            tree_health=100,
            tree_dead=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Concede cosméticos iniciais de onboarding se necessário
        initial_cosmetic = models.InventoryItem(user_id=user.id, item_id="goldpot", quantity=1, equipped=False)
        db.add(initial_cosmetic)
        db.commit()

    # Gera token JWT local do SaaS
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# --- GESTÃO DE ESTADO DO JOGADOR (SYNC & ANTIFRAUDE) ---
@app.get("/users/me", response_model=schemas.UserResponse)
def get_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.put("/users/me/sync", response_model=schemas.UserResponse)
def sync_user_state(
    payload: schemas.UserResponse, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # ANTIFRAUDE: Auditoria básica de consistência de dados recebidos do front
    # 1. Impede ganho massivo absurdo de XP de uma vez só (Anti-Cheat no Rank)
    xp_diff = payload.xp + (payload.level * 100) - (current_user.xp + (current_user.level * 100))
    if xp_diff > 1200: # Limite de ganho plausível por ciclo de sincronização
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anomalia de consistência no ganho de XP detectada!"
        )
        
    # 2. Impede alteração ilegal de Gemas (Anti-Cheat da Loja)
    gems_diff = payload.gems - current_user.gems
    if gems_diff > 500: # Limite seguro para evitar injeção de moedas
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inconsistência na carteira de gemas detectada!"
        )

    # Sincroniza dados permitidos
    current_user.xp = payload.xp
    current_user.level = payload.level
    current_user.gems = payload.gems
    current_user.streak = payload.streak
    current_user.water_units = payload.water_units
    current_user.skill_points = payload.skill_points
    current_user.tree_health = payload.tree_health
    current_user.tree_dead = payload.tree_dead
    
    current_user.mudas = payload.mudas
    current_user.adubos = payload.adubos
    current_user.essencias = payload.essencias
    
    current_user.last_streak_date = payload.last_streak_date
    current_user.last_activity_date = payload.last_activity_date
    
    db.commit()
    db.refresh(current_user)
    return current_user


# --- TAREFAS SECUNDÁRIAS (TO-DO LIST) ---
@app.get("/todos", response_model=List[schemas.TodoResponse])
def read_todos(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return db.query(models.TodoItem).filter(models.TodoItem.user_id == current_user.id).all()

@app.post("/todos", response_model=schemas.TodoResponse)
def create_todo(
    todo: schemas.TodoCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_todo = models.TodoItem(user_id=current_user.id, text=todo.text, completed=False)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.put("/todos/{todo_id}", response_model=schemas.TodoResponse)
def update_todo(
    todo_id: int,
    todo_update: schemas.TodoUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_todo = db.query(models.TodoItem).filter(
        models.TodoItem.id == todo_id, 
        models.TodoItem.user_id == current_user.id
    ).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
    db_todo.completed = todo_update.completed
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_todo = db.query(models.TodoItem).filter(
        models.TodoItem.id == todo_id, 
        models.TodoItem.user_id == current_user.id
    ).first()
    if not db_todo:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
    db.delete(db_todo)
    db.commit()
    return {"message": "Tarefa deletada"}


# --- BOSQUE DE TROFÉUS (FOREST) ---
@app.get("/forest", response_model=List[schemas.TreeHistoryResponse])
def get_forest(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return db.query(models.TreeHistory).filter(models.TreeHistory.user_id == current_user.id).all()

@app.post("/forest", response_model=schemas.TreeHistoryResponse)
def add_tree_to_forest(
    tree: schemas.TreeHistoryResponse,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_tree = models.TreeHistory(
        user_id=current_user.id,
        name=tree.name,
        level=tree.level,
        theme=tree.theme,
        completed_at=tree.completed_at
    )
    db.add(db_tree)
    db.commit()
    db.refresh(db_tree)
    return db_tree


# --- INVENTÁRIO (BAÚ DE ITENS & SHOP) ---
@app.get("/inventory", response_model=List[schemas.InventoryItemResponse])
def get_user_inventory(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return db.query(models.InventoryItem).filter(models.InventoryItem.user_id == current_user.id).all()

@app.put("/inventory/{item_id}/equip", response_model=schemas.InventoryItemResponse)
def equip_item(
    item_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.user_id == current_user.id,
        models.InventoryItem.item_id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado no seu baú")
        
    item.equipped = not item.equipped
    db.commit()
    db.refresh(item)
    return item


# --- EDITORES DE RASCUNHOS ---
@app.get("/drafts", response_model=List[schemas.DraftResponse])
def read_drafts(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return db.query(models.DraftItem).filter(models.DraftItem.user_id == current_user.id).all()

@app.put("/drafts", response_model=schemas.DraftResponse)
def update_draft(
    draft: schemas.DraftBase,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_draft = db.query(models.DraftItem).filter(
        models.DraftItem.user_id == current_user.id,
        models.DraftItem.template_id == draft.template_id
    ).first()
    
    if not db_draft:
        db_draft = models.DraftItem(
            user_id=current_user.id,
            template_id=draft.template_id,
            content=draft.content
        )
        db.add(db_draft)
    else:
        db_draft.content = draft.content
        
    db.commit()
    db.refresh(db_draft)
    return db_draft


# --- RANKING GLOBAL MUNDIAL ---
@app.get("/ranking", response_model=List[schemas.RankUserResponse])
def get_global_ranking(db: Session = Depends(database.get_db)):
    # Retorna o TOP 50 usuários ordenados por Nível e XP acumulado
    return db.query(models.User).order_by(
        models.User.level.desc(), 
        models.User.xp.desc()
    ).limit(50).all()
