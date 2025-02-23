from fastapi import FastAPI, Query, Depends, HTTPException
from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from aioredis import create_redis_pool
import random, lorem, json

app = FastAPI()

# Database configuration
database_url = 'postgresql://postgres:password@db:5432/clientes_db'
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis caching configuration
redis_url = 'redis://caching-db:6379/0'
redis = None

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Product model
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    price = Column(Float)
    description = Column(String(500))

class Cliente(Base):
    __tablename__ = 'cliente'

    id_cliente = Column(Integer, primary_key=True)
    nome_cliente = Column(String(100), unique=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Add dummy product data
# db = SessionLocal()
# for i in range(1, 101):
#     name = f'Product_{i}'
#     price = round(random.uniform(1.99, 999.99), 2)
#     description = lorem.get_sentence(count=2)
#     product = Product(name=name, price=price, description=description)
#     db.add(product)
# db.commit()
# db.close()

# Set up Redis connection
@app.on_event("startup")
async def startup_event():
    global redis
    redis = await create_redis_pool(redis_url)

# Shutdown Redis connection
@app.on_event("shutdown")
async def shutdown_event():
    global redis
    redis.close()
    await redis.wait_closed()

# API endpoints
@app.get('/products')
async def get_all_products(db = Depends(get_db)):
    products = await redis.get('products')
    if products:
        return json.loads(products)
    
    products = db.query(Product).all()
    result = []
    for product in products:
        result.append({
            'name': product.name,
            'price': product.price,
            'description': product.description
        })
    await redis.set('products', json.dumps(result))

    return result

@app.get('/clientes')
async def get_all_products(db = Depends(get_db)):
    clientes = await redis.get('cliente')
    if clientes:
        return json.loads(clientes)
    
    clientes = db.query(Cliente).all()
    result = []
    for cliente in clientes:
        result.append({
            'name': cliente.nome_cliente,
        })
    await redis.set('products', json.dumps(result))

    return result

@app.get('/products/search')
async def search_product(keyword: str = Query(..., min_length=1), db = Depends(get_db)):
    result = await redis.get(keyword)
    if result:
        return json.loads(result)

    products = db.query(Product).filter(Product.name.ilike(f'%{keyword}%')).all()
    result = []
    for product in products:
        result.append({
            'name': product.name,
            'price': product.price,
            'description': product.description
        })
    await redis.set(keyword, json.dumps(result))

    return result

@app.get('/products/price-range')
async def get_products_by_price_range(min_price: float = Query(...), max_price: float = Query(...), db = Depends(get_db)):
    result = await redis.get(f'{min_price}_{max_price}')
    if result:
        return json.loads(result)

    products = db.query(Product).filter(Product.price.between(min_price, max_price)).all()
    result = []
    for product in products:
        result.append({
            'name': product.name,
            'price': product.price,
            'description': product.description
        })
    await redis.set(f'{min_price}_{max_price}', json.dumps(result))

    return result

@app.get('/products/{name}')
async def get_product_by_name(name: str, db = Depends(get_db)):
    product = await redis.get(name)
    if product:
        return json.loads(product)

    product = db.query(Product).filter_by(name=name).first()
    if product:
        result = {
            'name': product.name,
            'price': product.price,
            'description': product.description
            }
        await redis.set(name, json.dumps(result))
        return result
    else:
        raise HTTPException(status_code=404, detail='Product not found')