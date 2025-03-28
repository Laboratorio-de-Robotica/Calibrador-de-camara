"""
Este módulo contiene una única clase: ExtrinsicCalibrator, que hace las veces de calibrador extrínseco.

Si se ejecuta como programa, corre una demo en vivo sobre la cámara.
Requiere un patrón de calibración para detectar.

El módulo obtiene la pose y la homografía del patrón de calibración, 
de modo que sirve para ambos abordajes de cómputo de pose 3D de los objetos en la imagen.

La aplicación primaria es la de una cámara cenital que obtiene la vista superior o en ligera perspectiva
de la mesa del robot.
Esta imagen se procesa con detectores que identifican elementos sobre la imagen y sus coordenadas en píxeles.
La homografía y la pose permiten convertir esas coordenadas en píxeles a coordenadas métricas del mundo, 
las coordenadas del sistema del robot.

Este calibrador extrínseco obtiene la pose y homografía de un patrón.  
Si el patrón no coincide con el sistema de referencia del robot (del mundo),
hace falta una conversión adicional que debe medirse manualmente.  El módulo ``geometricTransforms.py``
contiene funciones para realizar esta conversión.
"""

import numpy as np
import cv2 as cv

class ExtrinsicCalibrator:
  """
  Clase para encontrar la homografía a partir de una imagen con un patrón de calibración ajedrez.

  Por lo general los resultados finales e intermedios se guardan en propiedades.
  Cuando se requiere una imagen, si se omite se toma la última guardada en la propiedad ```self.im```.
  """
  def __init__(self, chessBoard=(9,6), square_size=25, cameraMatrix=None, distCoeffs=None):
    """
    Inicializa el calibrador con parámetros de cámara y del patrón de calibración.

    Args:
      chessBoard: dimensiones del patrón de calibración ajedrez, preferentemente impar x par.
      square_size: longitud del lado del cuadrado del patrón de calibración, en las unidades métricas que el usuario elija.
      cameraMatrix: matriz de cámara de 3x3 obtenida en el proceso de calibración intrínseca, ajeno a este código.  Si no se proporciona no se antidistorsionan las esquinas.
      distCoeffs: coreficientes de distorsión obtenidos en el proceso de calibración intrínseca, ajeno a este código.  Si no se proporcionan se asumen cero (sin distorsión).
      
    """
    self.chessBoard = chessBoard
    self.square_size = square_size
    self.cameraMatrix = cameraMatrix
    if cameraMatrix is not None and distCoeffs is None:
      distCoeffs = np.zeros((5,1), np.float64)
    self.distCoeffs = distCoeffs
    self.chessboardPointCloud3D = np.zeros((self.chessBoard[0]*self.chessBoard[1],3), np.float32)
    self.chessboardPointCloud3D[:,:2] = np.mgrid[0:self.chessBoard[0],0:self.chessBoard[1]].T.reshape(-1,2)

  def findCorners(self, im:np.ndarray)->bool:
    """
    Detecta las esquinas del patrón de calibración ajedrez en la imagen, con precisión subpíxel.

    - Si se proporcionan los coeficientes de distorsión, las esquinas se antidistorsionan.
    - Los resultados se guardan en ```self.chessboardFound, self.corners, self.im y self.imGray```.
    - Si no se proporciona una imagen, retorna inmediatamente sin hacer nada preservando los resultados anteriores.

    Args:
      im (np.ndarray): imagen de la cámara en la que se buscará el patrón de calibración

    Returns:
      chessboardFound flag

    """
    self.imGray = cv.cvtColor(im, cv.COLOR_BGR2GRAY)
    self.chessboardFound, corners = cv.findChessboardCorners(self.imGray, self.chessBoard, None)
    if self.chessboardFound:
      corners = cv.cornerSubPix(self.imGray, corners, (11,11), (-1,-1), (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001))
      if self.distCoeffs is not None:
        corners = cv.undistortPoints(corners, self.cameraMatrix, self.distCoeffs, P=self.cameraMatrix)
    self.corners = corners
    return self.chessboardFound
  
  def drawCorners(self, im:np.ndarray)->np.ndarray:
    """
    Anota las esquinas del patrón ajedrez en la imagen.

    Args:
      im (np.ndarray): Imagen de entrada sobre la que se realizarán las anotaciones.

    Returns:
      la imagen anotada.

    """
    if self.chessboardFound:
      cv.drawChessboardCorners(im, self.chessBoard, self.corners, self.chessboardFound)
    return im
  
  def computeHwc(self)->np.ndarray | None:
    """
    Computa la homografía entre las esquinas del patrón en la imagen 
    y las coordenadas 3D de esas esquinas en el patrón.

    Returns:
      La homografía Hwc que transforma píxeles de la imagen en coordenadas métricas del mundo.
      Si no se logra computar la homografía la matriz estará vacía.

      None si no se encontraron las esquinas del patrón.

    """
    if not self.chessboardFound:
      return None
    
    Hwc, _ = cv.findHomography(self.corners, self.chessboardPointCloud3D)
    return Hwc

  def computePose(self)->tuple[np.ndarray, np.ndarray, np.ndarray] | tuple[None, None, None]:
    """
    De la homografía extrae la pose 3D y la expresa de dos maneras:
    
    - como Tcw, la matriz de 4x4 en coordenadas homogéneas
    - en notación Rodrigues: vectores traslación y rotación

    Returns:
      rvecs
      tvecs
      Tcw

    """
    if self.cameraMatrix is None:
       print('Sin la matriz intrínseca de la cámara no se puede calcular la pose.')
       return None, None, None
    
    if not self.chessboardFound:
      print('No se detectó el patrón y no se puede calcular la pose.')
      return None, None, None
 
    retval, rvecs, tvecs = cv.solvePnP(self.chessboardPointCloud3D, self.corners, self.cameraMatrix, self.distCoeffs)
    if not retval:
      print('solvePnP falló en calcular la pose.')
      return None, None, None

    Rcw, _ = cv.Rodrigues(rvecs)
    Tcw = np.hstack((Rcw, tvecs))
    Tcw = np.vstack((Tcw, [0,0,0,1]))

    return rvecs, tvecs, Tcw
    

if(__name__ == '__main__'):
  import geometricTransforms as gt
  print("""
        Usage:
        SPACE: compute H and pose
        ESC: quit
        """)

  ESC = chr(27)
  cv.namedWindow("Cam", cv.WINDOW_NORMAL)
  cv.namedWindow("Tablero", cv.WINDOW_NORMAL)
  defaultPrintOptions = np.get_printoptions()

  imChessboard = cv.imread("./docs/images/pattern_chessboard 6 x 9.png")#, flags = cv.IMREAD_GRAYSCALE)
  cv.imshow("Tablero", imChessboard)

  cam = cv.VideoCapture(0)
  width = cam.get(cv.CAP_PROP_FRAME_WIDTH)
  height = cam.get(cv.CAP_PROP_FRAME_HEIGHT)
  print("Cam resolution:", width, " x ", height)
  newSize = (640, int(640 * height / width))

  cx = width / 2 - 0.5
  cy = height / 2 - 0.5
  f = 2.4 * cx    # Para una cámara de 57º de apertura visual
  cameraMatrix = np.array(
      [[f, 0.0, cx],
      [0.0, f, cy],
      [0.0, 0.0, 1.0]], np.float32)

  calibrator = ExtrinsicCalibrator(cameraMatrix=cameraMatrix) # use fake cameraMatrix

  while True:
    ret, im = cam.read()
    if ret:
      imLowRes = cv.resize(im, newSize)
      if calibrator.findCorners(imLowRes):
        Hwc = calibrator.computeHwc()

        # Transformación arbitraria para visualización
        Hviz = gt.scaleAndTranslateH(Hwc, scaleFactor=25.0, translation=(5,5))
        imFrontal = cv.warpPerspective(imLowRes, Hviz, (im.shape[1], im.shape[0]))
        cv.imshow('Frontal', imFrontal)
        imLowRes = calibrator.drawCorners()

      cv.imshow('Cam', imLowRes)

    key = cv.waitKey(33)
    if key>=0:
      key = chr(key)
      print(key)
      match key:
        case ' ':
          # Calcula parámetros extrínsecos
          calibrator.findCorners(im)
          if not calibrator.chessboardFound:
            print('No se detectó el patrón')
            continue
          Hwc = calibrator.computeHwc()
          rvecs, tvecs, Tcw = calibrator.computePose()

          # Muestra resultados
          np.set_printoptions(precision=2, suppress=True)
          print("Matriz Hwc", Hwc)
          print("rvecs", rvecs)
          print("tvecs", tvecs)
          print("Tcw", Tcw)
          np.set_printoptions(**defaultPrintOptions)

        case 'v':
          # Produce una vista frontal
          calibrator.findCorners(im)
          if not calibrator.chessboardFound:
            continue
          calibrator.computeHwc()
          Hviz = calibrator.getHviz(scaleFactor=25.0, translation=(5,5))
          imFrontal = cv.warpPerspective(im, Hviz, (im.shape[1], im.shape[0]))
          cv.imshow('Frontal', imFrontal)

        case ESC:
          print("Terminando.")
          break