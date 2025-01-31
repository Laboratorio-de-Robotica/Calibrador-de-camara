import numpy as np
import cv2 as cv

class ExtrinsicCalibrator:
  def __init__(self, chessBoard=(9,6), square_size=25, cameraMatrix=None, distCoeffs=None):
    self.chessBoard = chessBoard
    self.square_size = square_size
    self.cameraMatrix = cameraMatrix
    self.distCoeffs = distCoeffs
    self.chessboardPointCloud3D = np.zeros((self.chessBoard[0]*self.chessBoard[1],3), np.float32)
    self.chessboardPointCloud3D[:,:2] = np.mgrid[0:self.chessBoard[0],0:self.chessBoard[1]].T.reshape(-1,2)

  def findChessboardCorners(self, im):
    '''
    Finds the chessboard corners in the image, with subpixel precision.
    If the camera matrix and distortion coefficients are provided, the corners are undistorted.
    Results are stored in self.chessboardFound, self.corners, self.im and self.imGray.
    If image is not provided, it returns immediately leaving previous results untouched.
    '''
    if im is None:
      return
    
    self.im = im
    self.imGray = cv.cvtColor(im, cv.COLOR_BGR2GRAY)
    self.chessboardFound, corners = cv.findChessboardCorners(self.imGray, self.chessBoard, None)
    if self.chessboardFound:
      corners = cv.cornerSubPix(im, corners, (11,11), (-1,-1), (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001))
      if self.distCoeffs is not None:
        corners = cv.undistortPoints(corners, self.cameraMatrix, self.distCoeffs)
    self.corners = corners
    self.Hwc = None
    self.tvecs = None
    self.rvecs = None
    self.Tcw = None
  
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
    self.findChessboardCorners(im)
    if not self.chessboardFound:
      return None, None, None
 
    retval, self.rvecs, self.tvecs = cv.solvePnP(self.chessboardPointCloud3D, self.corners, self.cameraMatrix, self.distCoeffs)
    if not retval:
      return None, None, None

    Rcw, _ = cv.Rodrigues(self.rvecs)
    self.Tcw = np.hstack((Rcw, self.tvecs))
    self.Tcw = np.vstack((Tcw, [0,0,0,1]))

    return self.rvecs, self.tvecs, self.Tcw
    

if(__name__ == '__main__'):
  pass