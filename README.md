# sistema-integral-de-planificacion-y-optimizacion



call mvnw.cmd clean install

# En la carpeta raíz del proyecto
set PYTHONPATH=%PYTHONPATH%;. && python sipo/app.py

# En la carpeta frontend/
cd frontend
ng serve

# Para ejecutar el backend

## Se inicializa la base de datos antes de ejecutar el backend
cd sipo && python init_db.py

## Se ejecuta el backend
python -m sipo.app ó \n
 python -c "import sys; sys.path.append('.'); from sipo.app import create_app; app = create_app('development'); app.run(debug=True, host='0.0.0.0', port=5000)"
