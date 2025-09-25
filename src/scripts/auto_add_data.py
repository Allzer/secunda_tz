from pathlib import Path
import random
import sys

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

from database import session_maker
import datagenerator as dg
from src.models.models import *

def add_data():
    with session_maker() as session:
        activity_name = dg.gen_activites()
        keys = list(activity_name.keys())
        
        for key in keys:
            activities_id = dg.gen_uuid()
            activities = ActivitiesModels(
                id=activities_id,
                parent_id=None,
                name=key,
            )
            session.add(activities)
            session.commit()

            buildings_id = dg.gen_uuid()
            buildings = BuildingsModel(
                id=buildings_id,
                address=dg.gen_adres(),
                latitude_longitude=dg.gen_latitude_longitude()
            )
            session.add(buildings)
            session.commit()

            for i in activity_name[key]:
                child_id = dg.gen_uuid()
                child_activites = ActivitiesModels(
                    id=child_id,
                    parent_id=activities_id,
                    name=i
                )
                session.add(child_activites)
                session.commit()

                organizations_id = dg.gen_uuid()
                organizations = OrganizationsModels(
                    id=organizations_id,
                    buildings_id=buildings_id,
                    name=dg.gen_name(),
                )
                session.add(organizations)
                session.commit()

                organization_phones_id = dg.gen_uuid()
                organization_phones = OrganizationPhonesModels(
                    id=organization_phones_id,
                    organization_id=organizations_id,
                    phone_number=dg.gen_phone_number(),
                )
                session.add(organization_phones)
                session.commit()

                choice = random.choice(['child', 'parent', 'both'])
                to_create = []
                if choice == 'child' or choice == 'both':
                    org_act_id = dg.gen_uuid()
                    to_create.append(OrganizationActivitiesModels(
                        id=org_act_id,
                        organization_id=organizations_id,
                        activity_id=child_id,
                    ))
                if choice == 'parent' or choice == 'both':
                    org_act_id = dg.gen_uuid()
                    to_create.append(OrganizationActivitiesModels(
                        id=org_act_id,
                        organization_id=organizations_id,
                        activity_id=activities_id,
                    ))
                for oa in to_create:
                    session.add(oa)
                session.commit()
        print('данные добавлены')

add_data()