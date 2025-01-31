# Calibración extrínseca

El documento [Calibración extrínseca y homografía](https://docs.google.com/document/d/1nhmtYOhzDWaSmLdVwkBU2KdvJJxvtFabnacuMqiCFtQ/edit?tab=t.0) describe los fundamentos de la calibración extrínseca y la determinación de homografía, así como las bases del programa `extrinsics.py` 

# extrinsics.py

Se puede usar como biblioteca que provee la clase `ExtrinsicCalibrator`, o direcamente para una demo sobre la webcam.

## ExtrinsicCalibrator
Esta clase toma los datos de configuración en la construcción, y presenta métodos para obtener homografía y pose sobre la imagen proporcionada.

Cuando se pasa una imagen en los métodos getPose o getHomography, la imagen se registra y se procesa para detectar las esquinas del patrón.  Cuando no se pasa nada se usa la imagen anterior.

### Constructor
Todos los argumentos son de configuración y opcionales:
- chessBoard=(9,6), formato del patrón
- square_size=25, tamaño real del casillero del tablero
- cameraMatrix=None
- distCoeffs=None

Si se proporcionan los parámetros de cámara, la detección de esquinas del patrón ajedrez antidistorsiona las coordenadas.

Si no se proporcionan, no se puede usar getPose().

### getHomography
