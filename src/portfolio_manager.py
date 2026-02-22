"""Portfolio management business logic"""

import pandas as pd
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import Portfolio, Transaction, Stock, Analysis

class PortfolioManager:
    """Manages portfolios, transactions, and performance metrics"""
    
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id

    def create_portfolio(self, name: str, description: str = "") -> Portfolio:
        """Create a new portfolio"""
        portfolio = Portfolio(name=name, description=description, user_id=self.user_id)
        self.session.add(portfolio)
        self.session.commit()
        return portfolio

    def add_transaction(self, portfolio_id: int, ticker: str, trans_type: str, 
                       quantity: float, price: float, fees: float = 0.0, 
                       notes: str = "") -> Transaction:
        """Add a new transaction to a portfolio"""
        # Ensure stock exists
        stock = self.session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            stock = Stock(ticker=ticker)
            self.session.add(stock)
            self.session.flush()
            
        transaction = Transaction(
            portfolio_id=portfolio_id,
            stock_id=stock.id,
            type=trans_type.upper(),
            quantity=quantity,
            price=price,
            fees=fees,
            notes=notes
        )
        self.session.add(transaction)
        self.session.commit()
        return transaction

    def get_portfolio_holdings(self, portfolio_id: int) -> pd.DataFrame:
        """Calculate current holdings and cost basis for a portfolio"""
        transactions = self.session.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id
        ).all()
        
        if not transactions:
            return pd.DataFrame()
            
        holdings = {}
        for t in transactions:
            ticker = t.stock.ticker
            if ticker not in holdings:
                holdings[ticker] = {'qty': 0.0, 'cost_basis': 0.0, 'total_spent': 0.0}
            
            if t.type == 'BUY':
                new_qty = holdings[ticker]['qty'] + t.quantity
                new_spent = holdings[ticker]['total_spent'] + (t.quantity * t.price) + t.fees
                holdings[ticker]['qty'] = new_qty
                holdings[ticker]['total_spent'] = new_spent
                holdings[ticker]['cost_basis'] = new_spent / new_qty if new_qty > 0 else 0
            elif t.type == 'SELL':
                holdings[ticker]['qty'] -= t.quantity
                # For simplicity, we don't adjust cost basis on sell, just reduce quantity
                if holdings[ticker]['qty'] <= 0:
                    holdings[ticker]['qty'] = 0
                    holdings[ticker]['total_spent'] = 0
                    holdings[ticker]['cost_basis'] = 0
                    
        # Filter out empty holdings
        active_holdings = {k: v for k, v in holdings.items() if v['qty'] > 0}
        
        if not active_holdings:
            return pd.DataFrame()
            
        return pd.DataFrame.from_dict(active_holdings, orient='index').reset_index().rename(columns={'index': 'Ticker'})

    def get_portfolio_performance(self, portfolio_id: int, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """Calculate total portfolio performance metrics"""
        df = self.get_portfolio_holdings(portfolio_id)
        if df.empty:
            return {'total_value': 0.0, 'total_cost': 0.0, 'total_pl': 0.0, 'total_pl_pct': 0.0}
            
        total_value = 0.0
        total_cost = 0.0
        
        for _, row in df.iterrows():
            ticker = row['Ticker']
            current_price = current_prices.get(ticker, 0.0)
            total_value += row['qty'] * current_price
            total_cost += row['total_spent']
            
        total_pl = total_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pl': total_pl,
            'total_pl_pct': total_pl_pct
        }
