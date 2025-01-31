import numpy as np
import cv2 as cv

class ExtrinsicCalibrator:
  def __init__(self, chessBoard=(9,6), square_size=25, cameraMatrix=None, distCoeffs=None):
    self.chessBoard = chessBoard
    self.square_size = square_size
    self.cameraMatrix = cameraMatrix
    if cameraMatrix is not None and distCoeffs is None:
      distCoeffs = np.zeros((5,1), np.float64)
    self.distCoeffs = distCoeffs
    self.chessboardPointCloud3D = np.zeros((self.chessBoard[0]*self.chessBoard[1],3), np.float32)
    self.chessboardPointCloud3D[:,:2] = np.mgrid[0:self.chessBoard[0],0:self.chessBoard[1]].T.reshape(-1,2)

  def findChessboardCorners(self, im):
    '''
    Finds the chessboard corners in the image, with subpixel precision.
    If the camera matrix and distortion coefficients are provided, the corners are undistorted.
    Results are stored in self.chessboardFound, self.corners, self.im and self.imGray.
    If image is not provided, it returns immediately leaving previous results untouched.
    Returns chessboardFound flag
    '''
    if im is None:
      return
    
    self.im = im
    self.Hwc = None
    self.tvecs = None
    self.rvecs = None
    self.Tcw = None
    
    self.imGray = cv.cvtColor(im, cv.COLOR_BGR2GRAY)
    self.chessboardFound, corners = cv.findChessboardCorners(self.imGray, self.chessBoard, None)
    if self.chessboardFound:
      corners = cv.cornerSubPix(self.imGray, corners, (11,11), (-1,-1), (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001))
      if self.distCoeffs is not None:
        corners = cv.undistortPoints(corners, self.cameraMatrix, self.distCoeffs)
    self.corners = corners
    return self.chessboardFound
  
  def drawChessboardCorners(self, im=None):
    '''
    Draws the chessboard corners in the image.
    If the image is not provided, it uses the last results from image stored in self.im.
    '''
    if im is None:
       im = self.im
    if self.chessboardFound:
      cv.drawChessboardCorners(im, self.chessBoard, self.corners, self.chessboardFound)
    return im
  
  def getHomography(self, im=None):
    '''
    Finds the homography between the chessboard corners and the 3D chessboard points.
    If the image is not provided, it uses the last results from image stored in self.im.
    Returns Hwc, wich can be an empty matrix if the homography is not found.
    Returns None if the corners are not found.
    '''
    self.findChessboardCorners(im)
    if self.chessboardFound:
      self.Hwc, _ = cv.findHomography(self.corners, self.chessboardPointCloud3D)
      return self.Hwc
    
    return None
  
  def getPose(self, im=None):
    if self.cameraMatrix is None:
       return None, None, None
    
    self.findChessboardCorners(im)
    if not self.chessboardFound:
      return None, None, None
 
    retval, self.rvecs, self.tvecs = cv.solvePnP(self.chessboardPointCloud3D, self.corners, self.cameraMatrix, self.distCoeffs)
    if not retval:
      return None, None, None

    Rcw, _ = cv.Rodrigues(self.rvecs)
    self.Tcw = np.hstack((Rcw, self.tvecs))
    self.Tcw = np.vstack((self.Tcw, [0,0,0,1]))

    return self.rvecs, self.tvecs, self.Tcw
    

if(__name__ == '__main__'):
  print("""
        Usage:
        C: calibrate with taken pictures
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

  calibrator = ExtrinsicCalibrator()

  while True:
    ret, im = cam.read()
    if ret:
      imLowRes = cv.resize(im, newSize)
      if calibrator.findChessboardCorners(imLowRes):
        imLowRes = calibrator.drawChessboardCorners()
      cv.imshow('Cam', imLowRes)

    key = cv.waitKey(33)
    if key>=0:
      key = chr(key)
      print(key)
      match key:
        case 'c':
          # Calibra
          calibrator.findChessboardCorners(im)
          calibrator.getHomography()
          calibrator.getPose()

          # Muestra resultados
          np.set_printoptions(precision=2, suppress=True)
          print("Matriz Hwc", calibrator.Hwc)
          print("rvecs", calibrator.rvecs)
          print("tvecs", calibrator.tvecs)
          print("Tcw", calibrator.Tcw)
          np.set_printoptions(**defaultPrintOptions)

        case ESC:
          print("Terminando.")
          break