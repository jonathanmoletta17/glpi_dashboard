PYTHON=python3
PIP=pip

.PHONY: install-backend install-frontend start-backend start-frontend

install-backend:
	cd backend && $(PIP) install -r requirements.txt

install-frontend:
	cd frontend && npm install

start-backend:
	cd backend && USE_MOCK_DATA=true $(PYTHON) app.py

start-frontend:
	cd frontend && npm run dev

install: install-backend install-frontend
