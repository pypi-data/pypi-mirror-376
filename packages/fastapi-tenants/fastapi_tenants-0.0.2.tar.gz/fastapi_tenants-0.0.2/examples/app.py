# examples/app.py
from fastapi import FastAPI
from fastapi_tenants.transport.header import HeaderTransport
from fastapi_tenants.middleware.tenant_middleware import TenantMiddleware
from fastapi_tenants.db.registry import TenantRegistry
from fastapi_tenants.db.factory import default_create_engine

from sqlalchemy.ext.asyncio import AsyncEngine

from fastapi_tenants.db import deps as deps_mod

app = FastAPI()


async def create_engine_fn(tenant_id: str) -> AsyncEngine:
    # In prod: fetch secrets from secure store, construct DSN, return engine
    base = "postgresql+asyncpg://user:pass@localhost:5432/{tenant}"
    return await default_create_engine(tenant_id, base)


registry = TenantRegistry(create_engine_fn)
# attach to global so deps can use; alternatively store on app.state

deps_mod.tenant_registry = registry


@app.on_event("startup")
async def startup() -> None:
    await registry.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    await registry.stop()


# header extractor instance
hdr = HeaderTransport("X-Tenant-Id")
app.add_middleware(TenantMiddleware, extractor=hdr.extract_tenant)
