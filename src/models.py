"""
Database models and data persistence layer using SQLAlchemy.

Provides caching of GEX data, historical tracking, and configuration storage.
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


logger = logging.getLogger('GammaScope.Models')

Base = declarative_base()


class GEXSnapshot(Base):
    """
    Stores GEX snapshot data for a symbol at a specific timestamp.
    """
    __tablename__ = 'gex_snapshots'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    underlying_price = Column(Float, nullable=False)

    # Aggregated GEX metrics
    total_call_gex = Column(Float, nullable=False)
    total_put_gex = Column(Float, nullable=False)
    net_gex = Column(Float, nullable=False)

    # DEX metrics
    total_call_dex = Column(Float, nullable=True)
    total_put_dex = Column(Float, nullable=True)
    net_dex = Column(Float, nullable=True)

    # Open interest
    total_call_oi = Column(Integer, nullable=False)
    total_put_oi = Column(Integer, nullable=False)

    # Gamma flip point
    gamma_flip_point = Column(Float, nullable=True)

    # Per-strike data stored as JSON
    per_strike_data = Column(Text, nullable=False)  # JSON serialized

    # Metadata
    expiration_filter = Column(String(50), nullable=True)
    data_quality = Column(String(20), default='good')  # good, partial, stale

    # Indexes for common queries
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'underlying_price': self.underlying_price,
            'total_call_gex': self.total_call_gex,
            'total_put_gex': self.total_put_gex,
            'net_gex': self.net_gex,
            'total_call_dex': self.total_call_dex,
            'total_put_dex': self.total_put_dex,
            'net_dex': self.net_dex,
            'total_call_oi': self.total_call_oi,
            'total_put_oi': self.total_put_oi,
            'gamma_flip_point': self.gamma_flip_point,
            'per_strike_data': json.loads(self.per_strike_data),
            'expiration_filter': self.expiration_filter,
            'data_quality': self.data_quality
        }


class OptionContract(Base):
    """
    Stores individual option contract data.
    """
    __tablename__ = 'option_contracts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    underlying_symbol = Column(String(10), nullable=False, index=True)
    strike = Column(Float, nullable=False)
    expiration = Column(String(10), nullable=False)
    option_type = Column(String(4), nullable=False)  # call or put

    # Greeks
    gamma = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    vega = Column(Float, nullable=True)
    theta = Column(Float, nullable=True)

    # Market data
    implied_volatility = Column(Float, nullable=True)
    open_interest = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=True)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    last_price = Column(Float, nullable=True)

    # Calculated exposures
    gex = Column(Float, nullable=False)
    dex = Column(Float, nullable=True)

    timestamp = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index('idx_underlying_timestamp', 'underlying_symbol', 'timestamp'),
        Index('idx_snapshot', 'snapshot_id'),
    )


class RefreshLog(Base):
    """
    Tracks data refresh operations and their status.
    """
    __tablename__ = 'refresh_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbols = Column(Text, nullable=False)  # JSON array
    status = Column(String(20), nullable=False)  # success, partial, failed
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    records_created = Column(Integer, default=0)


class DatabaseManager:
    """
    Manages database connections, sessions, and common operations.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            from .utils import get_project_root
            db_path = str(get_project_root() / 'data' / 'cache.db')

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create engine
        self.db_path = db_path
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool
        )

        # Create tables
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        logger.info(f"Database initialized at {db_path}")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_gex_snapshot(self, symbol_gex, session: Optional[Session] = None) -> GEXSnapshot:
        """
        Save a SymbolGEX object to the database.

        Args:
            symbol_gex: SymbolGEX object from gex_calculator
            session: Optional session (creates new one if not provided)

        Returns:
            Created GEXSnapshot object
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True

        try:
            # Serialize per-strike data
            per_strike_json = json.dumps({
                str(strike): {
                    'strike': strike,
                    'call_gex': exposure.call_gex,
                    'put_gex': exposure.put_gex,
                    'net_gex': exposure.net_gex,
                    'call_dex': exposure.call_dex,
                    'put_dex': exposure.put_dex,
                    'net_dex': exposure.net_dex,
                    'call_oi': exposure.call_oi,
                    'put_oi': exposure.put_oi,
                    'total_oi': exposure.total_oi
                }
                for strike, exposure in symbol_gex.per_strike.items()
            })

            # Create snapshot
            snapshot = GEXSnapshot(
                symbol=symbol_gex.symbol,
                timestamp=datetime.fromisoformat(symbol_gex.timestamp),
                underlying_price=symbol_gex.underlying_price,
                total_call_gex=symbol_gex.total_call_gex,
                total_put_gex=symbol_gex.total_put_gex,
                net_gex=symbol_gex.net_gex,
                total_call_dex=symbol_gex.total_call_dex,
                total_put_dex=symbol_gex.total_put_dex,
                net_dex=symbol_gex.net_dex,
                total_call_oi=symbol_gex.total_call_oi,
                total_put_oi=symbol_gex.total_put_oi,
                gamma_flip_point=symbol_gex.gamma_flip_point,
                per_strike_data=per_strike_json
            )

            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            logger.info(f"Saved GEX snapshot for {symbol_gex.symbol} at {symbol_gex.timestamp}")

            return snapshot

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving GEX snapshot: {e}")
            raise
        finally:
            if close_session:
                session.close()

    def get_latest_snapshot(self, symbol: str, session: Optional[Session] = None) -> Optional[GEXSnapshot]:
        """
        Get the most recent GEX snapshot for a symbol.

        Args:
            symbol: Ticker symbol
            session: Optional session

        Returns:
            Latest GEXSnapshot or None
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True

        try:
            snapshot = session.query(GEXSnapshot)\
                .filter(GEXSnapshot.symbol == symbol)\
                .order_by(GEXSnapshot.timestamp.desc())\
                .first()

            return snapshot
        finally:
            if close_session:
                session.close()

    def get_snapshots_in_range(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        session: Optional[Session] = None
    ) -> List[GEXSnapshot]:
        """
        Get GEX snapshots for a symbol within a time range.

        Args:
            symbol: Ticker symbol
            start_time: Start of time range
            end_time: End of time range
            session: Optional session

        Returns:
            List of GEXSnapshot objects
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True

        try:
            snapshots = session.query(GEXSnapshot)\
                .filter(GEXSnapshot.symbol == symbol)\
                .filter(GEXSnapshot.timestamp >= start_time)\
                .filter(GEXSnapshot.timestamp <= end_time)\
                .order_by(GEXSnapshot.timestamp.asc())\
                .all()

            return snapshots
        finally:
            if close_session:
                session.close()

    def cleanup_old_data(self, days_to_keep: int = 7, session: Optional[Session] = None) -> int:
        """
        Remove snapshots older than specified days.

        Args:
            days_to_keep: Number of days of data to retain
            session: Optional session

        Returns:
            Number of records deleted
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True

        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            deleted = session.query(GEXSnapshot)\
                .filter(GEXSnapshot.timestamp < cutoff_date)\
                .delete()

            session.commit()

            logger.info(f"Cleaned up {deleted} old snapshots (keeping {days_to_keep} days)")

            return deleted
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up old data: {e}")
            raise
        finally:
            if close_session:
                session.close()

    def log_refresh(
        self,
        symbols: List[str],
        status: str,
        duration: Optional[float] = None,
        error: Optional[str] = None,
        records: int = 0,
        session: Optional[Session] = None
    ):
        """
        Log a data refresh operation.

        Args:
            symbols: List of symbols refreshed
            status: 'success', 'partial', or 'failed'
            duration: Duration in seconds
            error: Error message if failed
            records: Number of records created
            session: Optional session
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True

        try:
            log_entry = RefreshLog(
                timestamp=datetime.now(),
                symbols=json.dumps(symbols),
                status=status,
                duration_seconds=duration,
                error_message=error,
                records_created=records
            )

            session.add(log_entry)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Error logging refresh: {e}")
        finally:
            if close_session:
                session.close()


# Example usage
if __name__ == '__main__':
    # Initialize database
    db = DatabaseManager()

    # Test session
    session = db.get_session()
    print(f"Database initialized: {db.db_path}")

    # Check tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")

    session.close()
