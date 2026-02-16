import asyncpg
import aiomysql
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Any
from contextlib import asynccontextmanager

from app.core.config import settings

# --- Connection Pools ---

_pg_pool: Optional[asyncpg.Pool] = None
_mysql_pools: dict[str, aiomysql.Pool] = {}
_mongo_client: Optional[AsyncIOMotorClient] = None


async def init_postgres():
    global _pg_pool
    _pg_pool = await asyncpg.create_pool(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        min_size=2,
        max_size=10,
    )


async def close_postgres():
    global _pg_pool
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None


async def get_pg_pool() -> asyncpg.Pool:
    if _pg_pool is None:
        await init_postgres()
    return _pg_pool


@asynccontextmanager
async def get_pg_connection():
    pool = await get_pg_pool()
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)


# --- MySQL ---

async def get_mysql_pool(db_name: str) -> aiomysql.Pool:
    if db_name not in _mysql_pools:
        _mysql_pools[db_name] = await aiomysql.create_pool(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=db_name,
            minsize=1,
            maxsize=5,
            charset="utf8mb4",
            autocommit=True,
        )
    return _mysql_pools[db_name]


@asynccontextmanager
async def get_mysql_connection(db_name: str):
    pool = await get_mysql_pool(db_name)
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        pool.release(conn)


async def close_mysql_pools():
    for pool in _mysql_pools.values():
        pool.close()
        await pool.wait_closed()
    _mysql_pools.clear()


async def mysql_query(
    db_name: str,
    sql: str,
    params: tuple = (),
    fetch_one: bool = False,
) -> Any:
    async with get_mysql_connection(db_name) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, params)
            if fetch_one:
                return await cur.fetchone()
            return await cur.fetchall()


async def mysql_execute(db_name: str, sql: str, params: tuple = ()) -> int:
    async with get_mysql_connection(db_name) as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            await conn.commit()
            return cur.lastrowid


# --- MongoDB ---

def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    return _mongo_client


def get_mongo_db():
    client = get_mongo_client()
    return client[settings.MONGO_DB_NAME]


async def close_mongo():
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None


# --- Lifecycle ---

async def startup_db():
    await init_postgres()


async def shutdown_db():
    await close_postgres()
    await close_mysql_pools()
    await close_mongo()
