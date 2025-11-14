"""
Database Schemas for Saree Sanctuary

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase of the class name.

Use these models for validation before writing to the database.
"""

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl


class Category(BaseModel):
    name: str = Field(..., description="Display name of the category (e.g., Banarasi)")
    slug: str = Field(..., description="URL-safe unique slug (e.g., banarasi)")


class Vendor(BaseModel):
    store_name: str = Field(..., description="Public store name")
    slug: str = Field(..., description="URL-safe unique slug for the vendor")
    logo_url: Optional[HttpUrl] = Field(None, description="Public logo URL")
    about: Optional[str] = Field(None, description="Short story/about the vendor")
    verified: bool = Field(False, description="Whether vendor is verified")
    membership_status: Literal["active", "expired"] = Field("active")
    membership_renewal_date: Optional[str] = Field(None, description="ISO date string for renewal")
    region: Optional[str] = Field(None, description="Vendor region/city/state")


class Product(BaseModel):
    title: str
    slug: str
    description: Optional[str] = None
    vendor_slug: str = Field(..., description="FK to Vendor.slug")
    price_in_paise: int = Field(..., ge=0)
    saree_type: str = Field(..., description="Category name or type")
    color: Optional[str] = None
    material: Optional[str] = None
    occasion: Optional[str] = None
    care: Optional[str] = None
    images: List[HttpUrl] = Field(default_factory=list)
    stock: int = Field(10, ge=0)


class Review(BaseModel):
    product_slug: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    author_name: Optional[str] = None


class Order(BaseModel):
    buyer_name: str
    buyer_email: str
    vendor_slug: str
    items: List[dict] = Field(..., description="List of items with product_slug, quantity, price_in_paise")
    total_in_paise: int = Field(..., ge=0)
    status: Literal["pending", "paid", "dispatched", "delivered", "refunded"] = "pending"


# Note for the built-in database viewer:
# - It will read these via GET /schema
# - Use class name lowercased as the collection name
