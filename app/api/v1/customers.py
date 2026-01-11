from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_merchant
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.invoice import InvoiceResponse

router = APIRouter()


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer: CustomerCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Create a new customer for the authenticated merchant"""
    db_customer = Customer(
        merchant_id=current_merchant.id,
        **customer.model_dump()
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    return CustomerResponse.model_validate(db_customer)


@router.get("", response_model=List[CustomerResponse])
def get_all_customers(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get all customers for the authenticated merchant"""
    customers = db.query(Customer).filter(
        Customer.merchant_id == current_merchant.id
    ).all()
    
    return [CustomerResponse.model_validate(customer) for customer in customers]


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer_by_id(
    customer_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get a specific customer by ID for the authenticated merchant"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.merchant_id == current_merchant.id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    customer_update: CustomerUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Update customer details for the authenticated merchant"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.merchant_id == current_merchant.id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Get only the fields that were provided (not None)
    update_data = customer_update.model_dump(exclude_unset=True)
    
    # Update the customer with provided fields
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    
    return CustomerResponse.model_validate(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Delete a customer for the authenticated merchant"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.merchant_id == current_merchant.id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    db.delete(customer)
    db.commit()
    
    return None


@router.get("/{customer_id}/invoices", response_model=List[InvoiceResponse])
def get_customer_invoices(
    customer_id: UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get all invoices for a specific customer"""
    # Validate customer belongs to merchant
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.merchant_id == current_merchant.id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to merchant"
        )
    
    # Get all invoices for this customer (not soft deleted)
    invoices = db.query(Invoice).filter(
        Invoice.customer_id == customer_id,
        Invoice.merchant_id == current_merchant.id,
        Invoice.deleted_at.is_(None)
    ).order_by(Invoice.created_at.desc()).all()
    
    return [InvoiceResponse.model_validate(invoice) for invoice in invoices]

