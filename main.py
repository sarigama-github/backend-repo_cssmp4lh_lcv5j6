import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import LingerieProduct

app = FastAPI(title="Lingerie Shop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Lingerie Shop API running"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Utility to convert Mongo documents
class ProductOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    price: float
    category: str
    images: List[str] = []
    colors: List[str] = []
    sizes: List[str] = []
    tags: List[str] = []
    in_stock: bool
    is_featured: bool
    rating: Optional[float] = None


@app.post("/api/products", response_model=dict)
async def create_product(product: LingerieProduct):
    collection = "lingerieproduct"
    try:
        inserted_id = create_document(collection, product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products", response_model=List[ProductOut])
async def list_products(category: Optional[str] = None, featured: Optional[bool] = None):
    collection = "lingerieproduct"
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    if featured is not None:
        filter_dict["is_featured"] = featured

    try:
        docs = get_documents(collection, filter_dict)
        results: List[ProductOut] = []
        for d in docs:
            results.append(ProductOut(
                id=str(d.get("_id")),
                title=d.get("title"),
                description=d.get("description"),
                price=float(d.get("price", 0)),
                category=d.get("category"),
                images=[str(x) for x in d.get("images", [])],
                colors=[str(x) for x in d.get("colors", [])],
                sizes=[str(x) for x in d.get("sizes", [])],
                tags=[str(x) for x in d.get("tags", [])],
                in_stock=bool(d.get("in_stock", True)),
                is_featured=bool(d.get("is_featured", False)),
                rating=d.get("rating") if d.get("rating") is not None else None
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/sample", response_model=List[ProductOut])
async def seed_sample_products():
    """Convenience endpoint to seed some demo products if collection is empty"""
    collection = "lingerieproduct"
    try:
        existing = get_documents(collection, {}, limit=1)
        if existing:
            # Return first few documents
            docs = get_documents(collection, {}, limit=12)
            return [
                ProductOut(
                    id=str(d.get("_id")),
                    title=d.get("title"),
                    description=d.get("description"),
                    price=float(d.get("price", 0)),
                    category=d.get("category"),
                    images=[str(x) for x in d.get("images", [])],
                    colors=[str(x) for x in d.get("colors", [])],
                    sizes=[str(x) for x in d.get("sizes", [])],
                    tags=[str(x) for x in d.get("tags", [])],
                    in_stock=bool(d.get("in_stock", True)),
                    is_featured=bool(d.get("is_featured", False)),
                    rating=d.get("rating") if d.get("rating") is not None else None
                ) for d in docs
            ]
        # Seed
        demo = [
            {
                "title": "Silk Embrace Bra",
                "description": "Luxurious silk with delicate lace trim.",
                "price": 69.0,
                "category": "bras",
                "images": [
                    "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?q=80&w=1200&auto=format&fit=crop"
                ],
                "colors": ["black", "blush", "ivory"],
                "sizes": ["32B", "34C", "36D"],
                "tags": ["silk", "lace", "underwire"],
                "is_featured": True,
                "rating": 4.7
            },
            {
                "title": "Velvet Night Set",
                "description": "Two-piece velvet lounge set.",
                "price": 89.0,
                "category": "sets",
                "images": [
                    "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?q=80&w=1200&auto=format&fit=crop"
                ],
                "colors": ["wine", "emerald"],
                "sizes": ["S", "M", "L"],
                "tags": ["set", "velvet", "lounge"],
                "is_featured": True,
                "rating": 4.5
            },
            {
                "title": "Everyday Comfort Brief",
                "description": "Breathable cotton mid-rise brief.",
                "price": 18.0,
                "category": "panties",
                "images": [
                    "https://images.unsplash.com/photo-1516641392179-434d6d130a7b?q=80&w=1200&auto=format&fit=crop"
                ],
                "colors": ["nude", "black", "white"],
                "sizes": ["S", "M", "L", "XL"],
                "tags": ["cotton", "comfort"],
                "rating": 4.2
            }
        ]
        for item in demo:
            create_document(collection, item)
        docs = get_documents(collection, {}, limit=12)
        return [
            ProductOut(
                id=str(d.get("_id")),
                title=d.get("title"),
                description=d.get("description"),
                price=float(d.get("price", 0)),
                category=d.get("category"),
                images=[str(x) for x in d.get("images", [])],
                colors=[str(x) for x in d.get("colors", [])],
                sizes=[str(x) for x in d.get("sizes", [])],
                tags=[str(x) for x in d.get("tags", [])],
                in_stock=bool(d.get("in_stock", True)),
                is_featured=bool(d.get("is_featured", False)),
                rating=d.get("rating") if d.get("rating") is not None else None
            ) for d in docs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
