from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CertificateType(str, Enum):
    ROOT = 'ROOT'
    INTERMEDIATE = 'INTERMEDIATE'
    USER = 'USER'

class AlgorithmType(str, Enum):
    GOST = 'GOST'
    RSA = 'RSA'
    

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default='user')

    certificates = relationship('Certificate', back_populates='owner')
    chains = relationship('CertificateChain', back_populates='owner')

class Certificate(Base):
    __tablename__ = 'certificates'

    id = Column(Integer, primary_key=True, index=True)
    common_name = Column(String, index=True)
    serial_number = Column(String, unique=True, index=True)
    issuer = Column(String)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    revoked = Column(Boolean, default=False)
    revocation_date = Column(DateTime, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    certificate_type = Column(SQLAlchemyEnum(CertificateType), default=CertificateType.USER)
    algorithm = Column(SQLAlchemyEnum(AlgorithmType), default=AlgorithmType.RSA)

    owner = relationship('User', back_populates='certificates')
    chain_links = relationship('CertificateChainLink', back_populates='certificate')
    

class CertificateChain(Base):
    __tablename__ = 'certificate_chains'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('User', back_populates='chains')
    chain_links = relationship('CertificateChainLink', back_populates='chain')

class CertificateChainLink(Base):
    __tablename__ = "certificate_chain_links"

    id = Column(Integer, primary_key=True, index=True)
    chain_id = Column(Integer, ForeignKey('certificate_chains.id'))
    certificate_id = Column(Integer, ForeignKey('certificates.id'))
    order = Column(Integer)

    chain = relationship('CertificateChain', back_populates='chain_links')
    certificate = relationship('Certificate', back_populates='chain_links')

    
class CRL(Base):
    __tablename__ = 'crls'

    id = Column(Integer, primary_key=True, index=True)
    issuer = Column(String)  # Издатель CRL (обычно корневой или промежуточный сертификат)
    this_update = Column(DateTime)  # Дата выпуска CRL
    next_update = Column(DateTime)  # Дата следующего обновления CRL
    crl_number = Column(Integer)  # Номер CRL (увеличивается с каждым обновлением)
    revoked_certificates = relationship('RevokedCertificate', back_populates='crl')
    
class DeltaCRL(Base):
    __tablename__ = 'delta_crls'

    id = Column(Integer, primary_key=True, index=True)
    issuer = Column(String)  # Издатель Delta CRL
    this_update = Column(DateTime)  # Дата выпуска Delta CRL
    next_update = Column(DateTime)  # Дата следующего обновления Delta CRL
    crl_number = Column(Integer)  # Номер Delta CRL
    base_crl_id = Column(Integer, ForeignKey('crls.id'))  # Ссылка на базовый CRL
    revoked_certificates = relationship('RevokedCertificate', back_populates='delta_crl')

# Обновим модель RevokedCertificate для поддержки Delta CRL
class RevokedCertificate(Base):
    __tablename__ = 'revoked_certificates'

    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey('certificates.id'))
    revocation_date = Column(DateTime)  # Дата отзыва сертификата
    crl_id = Column(Integer, ForeignKey('crls.id'), nullable=True)  # Может быть частью CRL
    delta_crl_id = Column(Integer, ForeignKey('delta_crls.id'), nullable=True)  # Или частью Delta CRL

    certificate = relationship('Certificate')
    crl = relationship('CRL', back_populates='revoked_certificates')
    delta_crl = relationship('DeltaCRL', back_populates='revoked_certificates')