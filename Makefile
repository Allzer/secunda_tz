all: install_lib create_db create_data

install_lib:
	pip install -r requirements.txt
	pip install --upgrade pip

create_db:
	python create_db.py
	alembic upgrade head

create_data:
	python src/scripts/auto_add_data.py