from sqlalchemy import Column, ForeignKey, String, Uuid

from database import Base

__all__ = [
    'BuildingsModel', 'ActivitiesModels',
    'OrganizationsModels', 'OrganizationPhonesModels', 'OrganizationActivitiesModels',
]

class BuildingsModel(Base):

    __tablename__ = 'buildings'

    id = Column(Uuid, primary_key=True)

    address = Column(String, nullable=False)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)

class ActivitiesModels(Base):

    __tablename__ = 'activities'

    id = Column(Uuid, primary_key=True)

    parent_id = Column(Uuid, nullable=True)

    name = Column(String, nullable=False)

class OrganizationsModels(Base):

    __tablename__ = 'organizations'

    id = Column(Uuid, primary_key=True)

    buildings_id = Column(Uuid, ForeignKey('buildings.id'))

    name = Column(String, nullable=False)

class OrganizationPhonesModels(Base):
    
    __tablename__ = 'organization_phones'

    id = Column(Uuid, primary_key=True)

    organization_id = Column(Uuid, ForeignKey('organizations.id'))

    phone_number = Column(String(length=15), nullable=False, unique=True)

class OrganizationActivitiesModels(Base):
    
    __tablename__ = 'organization_activities'

    id = Column(Uuid, primary_key=True)

    organization_id = Column(Uuid, ForeignKey('organizations.id'))
    activity_id = Column(Uuid, ForeignKey('activities.id'))
    