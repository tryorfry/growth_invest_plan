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

    def create_portfolio(self, name: str, description: str = "", initial_balance: float = 0.0) -> Portfolio:
        """Create a new portfolio"""
        portfolio = Portfolio(name=name, description=description, initial_balance=initial_balance, user_id=self.user_id)
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
                qty = float(t.quantity or 0.0)
                price = float(t.price or 0.0)
                fees = float(t.fees or 0.0)
                
                new_qty = holdings[ticker]['qty'] + qty
                new_spent = holdings[ticker]['total_spent'] + (qty * price) + fees
                holdings[ticker]['qty'] = new_qty
                holdings[ticker]['total_spent'] = new_spent
                holdings[ticker]['cost_basis'] = new_spent / new_qty if new_qty > 0 else 0
            elif t.type == 'SELL':
                qty = float(t.quantity or 0.0)
                holdings[ticker]['qty'] -= qty
                # Reduce total spent proportionally when selling
                if holdings[ticker]['qty'] <= 0:
                    holdings[ticker]['qty'] = 0
                    holdings[ticker]['total_spent'] = 0
                    holdings[ticker]['cost_basis'] = 0
                else:
                    # Maintain the same cost basis per share, just reduce total spent
                    holdings[ticker]['total_spent'] = holdings[ticker]['cost_basis'] * holdings[ticker]['qty']
                    
        # Filter out empty holdings
        active_holdings = {k: v for k, v in holdings.items() if v['qty'] > 0}
        
        if not active_holdings:
            return pd.DataFrame()
            
        return pd.DataFrame.from_dict(active_holdings, orient='index').reset_index().rename(columns={'index': 'Ticker'})

    def get_portfolio_performance(self, portfolio_id: int, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """Calculate total portfolio performance metrics and available cash"""
        
        # Get portfolio config
        portfolio = self.session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        initial_balance = float(portfolio.initial_balance or 0.0) if portfolio else 0.0
        
        # Calculate cash available from all transactions
        transactions = self.session.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id
        ).all()
        
        cash_balance = initial_balance
        for t in transactions:
            qty = float(t.quantity or 0.0)
            price = float(t.price or 0.0)
            fees = float(t.fees or 0.0)
            
            if t.type == 'BUY':
                cash_balance -= (qty * price) + fees
            elif t.type == 'SELL':
                cash_balance += (qty * price) - fees
        
        df = self.get_portfolio_holdings(portfolio_id)
        
        if df.empty:
            return {
                'total_value': 0.0, 
                'total_cost': 0.0, 
                'total_pl': 0.0, 
                'total_pl_pct': 0.0, 
                'cash_balance': cash_balance,
                'nlv': cash_balance
            }
            
        total_market_value = 0.0
        total_cost = 0.0
        
        # Sector allocation tracking
        sectors = {}
        
        for _, row in df.iterrows():
            ticker = row['Ticker']
            current_price = float(current_prices.get(ticker, 0.0))
            position_value = float(row['qty']) * current_price
            total_market_value += position_value
            total_cost += float(row['total_spent'])
            
            # Fetch Sector
            stock = self.session.query(Stock).filter(Stock.ticker == ticker).first()
            sector_name = stock.sector if stock and stock.sector else "Unknown"
            if sector_name not in sectors:
                sectors[sector_name] = 0.0
            sectors[sector_name] += position_value
            
        total_pl = total_market_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0
        nlv = cash_balance + total_market_value
        
        # Calculate Sector Percentages
        sector_allocation = {}
        if total_market_value > 0:
            for s_name, value in sectors.items():
                sector_allocation[s_name] = (value / total_market_value) * 100
        
        return {
            'total_value': total_market_value,
            'total_cost': total_cost,
            'total_pl': total_pl,
            'total_pl_pct': total_pl_pct,
            'cash_balance': cash_balance,
            'nlv': nlv,
            'sector_allocation': sector_allocation
        }
