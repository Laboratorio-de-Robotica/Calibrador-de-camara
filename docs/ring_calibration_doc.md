# Calibración manual de un ring

El programa manualRingCalibration.py calibra un ring de manera interactiva, y computa la homografía que transforma coordenadas de píxeles sobre la imagen en coordenadas métricas del ring.

Se ejecuta con dos parámetros: ancho y alto del ring en mm

    python manualRingCalibration.py 1000 500

El usuario debe hacer clic sobre cada esquina del ring rectangular, comenzando por el origen de coordenadas, siguiendo por el eje x y continuando en sentido circular.  Con el 4º clic queda establecido el ring y se computa la homografía y se presenta en consola.  Calibrado el ring de este modo, a modo de prueba sobre la imagen se mostrarán las coordenadas métricas del puntero del mouse.

Con la tecla de borrar se borra el último vértice y se vuelve un paso atrás.  ESC para salir.