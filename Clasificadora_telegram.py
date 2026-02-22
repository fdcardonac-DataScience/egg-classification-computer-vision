#se llaman las librerias 
import cv2
import numpy as np
import os
import telegram
import asyncio
import time
import threading # <-- Importamos threading

#Funcion que permite la comunicacion con telegram
CHAT_ID = '6989622883'
TOKEN = '8343792328:AAH3Gcndb5SGnlrhc0GqnypIiuJsBA-qLAI' 
bot = telegram.Bot(token=TOKEN)

async def send_message_async(chat_id, text):
    """Función asíncrona para enviar mensajes sin bloquear el bucle principal."""
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

# --- Inicialización del bucle de eventos de Asyncio en segundo plano ---
# Esta función corre en un hilo separado
def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

new_loop = asyncio.new_event_loop()
# Creamos y arrancamos el hilo que manejará las comunicaciones de red
t = threading.Thread(target=start_asyncio_loop, args=(new_loop,), daemon=True)
t.start()

# Ejecutar el mensaje de bienvenida y encendido (usando el nuevo loop de forma segura)
def startup_messages():
    # Usamos call_soon_threadsafe para agendar la tarea en el otro hilo
    new_loop.call_soon_threadsafe(asyncio.create_task, send_message_async(CHAT_ID, "Clasificadora De Huevo Del Tolima - Iniciando"))
    time.sleep(1) 
    new_loop.call_soon_threadsafe(asyncio.create_task, send_message_async(CHAT_ID, "Clasificadora Encendida"))
# --- Fin Inicialización Asyncio ---
	
# --- Inicialización de variables y cámara ---
contA, contAA, contAAA, contjum = 0, 0, 0, 0
texto = 'Tipo: '
contador = 0
cap=cv2.VideoCapture(1,cv2.CAP_DSHOW)
kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))

if not cap.isOpened():
    print("No se pudo abrir la cámara.")
    exit()
	
startup_messages()

# Define el área de interés (ROI) una sola vez
area_pts = np.array([[570, 10], [130, 10], [130, 475], [570, 475]], dtype=np.int32)
# Crea la máscara auxiliar una sola vez, no en cada frame
imgaux_mask = np.zeros(shape=(480, 640), dtype=np.uint8)
cv2.drawContours(imgaux_mask, [area_pts], -1, 255, -1)	

print("Iniciando bucle principal...")

while True:

	ret,frame=cap.read()
	
	if ret==False:break
		
	#se crea una imagen auxiliar del mismo tamaño de frame	
	imgarea=cv2.bitwise_and(frame,frame, mask=imgaux_mask)
	
	#la imagen se convierte al espacio de color YCrCb y se separa sus componentes
	img=cv2.cvtColor(imgarea,cv2.COLOR_BGR2YCrCb)
	YCrCb=cv2.medianBlur(img,23)
	
	Cr=YCrCb[:,:,2] # Canal de Crominancia Roja	
	
	#se aplica umbralizacion, dilatación, filtrado 
	_,binarizada1=cv2.threshold(Cr,123,255,cv2.THRESH_BINARY_INV)
	binarizada2=cv2.dilate(binarizada1,None,iterations=3)
	binarizada3=cv2.morphologyEx(binarizada2,cv2.MORPH_OPEN,kernel)
	binarizada4=cv2.medianBlur(binarizada3,35)
	
	#se hallan los contornos de la imagen
	cnts=cv2.findContours(binarizada4,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]	
	
	#se hace un barrido por cada contorno encontrado
	for c in cnts:
		color = (0, 0, 0) # Naranja
		   		
		#analisis del area del contorno
		if cv2.contourArea(c)>4000:						
			#se obtine medidas del contorno y se calcula matematicamente un aproximado del peso
			x,y,w,h=cv2.boundingRect(c)
						
			if 118<y<128:					      
				ancho=((w/5.22)/2) #5.3354
				alto=((h/5.1277)/2) #5.1277
				area=((ancho)*(alto)*np.pi)				
				peso=(area-1041)/14.76
				peso=int(peso)
				contador=contador+1
				print(f"Huevo detectado: {contador}, Peso: {peso}g")
				
				# Variable para el mensaje de Telegram
				mensaje_telegram = ""
			
				#con condicionales se analiza el rangos del peso								
				if 60.9>peso>51.8:
					texto='Tipo: A'
					contA=contA+1
					color = (255, 165, 0) # Naranja		
					mensaje_telegram = f"🥚 Huevo A | Peso: {peso}g | Total A: {contA}"			
				if 67.9>peso>60.9:
					texto='Tipo: AA'
					contAA=contAA+1
					color = (255, 0, 0) # Azul
					mensaje_telegram = f"🥚 Huevo AA | Peso: {peso}g | Total AA: {contAA}"
				if 79>peso>67.9:					
					texto='Tipo: AAA'
					contAAA=contAAA+1
					color = (0, 0, 255) # Rojo
					mensaje_telegram = f"🥚 Huevo AAA | Peso: {peso}g | Total AAA: {contAAA}"
				
				cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                # Disparar el mensaje a Telegram de forma asíncrona
				if mensaje_telegram:
					new_loop.call_soon_threadsafe(asyncio.create_task, send_message_async(CHAT_ID, mensaje_telegram))

	#se muestra en pantalla la imagen
	cv2.putText(frame,texto,(20,40),2,1.5,(0,0,255),1,cv2.LINE_AA)										
	cv2.imshow('Clasificador',frame)
	cv2.imshow('binarizada',binarizada4)

	k=cv2.waitKey(1)
	
	if k==27:
		break

#se apaga camara y se cierran ventanas
cap.release()
cv2.destroyAllWindows()
os.system('cls' if os.name == 'nt' else 'clear')

print('cant. huevos: '+str(contador))
print('A= '+str(contA))
print('AA= '+str(contAA))
print('AAA= '+str(contAAA))

# Función para enviar resumen final (también usando el hilo secundario)
def shutdown_messages():
    final_summary = f"Resumen:\nTotal: {contador}\nTipo A: {contA}\nTipo AA: {contAA}\nTipo AAA: {contAAA}"
    new_loop.call_soon_threadsafe(asyncio.create_task, send_message_async(CHAT_ID, final_summary))
    new_loop.call_soon_threadsafe(asyncio.create_task, send_message_async(CHAT_ID, "Clasificadora Apagada"))
    # Da tiempo al hilo para enviar los mensajes antes de que el programa termine completamente
    time.sleep(2) 

shutdown_messages()
