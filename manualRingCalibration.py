'''
Demo de calibración de ring manual, a través de clic del usuario.

TODO:
- Implementar la grilla
- Elegir colores y grosor de líneas
- ¿Visualización de la homografía?  Requiere escalar la homografía automáticamente.
'''

import numpy as np
import cv2 as cv
import argparse
import geometricTransforms as gt

parser = argparse.ArgumentParser(description='Calibración de un ring rectangular.')
parser.add_argument('x', type=int, help='ancho real del ring [mm]', default=1000)
parser.add_argument('y', type=int, help='ancho real del ring [mm]', default=1000)
args = parser.parse_args()
realRingCorners = np.array([[0,0],[args.x,0],[args.x,args.y],[0,args.y]])
#realRingCorners = np.array([[0,0],[args.ringSize[0],0],[args.ringSize[0],args.ringSize[1]],[0,args.ringSize[1]]])

mousePos = (0,0)
step = 0
imRingCorners = []
H = np.eye(3)

def annotate(im:np.ndarray)->np.ndarray:
  for i in range(step):
    # Dibuja los vértices
    cv.circle(im,imRingCorners[i],5,(0,0,255),-1)
    if i>0:
      # Une los vértices con segmentos de rectas
      cv.line(im,imRingCorners[i-1],imRingCorners[i],(0,0,255),2)

  if step==4:
    # Cierra el trapecio
    cv.line(im,imRingCorners[i],imRingCorners[0],(0,0,255),2)

    # Muestra las coordenadas convertidas
    realPoint = gt.projectPoint(H, mousePos)
    cv.putText(im, f'Coords: {realPoint}', (0,im.shape[0]), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1, cv.LINE_AA)

    # Dibuja una grilla
    # ...
  elif step>0:
    # Dibuja el último segmento de recta
    cv.line(im,imRingCorners[i],mousePos,(0,0,255),2)
  
  return im

def mouse(event:int,x:int,y:int,flags,param):
  global mousePos, step
  if event == cv.EVENT_LBUTTONUP:
    '''
    LBUTTONDOWN se dispara varias veces consecutivas.
    LBUTTONUP solo una vez, es mejor para detectar clic.
    mousePos se actualiza después, es una manera de tomar la última posición mientras el botón está presionado.
    '''
    global H

    if step<4:
      step+=1
      imRingCorners.append(mousePos)

      if step==4:
        # Calcular la homografía
        H, _ = cv.findHomography(np.array(imRingCorners),realRingCorners)
        print('Homografía:')
        print(H)

  mousePos = (x,y)

cv.namedWindow('Webcam')
cv.setMouseCallback('Webcam',mouse)
webcam = cv.VideoCapture(0)

while True:
  ret, im = webcam.read()
  if not ret:
    break
  
  annotate(im)
  cv.imshow('Webcam', im)
  key = cv.waitKey(30) & 0xFF
  if key == 27:#ESC
    break
  elif key == 8:#BS
    if step:
      step-=1
      imRingCorners.pop()