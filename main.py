import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Product, Vendor, Category, Review, Order

app = FastAPI(title="Saree Sanctuary API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "Saree Sanctuary API", "status": "ok"}


@app.get("/schema")
def get_schema():
    # Expose schema classes for the database viewer
    return {
        "category": Category.model_json_schema(),
        "vendor": Vendor.model_json_schema(),
        "product": Product.model_json_schema(),
        "review": Review.model_json_schema(),
        "order": Order.model_json_schema(),
    }


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set" if not os.getenv("DATABASE_URL") else "✅ Set",
        "database_name": "❌ Not Set" if not os.getenv("DATABASE_NAME") else "✅ Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()
            except Exception:
                pass
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ---------- Seed sample data ----------
@app.post("/api/seed")
def seed_data():
    if db is None:
        raise HTTPException(503, "Database not available")

    created = {"categories": 0, "vendors": 0, "products": 0, "reviews": 0}

    # Categories
    existing_cats = list(db["category"].find({}))
    if not existing_cats:
        categories = [
            {"name": "Banarasi", "slug": "banarasi"},
            {"name": "Kanjivaram", "slug": "kanjivaram"},
            {"name": "Cotton", "slug": "cotton"},
            {"name": "Silk", "slug": "silk"},
            {"name": "Organza", "slug": "organza"},
        ]
        for c in categories:
            create_document("category", c)
            created["categories"] += 1

    # Vendors
    existing_vendors = list(db["vendor"].find({}))
    if not existing_vendors:
        vendors = [
            {"store_name": "Varanasi Weaves", "slug": "varanasi-weaves", "about": "Handwoven Banarasi sarees.", "verified": True, "region": "Varanasi"},
            {"store_name": "Kanjivaram Katha", "slug": "kanjivaram-katha", "about": "Traditional Kanjivaram silk.", "verified": True, "region": "Kanchipuram"},
            {"store_name": "Cotton Looms", "slug": "cotton-looms", "about": "Breathable cotton sarees.", "verified": False, "region": "Coimbatore"},
        ]
        for v in vendors:
            create_document("vendor", v)
            created["vendors"] += 1

    # Products
    existing_products = list(db["product"].find({}))
    if not existing_products:
        products = [
            {
                "title": "Royal Banarasi Brocade",
                "slug": "royal-banarasi-brocade",
                "description": "Rich zari work with traditional motifs.",
                "vendor_slug": "varanasi-weaves",
                "price_in_paise": 899900,
                "saree_type": "Banarasi",
                "color": "Maroon",
                "material": "Silk",
                "occasion": "Wedding",
                "care": "Dry clean only",
                "images": [
                    "https://images.unsplash.com/photo-1603575448894-0474f35f9f1b?q=80&w=1200&auto=format&fit=crop",
                ],
                "stock": 8,
            },
            {
                "title": "Classic Kanjivaram Gold",
                "slug": "classic-kanjivaram-gold",
                "description": "Pure silk with gold border.",
                "vendor_slug": "kanjivaram-katha",
                "price_in_paise": 1299900,
                "saree_type": "Kanjivaram",
                "color": "Indigo",
                "material": "Silk",
                "occasion": "Festive",
                "care": "Dry clean only",
                "images": [
                    "https://images.unsplash.com/photo-1610563166150-6ed79b3b6d62?q=80&w=1200&auto=format&fit=crop",
                ],
                "stock": 5,
            },
            {
                "title": "Summer Breeze Cotton",
                "slug": "summer-breeze-cotton",
                "description": "Lightweight cotton saree.",
                "vendor_slug": "cotton-looms",
                "price_in_paise": 299900,
                "saree_type": "Cotton",
                "color": "Saffron",
                "material": "Cotton",
                "occasion": "Casual",
                "care": "Machine wash gentle",
                "images": [
                    "https://images.unsplash.com/photo-1585487000160-6f1a5e60e1f9?q=80&w=1200&auto=format&fit=crop",
                ],
                "stock": 20,
            },
        ]
        for p in products:
            create_document("product", p)
            created["products"] += 1

    # Reviews sample
    existing_reviews = list(db["review"].find({}))
    if not existing_reviews:
        reviews = [
            {"product_slug": "royal-banarasi-brocade", "rating": 5, "comment": "Stunning craftsmanship!", "author_name": "Asha"},
            {"product_slug": "classic-kanjivaram-gold", "rating": 4, "comment": "Luxurious and elegant.", "author_name": "Meera"},
        ]
        for r in reviews:
            create_document("review", r)
            created["reviews"] += 1

    return {"seeded": created}


# ---------- Products ----------
@app.get("/api/products")
def list_products(
    q: Optional[str] = None,
    saree_type: Optional[str] = None,
    color: Optional[str] = None,
    material: Optional[str] = None,
    occasion: Optional[str] = None,
    limit: int = Query(24, ge=1, le=100),
):
    if db is None:
        return []
    filter_dict = {}
    if q:
        # Basic text search across title/description
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    if saree_type:
        filter_dict["saree_type"] = saree_type
    if color:
        filter_dict["color"] = color
    if material:
        filter_dict["material"] = material
    if occasion:
        filter_dict["occasion"] = occasion
    docs = get_documents("product", filter_dict=filter_dict, limit=limit)
    # Convert ObjectId to str if present
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return docs


@app.get("/api/products/{slug}")
def get_product(slug: str):
    if db is None:
        raise HTTPException(503, "Database not available")
    docs = get_documents("product", {"slug": slug}, limit=1)
    if not docs:
        raise HTTPException(404, "Product not found")
    d = docs[0]
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # attach reviews
    reviews = get_documents("review", {"product_slug": slug}, limit=50)
    for r in reviews:
        if "_id" in r:
            r["id"] = str(r.pop("_id"))
    d["reviews"] = reviews
    return d


class CreateProductBody(Product):
    pass


@app.post("/api/products")
def create_product(body: CreateProductBody):
    if db is None:
        raise HTTPException(503, "Database not available")
    pid = create_document("product", body)
    return {"id": pid}


# ---------- Vendors ----------
@app.get("/api/vendors")
def list_vendors(limit: int = Query(20, ge=1, le=100)):
    if db is None:
        return []
    docs = get_documents("vendor", limit=limit)
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return docs


@app.get("/api/vendors/{slug}")
def get_vendor(slug: str):
    if db is None:
        raise HTTPException(503, "Database not available")
    docs = get_documents("vendor", {"slug": slug}, limit=1)
    if not docs:
        raise HTTPException(404, "Vendor not found")
    d = docs[0]
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    # attach products preview
    products = get_documents("product", {"vendor_slug": slug}, limit=50)
    for p in products:
        if "_id" in p:
            p["id"] = str(p.pop("_id"))
    d["products"] = products
    return d


class CreateVendorBody(Vendor):
    pass


@app.post("/api/vendors")
def create_vendor(body: CreateVendorBody):
    if db is None:
        raise HTTPException(503, "Database not available")
    vid = create_document("vendor", body)
    return {"id": vid}


# ---------- Reviews ----------
class CreateReviewBody(Review):
    pass


@app.get("/api/reviews/{product_slug}")
def list_reviews(product_slug: str, limit: int = Query(20, ge=1, le=100)):
    if db is None:
        return []
    docs = get_documents("review", {"product_slug": product_slug}, limit=limit)
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return docs


@app.post("/api/reviews")
def create_review(body: CreateReviewBody):
    if db is None:
        raise HTTPException(503, "Database not available")
    rid = create_document("review", body)
    return {"id": rid}


# ---------- Orders (MVP, no payments) ----------
class CreateOrderBody(Order):
    pass


@app.post("/api/orders")
def create_order(body: CreateOrderBody):
    if db is None:
        raise HTTPException(503, "Database not available")
    oid = create_document("order", body)
    return {"id": oid, "status": body.status}


# ---------- Categories (seedable) ----------
@app.get("/api/categories")
def list_categories(limit: int = Query(20, ge=1, le=100)):
    if db is None:
        return [
            {"name": "Banarasi", "slug": "banarasi"},
            {"name": "Kanjivaram", "slug": "kanjivaram"},
            {"name": "Cotton", "slug": "cotton"},
            {"name": "Silk", "slug": "silk"},
            {"name": "Organza", "slug": "organza"},
        ]
    docs = get_documents("category", limit=limit)
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    return docs


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
